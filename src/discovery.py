"""
Ontdekt bureaus via de Google Places API (de nieuwe 'searchText'-endpoint).
Per stad x zoekterm doen we een zoekopdracht en bladeren we door de pagina's.

Je hebt hiervoor een eigen Google Places API-sleutel nodig (zet die in .env).
Zonder sleutel kun je nog steeds de --seed modus gebruiken (zie README).
"""
import time

import requests

import config

PLACES_URL = "https://places.googleapis.com/v1/places:searchText"
FIELD_MASK = (
    "places.displayName,places.formattedAddress,places.websiteUri,"
    "places.id,places.nationalPhoneNumber,nextPageToken"
)


def _search_once(query: str, api_key: str, page_token: str | None = None):
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": FIELD_MASK,
    }
    body = {"textQuery": query, "languageCode": "nl", "regionCode": "NL"}
    if page_token:
        body["pageToken"] = page_token
    resp = requests.post(PLACES_URL, headers=headers, json=body, timeout=config.REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def discover_agencies(api_key: str, cities=None, terms=None) -> list:
    """Geeft een lijst bureaus terug: {name, address, website, city, phone, place_id}."""
    cities = cities or config.CITIES
    terms = terms or config.SEARCH_TERMS
    found = {}  # place_id -> dict (ontdubbelt automatisch)

    for city in cities:
        for term in terms:
            query = f"{term} {city}"
            token = None
            for _ in range(3):  # max ~60 resultaten per query (3 pagina's)
                try:
                    data = _search_once(query, api_key, token)
                except requests.HTTPError as e:
                    print(f"  ! Fout bij '{query}': {e}")
                    break
                for p in data.get("places", []):
                    pid = p.get("id")
                    if not pid or pid in found:
                        continue
                    found[pid] = {
                        "place_id": pid,
                        "name": p.get("displayName", {}).get("text", ""),
                        "address": p.get("formattedAddress", ""),
                        "website": p.get("websiteUri", ""),
                        "phone": p.get("nationalPhoneNumber", ""),
                        "city": city,
                    }
                token = data.get("nextPageToken")
                if not token:
                    break
                time.sleep(2)  # token heeft even tijd nodig voor hij geldig is
            print(f"  {query}: {len(found)} bureaus totaal")
    return list(found.values())
