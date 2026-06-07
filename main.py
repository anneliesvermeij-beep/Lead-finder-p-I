"""
Bureau Lead Finder - hoofdscript.

Twee manieren om bureaus te verzamelen:

1) Ontdekken via Google Places (heel Nederland):
       python main.py --discover

2) Een eigen lijst sites analyseren (geen API-sleutel nodig):
       python main.py --seed data/seed_example.csv

In beide gevallen analyseert de tool elke website op fotografie-signalen,
geeft een score (0-100) en schrijft een gesorteerde CSV naar data/leads.csv.
"""
import argparse
import csv
import os

from dotenv import load_dotenv

import config
from src.discovery import discover_agencies
from src.website_analyzer import analyze_website
from src.scoring import score_lead
from src.storage import load_existing_domains, save_leads, _domain

load_dotenv()


def load_seed(path: str) -> list:
    """Leest een CSV met minstens een kolom 'website' (optioneel 'name', 'city')."""
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("website"):
                rows.append({
                    "name": row.get("name", ""),
                    "website": row["website"],
                    "city": row.get("city", ""),
                    "phone": row.get("phone", ""),
                })
    return rows


def build(agencies: list, out_path: str):
    existing = load_existing_domains(out_path)
    leads = []
    new = [a for a in agencies if a.get("website") and _domain(a["website"]) not in existing]
    print(f"\n{len(new)} nieuwe bureaus met website om te analyseren "
          f"({len(agencies) - len(new)} overgeslagen: geen site of al bekend).\n")

    for i, a in enumerate(new, 1):
        print(f"[{i}/{len(new)}] {a['name'] or a['website']}")
        signals = analyze_website(a["website"])
        score, reasons = score_lead(signals)
        leads.append({
            "score": score,
            "name": a.get("name", ""),
            "website": a["website"],
            "city": a.get("city", ""),
            "phone": a.get("phone", ""),
            "email": signals["emails"][0] if signals["emails"] else "",
            "reasons": "; ".join(reasons),
            "niche_hits": ", ".join(signals["niche_hits"]),
            "uses_stock": ", ".join(signals["used_stock"]),
        })
        print(f"      score {score} - {'; '.join(reasons)}")

    save_leads(out_path, leads)
    top = sorted(leads, key=lambda x: x["score"], reverse=True)[:10]
    print(f"\nKlaar. {len(leads)} leads opgeslagen in {out_path}.")
    print("\nTop 10:")
    for lead in top:
        print(f"  {lead['score']:>3}  {lead['name'] or lead['website']}  ({lead['email'] or 'geen mail'})")


def main():
    parser = argparse.ArgumentParser(description="Vind reclamebureaus als fotografie-leads.")
    parser.add_argument("--discover", action="store_true", help="Ontdek bureaus via Google Places")
    parser.add_argument("--seed", metavar="CSV", help="Analyseer sites uit een eigen CSV")
    parser.add_argument("--out", default="data/leads.csv", help="Uitvoerbestand (CSV)")
    args = parser.parse_args()

    if args.discover:
        api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        if not api_key:
            print("Geen GOOGLE_PLACES_API_KEY gevonden. Zet die in .env "
                  "of gebruik --seed met een eigen lijst.")
            return
        print("Bureaus ontdekken via Google Places (heel Nederland)...")
        agencies = discover_agencies(api_key)
        build(agencies, args.out)
    elif args.seed:
        agencies = load_seed(args.seed)
        build(agencies, args.out)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
