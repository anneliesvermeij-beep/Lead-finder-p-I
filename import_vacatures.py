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
from urllib.parse import quote

from dotenv import load_dotenv

load_dotenv()

SEED = "data/seed_vacatures.csv"


def main():
    url, key = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY")
    if not url or not key:
        print("Geen SUPABASE_URL/KEY in .env.")
        return
    from supabase import create_client
    db = create_client(url, key)

    with open(SEED, newline="", encoding="utf-8") as f:
        rijen = [r for r in csv.DictReader(f) if r.get("name")]

    # Welke vacature-bedrijven staan al in de CRM? (op naam, om dubbel te voorkomen)
    bestaande_namen = {
        (r.get("bedrijfsnaam") or "").lower()
        for r in db.table("crm_leads").select("bedrijfsnaam").eq("bron", "vacature").execute().data or []
    }

    nu = datetime.now(timezone.utc).isoformat()
    toegevoegd = 0
    for r in rijen:
        naam = r["name"]
        if naam.lower() in bestaande_namen:
            print(f"  (overslaan, al in CRM) {naam}")
            continue
        # De vacature staat op Indeed, niet op de bedrijfssite. We bewaren een
        # verifieerbare Indeed-zoeklink i.p.v. een (onzekere) bedrijfswebsite.
        link = "https://nl.indeed.com/jobs?q=" + quote(naam + " fotograaf")
        notitie = f"📌 Vacature voor fotograaf — bekijk op Indeed: {link}"
        db.table("crm_leads").insert({
            "id": "vac_" + uuid.uuid4().hex[:16],
            "bedrijfsnaam": naam,
            "branche": "overig",
            "website": link,
            "status": "nieuw",
            "prioriteit": False,
            "volgende_actie_op": None,
            "score": 0,
            "bron": "vacature",
            "contact_momenten": [
                {"id": uuid.uuid4().hex[:12], "datum": nu, "kanaal": "overig", "notitie": notitie}
            ],
            "aangemaakt_op": nu,
        }).execute()
        toegevoegd += 1
        print(f"  + {naam}")

    print(f"\n{toegevoegd} vacature-bedrijven toegevoegd (bron=vacature).")


if __name__ == "__main__":
    main()
