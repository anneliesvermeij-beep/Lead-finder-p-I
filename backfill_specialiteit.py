"""
Eenmalige bijwerking: vult de 'specialiteit'-kolom (niche_hits) van bestaande
leads met o.a. food/instore, die wel in 'reasons' staan maar niet los waren
opgeslagen. Geen herscan nodig.
Gebruik: python backfill_specialiteit.py
"""
import os

from dotenv import load_dotenv

load_dotenv()

PREFIXEN = (
    "Sterke match (jouw specialiteit): ",
    "Past bij jouw werk: ",
    "Beeld-/fotografiefocus: ",
)


def specialiteit_uit_reasons(reasons: str) -> str:
    woorden = []
    for deel in (reasons or "").split(";"):
        deel = deel.strip()
        for pre in PREFIXEN:
            if deel.startswith(pre):
                for kw in deel[len(pre):].split(","):
                    kw = kw.strip()
                    if kw and kw not in woorden:
                        woorden.append(kw)
    return ", ".join(woorden)


def main():
    url, key = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY")
    if not url or not key:
        print("Geen SUPABASE_URL/KEY in .env gevonden.")
        return

    from supabase import create_client
    db = create_client(url, key)

    rows = db.table("leads").select("website,reasons,niche_hits").execute().data or []
    bijgewerkt = 0
    for r in rows:
        nieuw = specialiteit_uit_reasons(r.get("reasons", ""))
        if nieuw and nieuw != (r.get("niche_hits") or ""):
            db.table("leads").update({"niche_hits": nieuw}).eq("website", r["website"]).execute()
            bijgewerkt += 1

    print(f"{len(rows)} leads bekeken, {bijgewerkt} specialiteit-velden bijgewerkt.")


if __name__ == "__main__":
    main()
