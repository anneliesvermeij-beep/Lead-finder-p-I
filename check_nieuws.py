"""
Nieuws-trigger voor je CRM-leads.

Voor elk bureau in crm_leads zoekt dit script recent nieuws (Google News, incl.
Adformatie/Marketing Report). Is er nieuw nieuws, dan:
  - komt de kop als contactmoment in de tijdlijn ("📰 Nieuws: ..."),
  - springt de lead naar 'Vandaag' (volgende_actie_op = vandaag),
  - krijgt de lead een ster (prioriteit).

Geen database-wijziging nodig: het gebruikt de bestaande velden. Al eerder
gemeld nieuws wordt niet dubbel toegevoegd.

Gebruik:
    python check_nieuws.py                # laatste 21 dagen
    python check_nieuws.py --dagen 7      # andere periode
"""
import argparse
import os
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote

import requests
from dotenv import load_dotenv

load_dotenv()

UA = {"User-Agent": "Mozilla/5.0 (compatible; LeadNewsCheck/1.0)"}
# Woorden die het over marketing/bureaus laten gaan (minder ruis bij algemene namen).
QUALIFIER = "(reclame OR campagne OR bureau OR marketing OR adformatie)"


def _id() -> str:
    return f"nws_{int(time.time()*1000):x}"


def zoek_nieuws(naam: str, sinds: datetime):
    """Geeft de nieuwste relevante nieuws-item terug, of None."""
    q = quote(f'"{naam}" {QUALIFIER}')
    url = f"https://news.google.com/rss/search?q={q}&hl=nl&gl=NL&ceid=NL:nl"
    try:
        r = requests.get(url, headers=UA, timeout=15)
        if r.status_code != 200:
            return None
        root = ET.fromstring(r.content)
    except Exception:
        return None

    beste = None
    for item in root.iter("item"):
        titel = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub = item.findtext("pubDate")
        if not titel or not pub:
            continue
        try:
            datum = parsedate_to_datetime(pub)
            if datum.tzinfo is None:
                datum = datum.replace(tzinfo=timezone.utc)
        except Exception:
            continue
        if datum < sinds:
            continue
        if beste is None or datum > beste["datum"]:
            beste = {"titel": titel, "link": link, "datum": datum}
    return beste


def main():
    p = argparse.ArgumentParser(description="Nieuws-trigger voor CRM-leads.")
    p.add_argument("--dagen", type=int, default=21, help="Hoever terug kijken (default 21)")
    args = p.parse_args()

    url, key = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY")
    if not url or not key:
        print("Geen SUPABASE_URL/KEY in .env.")
        return
    from supabase import create_client
    db = create_client(url, key)

    sinds = datetime.now(timezone.utc) - timedelta(days=args.dagen)
    vandaag = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    nu = datetime.now(timezone.utc).isoformat()

    # Alleen leads die je actief opvolgt (met opvolgdatum) — niet de hele voorraad.
    leads = (
        db.table("crm_leads")
        .select("id,bedrijfsnaam,contact_momenten,prioriteit")
        .not_.is_("volgende_actie_op", "null")
        .execute()
        .data
        or []
    )

    print(f"{len(leads)} actieve CRM-leads checken op nieuws (laatste {args.dagen} dagen)…\n")
    getriggerd = 0
    for lead in leads:
        naam = lead["bedrijfsnaam"]
        nieuws = zoek_nieuws(naam, sinds)
        time.sleep(1)  # netjes tegenover Google
        if not nieuws:
            continue

        momenten = lead.get("contact_momenten") or []
        # Al gemeld? (zelfde link al in de tijdlijn)
        if any(nieuws["link"] in (m.get("notitie") or "") for m in momenten):
            continue

        datum_kort = nieuws["datum"].strftime("%d-%m-%Y")
        notitie = f"📰 Nieuws ({datum_kort}): {nieuws['titel']} — {nieuws['link']}"
        nieuwe_momenten = [
            {"id": _id(), "datum": nu, "kanaal": "overig", "notitie": notitie}
        ] + momenten

        db.table("crm_leads").update({
            "contact_momenten": nieuwe_momenten,
            "volgende_actie_op": vandaag,
            "prioriteit": True,
        }).eq("id", lead["id"]).execute()

        getriggerd += 1
        print(f"  [nieuws] {naam}: {nieuws['titel'][:70]}")

    print(f"\nKlaar. {getriggerd} lead(s) met nieuw nieuws getriggerd.")


if __name__ == "__main__":
    main()
