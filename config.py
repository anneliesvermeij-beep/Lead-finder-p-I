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

# Onder dit aantal leesbare tekens gaan we ervan uit dat een site te 'dun' is
# (vaak een zware JavaScript-site die we niet goed kunnen lezen) -> handmatig checken.
LOW_CONTENT_CHARS = 400

# --- Signaaldetectie ---------------------------------------------------------

STOCK_DOMAINS = [
    "shutterstock", "istockphoto", "gettyimages", "stock.adobe",
    "depositphotos", "unsplash", "pexels", "pixabay", "freepik",
]

# Woorden die wijzen op werk dat past bij jouw expertise (food / product / industrie).
NICHE_KEYWORDS = [
    "food", "foodfotografie", "culinair", "horeca",
    "product", "productfotografie", "packaging", "verpakking", "retail",
    "industrie", "industrieel", "machine", "apparatuur", "fabrikant",
    "technisch", "maakindustrie",
    "campagne", "branding", "merk", "visual", "beeld",
]

# Woorden die suggereren dat een bureau campagne-/klantwerk levert (= regelmatig beeld nodig).
WORK_KEYWORDS = [
    "case", "cases", "portfolio", "ons werk", "sterk werk", "projecten",
    "campagne", "merken", "klanten", "opdrachtgever", "opdrachtgevers",
]

# Sterk signaal dat ze fotografie zélf in huis doen -> minder snel uitbesteden.
INHOUSE_KEYWORDS = ["eigen fotostudio", "in-house fotografie", "eigen studio", "huisfotograaf"]

# --- Scoring (0-100) ---------------------------------------------------------
WEIGHTS = {
    "reachable": 5,
    "uses_stock": 25,
    "photo_credit": 30,        # NIEUW: noemt een fotograaf bij naam -> koopt fotografie in
    "niche_per_keyword": 6,
    "niche_cap": 24,
    "does_campaign_work": 15,
    "has_contact_email": 15,
    "inhouse_penalty": -20,
    "review_floor": 30,        # NIEUW: dunne/JS-sites zakken niet onder deze score
}
