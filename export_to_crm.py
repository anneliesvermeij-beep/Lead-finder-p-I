"""
Veilige import: kopieert bureaus uit de finder-tabel (leads) naar de CRM-tabel
(crm_leads) in Supabase. Draait server-side met de GEHEIME service-sleutel, dus
de bureau-lijst blijft afgeschermd voor de buitenwereld.

- Standaard: de 20 hoogst scorende bureaus die nog niet benaderd zijn.
- Slaat bureaus over die al in je CRM staan (overschrijft je eigen werk nooit).

Gebruik:
    python export_to_crm.py                 # top 20 (hoogste score)
    python export_to_crm.py --aantal 10     # ander aantal
    python export_to_crm.py --niche food    # alleen een specialiteit
    python export_to_crm.py --min-score 70  # alleen vanaf een score
"""
import argparse
import json
import os
import uuid
from datetime import datetime, timezone
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv()

# Finder-status -> CRM-status
MAP_STATUS = {
    "niet benaderd": "nieuw",
    "benaderd": "benaderd",
    "geen interesse": "afgewezen",
    "klant": "klant",
}


def _id() -> str:
    return "crm_" + uuid.uuid4().hex[:16]


def _domain(url: str) -> str:
    url = url or ""
    return urlparse(url if url.startswith("http") else "https://" + url).netloc.replace("www.", "").lower()


def _branche(type_: str, niche: str) -> str:
    niche = (niche or "").lower()
    if (type_ or "") == "direct merk":
        return "horeca" if "horeca" in niche else "foodproducent"
    return "bureau"


def main():
    p = argparse.ArgumentParser(description="Importeer finder-bureaus naar de CRM.")
    p.add_argument("--aantal", type=int, default=20, help="Hoeveel bureaus (default 20)")
    p.add_argument("--min-score", type=int, default=0, help="Alleen vanaf deze score")
    p.add_argument("--niche", default="", help="Alleen met dit woord in de specialiteit")
    p.add_argument("--alles", action="store_true",
                   help="Importeer ALLE leads als voorraad (geen opvolgdatum, niet in 'Vandaag')")
    args = p.parse_args()
    aantal = 10**9 if args.alles else args.aantal

    url, key = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY")
    if not url or not key:
        print("Geen SUPABASE_URL/KEY in .env.")
        return
    if not key.startswith("sb_secret_") and "service_role" not in key:
        print("Let op: dit script vereist de GEHEIME service-sleutel in .env "
              "(de bureau-tabel is afgeschermd voor de publieke sleutel).")

    from supabase import create_client
    db = create_client(url, key)

    # 1) Welke bureaus staan al in de CRM? (op domein, om dubbel te voorkomen)
    bestaande = db.table("crm_leads").select("website").execute().data or []
    al_in_crm = {_domain(r["website"]) for r in bestaande if r.get("website")}

    # 2) Kandidaten uit de finder: niet 'klant'/'geen interesse', hoogste score eerst
    q = (
        db.table("leads")
        .select("name,website,city,email,phone,score,status,type,niche_hits,reasons")
        .gte("score", args.min_score)
        .order("score", desc=True)
    )
    rijen = q.execute().data or []

    gekozen = []
    for r in rijen:
        if r.get("status") in ("klant", "geen interesse"):
            continue
        if _domain(r.get("website", "")) in al_in_crm:
            continue
        if args.niche and args.niche.lower() not in (r.get("niche_hits") or "").lower():
            continue
        gekozen.append(r)
        if len(gekozen) >= aantal:
            break

    if not gekozen:
        print("Geen nieuwe bureaus om te importeren (alles al in de CRM of gefilterd weg).")
        return

    # 3) Omzetten naar CRM-leads en wegschrijven
    nu = datetime.now(timezone.utc).isoformat()
    vandaag = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    records = []
    for r in gekozen:
        score = int(r.get("score") or 0)
        context = f"Geïmporteerd uit lead-finder · score {score}"
        if r.get("niche_hits"):
            context += f" · {r['niche_hits']}"
        records.append({
            "id": _id(),
            "bedrijfsnaam": r.get("name") or r.get("website") or "Onbekend",
            "branche": _branche(r.get("type"), r.get("niche_hits")),
            "plaats": r.get("city") or None,
            "email": r.get("email") or None,
            "telefoon": r.get("phone") or None,
            "website": r.get("website") or None,
            "status": MAP_STATUS.get(r.get("status", ""), "nieuw"),
            # Voorraad-import (--alles): geen opvolgdatum, geen ster -> niet in 'Vandaag'.
            "prioriteit": (score >= 90) and not args.alles,
            "volgende_actie_op": None if args.alles else vandaag,
            "contact_momenten": [
                {"id": _id(), "datum": nu, "kanaal": "overig", "notitie": context}
            ],
            "aangemaakt_op": nu,
        })

    db.table("crm_leads").insert(records).execute()
    print(f"{len(records)} bureaus geïmporteerd naar de CRM:")
    for r in records:
        ster = " [prioriteit]" if r["prioriteit"] else ""
        print(f"  - {r['bedrijfsnaam']}{ster}  ({r['email'] or 'geen mail'})")


if __name__ == "__main__":
    main()
