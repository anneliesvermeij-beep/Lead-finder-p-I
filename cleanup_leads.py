"""
Opschonen: verwijdert leads met score 0 (niet bereikbaar / foute URL) uit
Supabase, maar behoudt bureaus waar je zelf al een status of notitie bij hebt.
Gebruik: python cleanup_leads.py
"""
import os

from dotenv import load_dotenv

load_dotenv()


def main():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        print("Geen SUPABASE_URL/KEY in .env gevonden.")
        return

    from supabase import create_client
    db = create_client(url, key)

    rows = db.table("leads").select("website,score,status,notes").execute().data or []
    weg = [
        r["website"] for r in rows
        if int(r.get("score") or 0) == 0
        and (r.get("status") or "niet benaderd") == "niet benaderd"
        and not (r.get("notes") or "").strip()
    ]

    print(f"{len(rows)} leads in database, {len(weg)} score-0 leads om te verwijderen.")
    for w in weg:
        db.table("leads").delete().eq("website", w).execute()

    over = len(rows) - len(weg)
    print(f"Klaar. {over} bruikbare leads over in de database.")


if __name__ == "__main__":
    main()
