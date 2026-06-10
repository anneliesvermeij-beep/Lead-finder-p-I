"""
Eenmalige opschoning van leads EN crm_leads:
  1) Niet-bureaus verwijderen (scholen, horeca, kerken, etc. — valse OSM-treffers)
  2) Dubbelen samenvoegen op merknaam-domein (jungleminds.nl == jungleminds.com)

Toon eerst wat er weg zou gaan; verwijder daarna. CRM-leads die je al hebt
aangeraakt (status != nieuw) blijven altijd staan.

Gebruik: python opschonen_nu.py        (toont alleen)
         python opschonen_nu.py --doe  (voert verwijderingen uit)
"""
import argparse
import os
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv()

# Namen/sites die op een niet-bureau wijzen.
JUNK = [
    "kindcentrum", "basisschool", "pcbde", "obs-", "schoolvereniging", "pizzeria",
    "restaurant", "eetcafe", "paviljoen", "brasserie", "camping", "strandpaviljoen",
    "parochie", "sportschool", "fysio", "tandarts", "manege", "dierenarts",
    "snackbar", "cafetaria",
]


def _base(url: str) -> str:
    """Merknaam-domein zonder TLD: jungleminds.com -> jungleminds."""
    net = urlparse(url if url and url.startswith("http") else "https://" + (url or "")).netloc
    net = net.replace("www.", "").lower()
    deel = net.split(".")
    return deel[0] if deel else ""


def is_junk(naam: str, website: str) -> bool:
    h = f"{naam or ''} {website or ''}".lower()
    return any(s in h for s in JUNK)


def schoon_tabel(db, tabel: str, doe: bool):
    naamkol = "bedrijfsnaam" if tabel == "crm_leads" else "name"
    velden = f"id,{naamkol},website,score"
    extra = ",status" if tabel == "crm_leads" else ""
    rows = db.table(tabel).select(velden + extra).execute().data or []
    for r in rows:
        r["_naam"] = r.get(naamkol, "")

    weg_junk, weg_dup = [], []

    # 1) Junk
    overgebleven = []
    for r in rows:
        if is_junk(r.get("_naam", ""), r.get("website", "")):
            if tabel == "crm_leads" and r.get("status", "nieuw") != "nieuw":
                overgebleven.append(r)  # door jou aangeraakt -> behouden
            else:
                weg_junk.append(r)
        else:
            overgebleven.append(r)

    weg_ids = set()

    def dedup(sleutel_fn):
        groepen = {}
        for r in overgebleven:
            if r["id"] in weg_ids:
                continue
            k = sleutel_fn(r)
            if k:
                groepen.setdefault(k, []).append(r)
        for groep in groepen.values():
            if len(groep) <= 1:
                continue
            groep.sort(key=lambda r: int(r.get("score") or 0), reverse=True)
            for r in groep[1:]:
                if tabel == "crm_leads" and r.get("status", "nieuw") != "nieuw":
                    continue
                weg_ids.add(r["id"])
                weg_dup.append(r)

    # 2a) Dubbelen op merknaam-domein (jungleminds.nl == jungleminds.com)
    dedup(lambda r: _base(r.get("website", "")))
    # 2b) Dubbelen op merknaam (Wieden+Kennedy op wk.com én wkams.com)
    dedup(lambda r: (r.get("_naam", "") or "").strip().lower())

    print(f"\n[{tabel}] {len(rows)} rijen -> {len(weg_junk)} junk, {len(weg_dup)} dubbel weg")
    for r in weg_junk[:30]:
        print(f"   junk : {int(r.get('score') or 0):>3} {r['_naam'][:26]:26} {r['website']}")
    for r in weg_dup[:30]:
        print(f"   dup  : {int(r.get('score') or 0):>3} {r['_naam'][:26]:26} {r['website']}")

    if doe:
        for r in weg_junk + weg_dup:
            db.table(tabel).delete().eq("id", r["id"]).execute()
        print(f"   -> {len(weg_junk)+len(weg_dup)} verwijderd.")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--doe", action="store_true", help="Voer de verwijderingen echt uit")
    args = p.parse_args()
    url, key = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY")
    from supabase import create_client
    db = create_client(url, key)
    for tabel in ("leads", "crm_leads"):
        schoon_tabel(db, tabel, args.doe)
    if not args.doe:
        print("\n(Niets verwijderd — draai met --doe om door te voeren.)")


if __name__ == "__main__":
    main()
