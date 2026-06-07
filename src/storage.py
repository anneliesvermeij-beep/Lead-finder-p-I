"""
Opslag in een eenvoudig CSV-bestand. Ontdubbelt op website-domein, zodat je
de tool vaker kunt draaien zonder dubbele bureaus te krijgen.
"""
import csv
import os
from urllib.parse import urlparse

FIELDS = [
    "score", "name", "website", "city", "email",
    "reasons", "niche_hits", "uses_stock", "phone",
]


def _domain(url: str) -> str:
    return urlparse(url if url.startswith("http") else "https://" + url).netloc.replace("www.", "")


def load_existing_domains(path: str) -> set:
    """Welke bureaus (op domein) staan er al in het bestand?"""
    if not os.path.exists(path):
        return set()
    seen = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("website"):
                seen.add(_domain(row["website"]))
    return seen


def save_leads(path: str, leads: list):
    """Schrijft leads gesorteerd op score (hoog -> laag) naar CSV."""
    leads = sorted(leads, key=lambda x: x["score"], reverse=True)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for lead in leads:
            writer.writerow({k: lead.get(k, "") for k in FIELDS})
