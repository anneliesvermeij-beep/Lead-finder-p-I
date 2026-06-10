"""
Eenmalige bijwerking: zet de score op bestaande crm_leads, door per bureau de
score uit de finder-tabel (leads) op te zoeken via het website-domein.
Vereist de score-kolom in crm_leads (zie SQL) en de geheime service-sleutel.

Gebruik: python backfill_score.py
"""
import os
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv()


def _domain(u: str) -> str:
    u = u or ""
    return urlparse(u if u.startswith("http") else "https://" + u).netloc.replace("www.", "").lower()


def main():
    url, key = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY")
    if not url or not key:
        print("Geen SUPABASE_URL/KEY in .env.")
        return
    from supabase import create_client
    db = create_client(url, key)

    # Score per domein uit de finder
    finder = db.table("leads").select("website,score").execute().data or []
    score_per_domein = {}
    for r in finder:
        d = _domain(r.get("website", ""))
        if d:
            score_per_domein[d] = int(r.get("score") or 0)

    crm = db.table("crm_leads").select("id,website,score").execute().data or []
    bijgewerkt = 0
    for lead in crm:
        d = _domain(lead.get("website", ""))
        nieuw = score_per_domein.get(d)
        if nieuw is not None and nieuw != (lead.get("score") or 0):
            db.table("crm_leads").update({"score": nieuw}).eq("id", lead["id"]).execute()
            bijgewerkt += 1

    print(f"{len(crm)} CRM-leads bekeken, {bijgewerkt} scores bijgewerkt.")


if __name__ == "__main__":
    main()
