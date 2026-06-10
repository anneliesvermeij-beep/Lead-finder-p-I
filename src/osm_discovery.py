"""
Ontdekt bureaus via OpenStreetMap (de gratis Overpass-vraagbaak).
Geen account of API-sleutel nodig.

We vragen heel Nederland op naar plekken die als reclame-/marketing-/
ontwerpbureau getagd staan, en halen daar naam, website, stad en telefoon uit.
Alleen bureaus met een ingevulde website doen mee (die kunnen we analyseren).
"""
import time

import requests

import config

# Een paar publieke Overpass-servers; als de eerste druk is, proberen we de volgende.
OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter",
]

# OSM-tags die op een reclame-/ontwerp-/marketingbureau wijzen.
OSM_QUERY = """
[out:json][timeout:240];
area["ISO3166-1"="NL"][admin_level=2]->.nl;
(
  nwr["office"="advertising_agency"](area.nl);
  nwr["office"="graphic_design"](area.nl);
  nwr["office"="marketing"](area.nl);
  nwr["office"="design"](area.nl);
  nwr["shop"="advertising"](area.nl);
  nwr["craft"="designer"](area.nl);
  nwr["name"~"reclamebureau|ontwerpbureau|designbureau|communicatiebureau|grafisch ontwerp",i]["website"](area.nl);
  nwr["name"~"design studio|reclamestudio|ontwerpstudio",i]["website"](area.nl);
);
out tags center;
"""


def _haal_op() -> dict:
    """Stuurt de vraag naar Overpass en geeft de JSON terug (probeert servers af)."""
    headers = {"User-Agent": config.USER_AGENT}
    laatste_fout = None
    for endpoint in OVERPASS_ENDPOINTS:
        try:
            resp = requests.post(
                endpoint, data={"data": OSM_QUERY}, headers=headers, timeout=200
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            laatste_fout = e
            print(f"  ! Overpass-server {endpoint} lukte niet ({type(e).__name__}), volgende proberen…")
            time.sleep(2)
    raise RuntimeError(f"Geen enkele Overpass-server reageerde. Laatste fout: {laatste_fout}")


def _website_van(tags: dict) -> str:
    for sleutel in ("website", "contact:website", "url"):
        if tags.get(sleutel):
            return tags[sleutel].strip()
    return ""


def discover_agencies_osm() -> list:
    """Geeft een lijst bureaus terug: {name, website, city, phone}.
    Alleen bureaus mét website worden meegenomen.
    """
    print("Bureaus ophalen uit OpenStreetMap (heel Nederland)…")
    data = _haal_op()
    elementen = data.get("elements", [])
    print(f"  {len(elementen)} plekken gevonden in OpenStreetMap.")

    bureaus = []
    gezien_sites = set()
    for el in elementen:
        tags = el.get("tags", {})
        website = _website_van(tags)
        if not website:
            continue  # zonder website kunnen we niets analyseren
        sleutel = website.lower().rstrip("/")
        if sleutel in gezien_sites:
            continue
        gezien_sites.add(sleutel)
        bureaus.append({
            "name": tags.get("name", ""),
            "website": website,
            "city": tags.get("addr:city", ""),
            "phone": tags.get("phone", "") or tags.get("contact:phone", ""),
        })

    print(f"  {len(bureaus)} bureaus mét website om te analyseren.")
    return bureaus
