"""
Centrale instellingen. Pas dit bestand aan om het zoekgedrag en de scoring
te tunen zonder de rest van de code aan te raken.
"""

# --- Ontdekking (Google Places) ---------------------------------------------

SEARCH_TERMS = [
    "reclamebureau",
    "marketingbureau",
    "creatief bureau",
    "communicatiebureau",
    "designbureau",
    "branding bureau",
]

CITIES = [
    "Amsterdam", "Rotterdam", "Den Haag", "Utrecht", "Eindhoven",
    "Groningen", "Tilburg", "Almere", "Breda", "Nijmegen",
    "Arnhem", "Haarlem", "Amersfoort", "Den Bosch", "Zwolle",
    "Maastricht", "Leiden", "Enschede", "Apeldoorn", "Deventer",
]

# --- Verzoeken (netjes scrapen) ----------------------------------------------

USER_AGENT = "BureauLeadFinder/1.0 (eigen onderzoek; contact via je-eigen-mail)"
REQUEST_TIMEOUT = 12
THROTTLE_SECONDS = 1.5
MAX_PAGES_PER_SITE = 3
LOW_CONTENT_CHARS = 400

# --- Signaaldetectie ---------------------------------------------------------

STOCK_DOMAINS = [
    "shutterstock", "istockphoto", "gettyimages", "stock.adobe",
    "depositphotos", "unsplash", "pexels", "pixabay", "freepik",
]

# VOORKEURSWOORDEN: jouw sterkste specialiteit. Deze tellen zwaarder mee
# (zie WEIGHTS hieronder). Pas deze lijst aan als je focus verschuift.
PRIORITY_NICHE_KEYWORDS = [
    "food", "foodfotografie", "culinair", "horeca", "gastronomie",
    "instore", "in-store", "in store", "in-store fotografie",
    "displays", "display", "schap", "shopper", "point of sale", "pos-materiaal",
]

# Algemene niche-woorden die bij jouw expertise passen (tellen normaal mee).
NICHE_KEYWORDS = [
    "product", "productfotografie", "packaging", "verpakking", "retail",
    "industrie", "industrieel", "machine", "apparatuur", "fabrikant",
    "technisch", "maakindustrie",
    "campagne", "branding", "merk", "visual", "beeld",
]

WORK_KEYWORDS = [
    "case", "cases", "portfolio", "ons werk", "sterk werk", "projecten",
    "campagne", "merken", "klanten", "opdrachtgever", "opdrachtgevers",
]

INHOUSE_KEYWORDS = ["eigen fotostudio", "in-house fotografie", "eigen studio", "huisfotograaf"]

# --- Scoring (0-100) ---------------------------------------------------------
WEIGHTS = {
    "reachable": 5,
    "uses_stock": 25,
    "photo_credit": 30,
    "priority_per_keyword": 12,   # voorkeurswoorden (food/instore) tellen dubbel zo zwaar
    "priority_cap": 36,
    "niche_per_keyword": 6,
    "niche_cap": 24,
    "does_campaign_work": 15,
    "has_contact_email": 15,
    "inhouse_penalty": -20,
    "review_floor": 30,
}
