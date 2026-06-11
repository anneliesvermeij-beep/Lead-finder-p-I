"""
Zet bedrijven met een fotograaf-vacature in de CRM, als APARTE categorie
(bron = 'vacature'). Ze verschijnen in het eigen tabblad 'Vacatures' en blijven
buiten je gewone werklijst.

Leest data/seed_vacatures.csv (kolommen: name, website), analyseert elke site
voor een score, en zet ze in crm_leads met bron='vacature'.

Vereist: kolom 'bron' in crm_leads (zie SQL) + geheime service-sleutel.
Gebruik: python import_vacatures.py
"""
import csv
import os
import uuid
from datetime import datetime, timezone
from urllib.parse import urlparse

from dotenv import load_dotenv

from src.website_analyzer import analyze_website
from src.scoring import score_lead

load_dotenv()

SEED = "data/seed_vacatures.csv"


def _domain(u: str) -> str:
    u = u or ""
    return urlparse(u if u.startswith("http") else "https://" + u).netloc.replace("www.", "").lower()


def _branche(niche: str) -> str:
    niche = (niche or "").lower()
    if "horeca" in niche:
        return "horeca"
    if "food" in niche:
        return "foodproducent"
    if "retail" in niche or "webshop" in niche or "product" in niche:
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
    toegevoegd = 0
    for r in rijen:
        site = r["website"]
        if _domain(site) in al_in_crm:
            print(f"  (overslaan, al in CRM) {r['name']}")
            continue

        signals = analyze_website(site)
        score, reasons, _ = score_lead(signals)
        spec = ", ".join(dict.fromkeys(
            signals.get("priority_hits", []) + signals.get("visual_hits", []) + signals["niche_hits"]
        ))
        notitie = f"📌 Heeft vacature voor fotograaf (gevonden via Indeed)"
        if spec:
            notitie += f" · specialiteit: {spec}"

        db.table("crm_leads").insert({
            "id": "vac_" + uuid.uuid4().hex[:16],
            "bedrijfsnaam": r["name"],
            "branche": _branche(spec),
            "website": site,
            "email": signals["emails"][0] if signals["emails"] else None,
            "status": "nieuw",
            "prioriteit": False,
            "volgende_actie_op": None,
            "score": score,
            "bron": "vacature",
            "contact_momenten": [
                {"id": uuid.uuid4().hex[:12], "datum": nu, "kanaal": "overig", "notitie": notitie}
            ],
            "aangemaakt_op": nu,
        }).execute()
        toegevoegd += 1
        print(f"  + {r['name']}  (score {score})")

    print(f"\n{toegevoegd} vacature-bedrijven toegevoegd (bron=vacature).")


if __name__ == "__main__":
    main()
