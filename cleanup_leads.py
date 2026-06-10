"""
Opschonen van de leadlijst in Supabase:
  1) Ontdubbelen op domein (ster.nl == www.ster.nl == http://ster.nl/...)
  2) Score-0 leads (niet bereikbaar / foute URL) verwijderen

Bureaus waar jij al een status of notitie bij hebt, blijven altijd staan.
Gebruik: python cleanup_leads.py
"""
import os
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv()


def _domain(u: str) -> str:
    u = u or ""
    return urlparse(u if u.startswith("http") else "https://" + u).netloc.replace("www.", "").lower()


def _aangeraakt(r: dict) -> bool:
    """Heeft de gebruiker dit bureau al een status/notitie gegeven?"""
    return (r.get("status") or "niet benaderd") != "niet benaderd" or bool((r.get("notes") or "").strip())


def main():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        print("Geen SUPABASE_URL/KEY in .env gevonden.")
        return

    from supabase import create_client
    import config
    db = create_client(url, key)

    rows = db.table("leads").select("website,name,score,status,notes").execute().data or []
    start = len(rows)

    # --- 0) Niet-bureaus (marktplaatsen/scholen/horeca/etc.) verwijderen -----
    def _is_niet_bureau(r: dict) -> bool:
        if _domain(r["website"]) in config.NON_AGENCY_DOMAINS:
            return True
        tekst = f"{r.get('name', '')} {r.get('website', '')}".lower()
        return any(w in tekst for w in config.NON_AGENCY_WORDS)

    niet_bureau = [
        r["website"] for r in rows
        if _is_niet_bureau(r) and not _aangeraakt(r)
    ]
    for w in niet_bureau:
        db.table("leads").delete().eq("website", w).execute()
    rows = [r for r in rows if r["website"] not in niet_bureau]

    # --- 1) Ontdubbelen op domein -------------------------------------------
    per_domein: dict = {}
    for r in rows:
        per_domein.setdefault(_domain(r["website"]), []).append(r)

    dubbel_weg = []
    for groep in per_domein.values():
        if len(groep) <= 1:
            continue
        # Behoud de beste: eerst een aangeraakt bureau, anders de hoogste score.
        groep.sort(key=lambda r: (_aangeraakt(r), int(r.get("score") or 0)), reverse=True)
        for r in groep[1:]:
            if not _aangeraakt(r):           # nooit iets met status/notitie weggooien
                dubbel_weg.append(r["website"])

    for w in dubbel_weg:
        db.table("leads").delete().eq("website", w).execute()

    # --- 2) Score-0 verwijderen ---------------------------------------------
    nul_weg = [
        r["website"] for r in rows
        if r["website"] not in dubbel_weg
        and int(r.get("score") or 0) == 0
        and not _aangeraakt(r)
    ]
    for w in nul_weg:
        db.table("leads").delete().eq("website", w).execute()

    over = start - len(set(niet_bureau)) - len(set(dubbel_weg)) - len(set(nul_weg))
    print(f"{start} leads gestart -> {len(niet_bureau)} niet-bureaus, "
          f"{len(dubbel_weg)} dubbel, {len(nul_weg)} score-0 verwijderd.")
    print(f"Klaar. {over} bruikbare leads over in de database.")


if __name__ == "__main__":
    main()
