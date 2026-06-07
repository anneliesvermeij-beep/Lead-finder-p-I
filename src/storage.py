"""
Opslag in een eenvoudig CSV-bestand. Ontdubbelt op website-domein, zodat je
de tool vaker kunt draaien zonder dubbele bureaus te krijgen.
"""
import csv
import os
from urllib.parse import urlparse

FIELDS = [
    "score", "review", "name", "website", "city", "email",
    "reasons", "photo_credits", "niche_hits", "uses_stock", "phone",
    "status", "notes",
]


def _domain(url: str) -> str:
    return urlparse(url if url.startswith("http") else "https://" + url).netloc.replace("www.", "")


def load_existing_domains(path: str) -> set:
    if not os.path.exists(path):
        return set()
    seen = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("website"):
                seen.add(_domain(row["website"]))
    return seen


def save_leads(path: str, leads: list):
    """Schrijft leads gesorteerd op score (hoog -> laag) naar CSV.
    Bestaande leads worden samengevoegd: notities en status blijven bewaard,
    en eerder gevonden bureaus die niet opnieuw geanalyseerd worden verdwijnen niet.
    """
    # Load existing rows so we can preserve notes/status and keep old entries.
    existing_by_domain: dict = {}
    if os.path.exists(path):
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("website"):
                    existing_by_domain[_domain(row["website"])] = row

    new_domains: set = set()
    merged: list = []
    for lead in leads:
        d = _domain(lead.get("website", ""))
        new_domains.add(d)
        existing = existing_by_domain.get(d, {})
        # Preserve CRM fields that the CLI doesn't set
        lead.setdefault("status", existing.get("status", ""))
        lead.setdefault("notes", existing.get("notes", ""))
        merged.append(lead)

    # Keep existing entries that were not re-analysed in this run
    for d, row in existing_by_domain.items():
        if d not in new_domains:
            merged.append(row)

    merged = sorted(merged, key=lambda x: int(x.get("score") or 0), reverse=True)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for lead in merged:
            writer.writerow({k: lead.get(k, "") for k in FIELDS})
