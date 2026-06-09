"""
Opslag in CSV én (optioneel) Supabase.
Supabase wordt gebruikt als SUPABASE_URL en SUPABASE_KEY in .env staan,
zodat CLI-runs automatisch in de cloud-app verschijnen.
"""
import csv
import os
from urllib.parse import urlparse

FIELDS = [
    "score", "review", "name", "website", "city", "email",
    "reasons", "photo_credits", "niche_hits", "uses_stock", "phone",
    "status", "notes", "type",
]


def _domain(url: str) -> str:
    return urlparse(url if url.startswith("http") else "https://" + url).netloc.replace("www.", "")


def _supabase_client():
    """Geeft een Supabase client terug als de omgevingsvariabelen gezet zijn."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        return None
    try:
        from supabase import create_client
        return create_client(url, key)
    except ImportError:
        return None


def load_existing_domains(path: str) -> set:
    """Laadt bekende domeinen uit CSV én Supabase (om dubbelen te voorkomen)."""
    seen = set()

    # Uit CSV
    if os.path.exists(path):
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("website"):
                    seen.add(_domain(row["website"]))

    # Uit Supabase
    client = _supabase_client()
    if client:
        try:
            result = client.table("leads").select("website").execute()
            for row in result.data or []:
                if row.get("website"):
                    seen.add(_domain(row["website"]))
        except Exception:
            pass

    return seen


def save_leads(path: str, leads: list):
    """Schrijft leads naar CSV en (als geconfigureerd) naar Supabase.
    Bestaande notities en status blijven bewaard.
    """
    # Bestaande data laden om notities/status te bewaren
    existing_by_domain: dict = {}
    if os.path.exists(path):
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("website"):
                    existing_by_domain[_domain(row["website"])] = row

    # Supabase: ook bestaande notities/status ophalen
    client = _supabase_client()
    if client:
        try:
            result = client.table("leads").select("website,status,notes,type").execute()
            for row in result.data or []:
                d = _domain(row.get("website", ""))
                if d and d not in existing_by_domain:
                    existing_by_domain[d] = row
        except Exception:
            pass

    new_domains: set = set()
    merged: list = []
    for lead in leads:
        d = _domain(lead.get("website", ""))
        new_domains.add(d)
        existing = existing_by_domain.get(d, {})
        lead.setdefault("status", existing.get("status", ""))
        lead.setdefault("notes", existing.get("notes", ""))
        lead.setdefault("type", existing.get("type") or "bureau")
        merged.append(lead)

    # Bestaande leads die niet opnieuw geanalyseerd zijn behouden
    for d, row in existing_by_domain.items():
        if d not in new_domains:
            merged.append(row)

    merged = sorted(merged, key=lambda x: int(x.get("score") or 0), reverse=True)

    # Naar CSV schrijven
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for lead in merged:
            writer.writerow({k: lead.get(k, "") for k in FIELDS})

    # Naar Supabase schrijven
    if client:
        try:
            records = [{k: lead.get(k, "") for k in FIELDS} for lead in merged]
            for r in records:
                r["score"] = int(r["score"] or 0)
            client.table("leads").upsert(records, on_conflict="website").execute()
            print(f"[OK] {len(records)} leads gesynchroniseerd naar Supabase.")
        except Exception as e:
            print(f"[FOUT] Supabase sync mislukt: {e}")
