"""
Importeert snelgroeiende/succesvolle bedrijven (bv. FD Gazellen) MET zwakke
fotografie als aparte categorie in de CRM (bron='groeibedrijf').

Voor elk bedrijf draaien we de beeldkwaliteit-analyse. Alleen bedrijven met
minstens één fotoprobleem (stockfoto / geen foto's / slechte belichting /
lage kwaliteit) komen erin — want díe hebben baat bij een betere fotograaf.

Leest data/seed_groeibedrijven.csv (kolommen: name, website[, city]).
Vereist de 'bron'-kolom in crm_leads + de geheime service-sleutel.

Gebruik: python import_groeibedrijven.py
"""
import csv
import os
import sys
import uuid
from datetime import datetime, timezone
from urllib.parse import urlparse

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from dotenv import load_dotenv

from src.website_analyzer import analyze_website
from src.scoring import score_lead, FOTO_REDEN

load_dotenv()

SEED = "data/seed_groeibedrijven.csv"


def _domain(u: str) -> str:
    u = u or ""
    return urlparse(u if u.startswith("http") else "https://" + u).netloc.replace("www.", "").lower()


def _branche(spec: str) -> str:
    spec = (spec or "").lower()
    if "horeca" in spec:
        return "horeca"
    if "food" in spec:
        return "foodproducent"
    if "retail" in spec or "webshop" in spec or "product" in spec:
        return "webshop"
    return "overig"


def main():
    url, key = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY")
    if not url or not key:
        print("Geen SUPABASE_URL/KEY in .env.")
        return
    from supabase import create_client
    db = create_client(url, key)

    bestaande = db.table("crm_leads").select("website").execute().data or []
    al_in_crm = {_domain(r["website"]) for r in bestaande if r.get("website")}

    with open(SEED, newline="", encoding="utf-8") as f:
        rijen = [r for r in csv.DictReader(f) if r.get("website")]

    nu = datetime.now(timezone.utc).isoformat()
    toegevoegd, overgeslagen = 0, 0
    for r in rijen:
        site = r["website"]
        if _domain(site) in al_in_crm:
            continue

        signals = analyze_website(site)
        criteria = signals.get("foto_criteria", [])
        if not signals.get("reachable") or not criteria:
            overgeslagen += 1
            print(f"  - {r['name']}: geen fotoprobleem (overslaan)")
            continue

        score, _, _ = score_lead(signals)
        spec = ", ".join(dict.fromkeys(
            signals.get("priority_hits", []) + signals.get("visual_hits", []) + signals["niche_hits"]
        ))
        problemen = ", ".join(FOTO_REDEN.get(c, c) for c in criteria)
        notitie = f"📷 Zwakke fotografie: {problemen}. Snelgroeiend/succesvol bedrijf."

        db.table("crm_leads").insert({
            "id": "groei_" + uuid.uuid4().hex[:14],
            "bedrijfsnaam": r["name"],
            "branche": _branche(spec),
            "plaats": r.get("city") or None,
            "website": site,
            "email": signals["emails"][0] if signals["emails"] else None,
            "status": "nieuw",
            "prioriteit": False,
            "volgende_actie_op": None,
            "score": score,
            "bron": "groeibedrijf",
            "contact_momenten": [
                {"id": uuid.uuid4().hex[:12], "datum": nu, "kanaal": "overig", "notitie": notitie}
            ],
            "aangemaakt_op": nu,
        }).execute()
        toegevoegd += 1
        print(f"  + {r['name']}  (score {score}) — {problemen}")

    print(f"\n{toegevoegd} groeibedrijven met zwakke fotografie toegevoegd, "
          f"{overgeslagen} overgeslagen (goede fotografie).")


if __name__ == "__main__":
    main()
