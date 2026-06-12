"""
Zet elke dag een werkstapel van (standaard) 20 voorraad-leads klaar om op te
volgen: het zet hun opvolgdatum op vandaag, zodat ze in 'Vandaag' verschijnen.

De selectie is een MIX van goede en slechte leads: we sorteren de voorraad op
score en pakken er gelijkmatig verspreid 20 uit (dus hoog, midden én laag).

Voorraad = crm_leads zonder opvolgdatum en met een open status.
Geen database-wijziging nodig.

Gebruik:
    python dagelijkse_leads.py            # 20 per dag
    python dagelijkse_leads.py --aantal 10
"""
import argparse
import os
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

OPEN_STATUS = ("nieuw", "benaderd", "in_gesprek")


def main():
    p = argparse.ArgumentParser(description="Dagelijkse werkstapel uit de voorraad.")
    p.add_argument("--aantal", type=int, default=20, help="Hoeveel per dag (default 20)")
    args = p.parse_args()

    url, key = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY")
    if not url or not key:
        print("Geen SUPABASE_URL/KEY in .env.")
        return
    from supabase import create_client
    db = create_client(url, key)

    # Voorraad: geen opvolgdatum, open status. Hoogste score eerst.
    voorraad = (
        db.table("crm_leads")
        .select("id,bedrijfsnaam,score,status,bron")
        .is_("volgende_actie_op", "null")
        .eq("bron", "finder")  # alleen bureaus; aparte bronnen hebben eigen tabblad
        .order("score", desc=True)
        .execute()
        .data
        or []
    )
    voorraad = [r for r in voorraad if r.get("status") in OPEN_STATUS]

    if not voorraad:
        print("Voorraad is leeg — geen leads meer om klaar te zetten.")
        return

    n = len(voorraad)
    aantal = min(args.aantal, n)

    # Gelijkmatig verspreid kiezen over de op-score-gesorteerde lijst -> mix.
    if n <= aantal:
        gekozen = voorraad
    else:
        stap = n / aantal
        gekozen = [voorraad[int(i * stap)] for i in range(aantal)]

    vandaag = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    ).isoformat()

    for lead in gekozen:
        db.table("crm_leads").update({"volgende_actie_op": vandaag}).eq("id", lead["id"]).execute()

    scores = [int(r.get("score") or 0) for r in gekozen]
    print(f"{len(gekozen)} leads klaargezet voor vandaag "
          f"(score van {min(scores)} tot {max(scores)}, {n - len(gekozen)} nog in voorraad):")
    for r in gekozen:
        print(f"  {int(r.get('score') or 0):>3}  {r['bedrijfsnaam']}")


if __name__ == "__main__":
    main()
