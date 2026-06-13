"""
Importeert FD Gazellen in de CRM als aparte categorie (bron='gazelle').
Leest data/seed_gazellen.csv (kolom: name). Per naam gokt het een website
(naam.nl / naam.com) en verifieert die; lukt dat niet, dan komt het bedrijf
als naam-alleen binnen (zonder website). Dedup op naam.

Gebruik: python import_gazellen.py
"""
import csv
import os
import re
import sys
import uuid
from datetime import datetime, timezone

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import requests
from dotenv import load_dotenv

load_dotenv()

SEED = "data/seed_gazellen.csv"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}


def vind_website(naam: str):
    # Naam is soms al een domein (Qoets.nl, computerzaak.nl).
    m = re.search(r"[a-z0-9\-]+\.[a-z]{2,}", naam.lower())
    kandidaten = []
    if m:
        kandidaten.append(m.group(0))
    slug = re.sub(r"[^a-z0-9]", "", naam.lower())
    if slug:
        kandidaten += [slug + ".nl", slug + ".com"]
    for dom in kandidaten:
        for sch in ("https://www.", "https://"):
            try:
                r = requests.get(sch + dom, headers=UA, timeout=8, allow_redirects=True)
                if r.status_code == 200:
                    return "https://" + dom
            except Exception:
                pass
    return None


def main():
    url, key = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY")
    if not url or not key:
        print("Geen SUPABASE_URL/KEY in .env.")
        return
    from supabase import create_client
    db = create_client(url, key)

    bestaand = {
        (r.get("bedrijfsnaam") or "").lower()
        for r in db.table("crm_leads").select("bedrijfsnaam").eq("bron", "gazelle").execute().data or []
    }

    with open(SEED, newline="", encoding="utf-8") as f:
        namen = [r["name"].strip() for r in csv.DictReader(f) if r.get("name", "").strip()]

    nu = datetime.now(timezone.utc).isoformat()
    toegevoegd, metsite = 0, 0
    for naam in namen:
        if naam.lower() in bestaand:
            continue
        site = vind_website(naam)
        if site:
            metsite += 1
        db.table("crm_leads").insert({
            "id": "gaz_" + uuid.uuid4().hex[:14],
            "bedrijfsnaam": naam,
            "branche": "overig",
            "website": site,
            "status": "nieuw",
            "prioriteit": False,
            "volgende_actie_op": None,
            "score": 0,
            "bron": "gazelle",
            "contact_momenten": [
                {"id": uuid.uuid4().hex[:12], "datum": nu, "kanaal": "overig",
                 "notitie": "FD Gazelle 2025 — snelgroeiend bedrijf"}
            ],
            "aangemaakt_op": nu,
        }).execute()
        toegevoegd += 1
        print(f"  + {naam}  ({site or 'geen website'})")

    print(f"\n{toegevoegd} Gazellen toegevoegd ({metsite} met website).")


if __name__ == "__main__":
    main()
