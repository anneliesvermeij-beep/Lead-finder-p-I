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

# Een realistische browser-UA: veel bureausites blokkeren onbekende bots.
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
REQUEST_TIMEOUT = 20          # ruimer: trage servers haalden de 12s niet
THROTTLE_SECONDS = 1.0
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

# BEELD-FOCUS: bureaus die hier vol op zitten kopen het vaakst fotografie in.
# Deze woorden geven een stevige bonus (zie WEIGHTS).
VISUAL_KEYWORDS = [
    "fotografie", "fotograaf", "photography", "beeld", "beeldbank", "beeldtaal",
    "visual", "visuals", "art direction", "artdirection", "styling", "stylist",
    "campagnebeeld", "fotostudio", "filmproductie", "videoproductie", "contentcreatie",
    "content creatie", "creatie", "creative studio", "merkbeeld", "fotoshoot", "shoot",
]

# NIET-PASSEND: research-, tech-, en platformbureaus kopen zelden fotografie in.
# Deze woorden geven een aftrek, zodat ze onder jouw beeldbureaus zakken.
NEGATIVE_KEYWORDS = [
    "marktonderzoek", "onderzoeksbureau", "research", "data science", "datascience",
    "software development", "webdevelopment", "development", "developers",
    "hosting", "webhosting", "seo", "sea ", "e-commerce platform", "webshop laten maken",
    "recruitment", "detachering", "platform", "cloud", "cybersecurity", "saas",
    "ict", "app laten bouwen", "marktplaats",
]

INHOUSE_KEYWORDS = ["eigen fotostudio", "in-house fotografie", "eigen studio", "huisfotograaf"]

# Geen bureaus: marktplaatsen, portals, pure tech/research-bedrijven die door
# toeval beeld-woorden op hun site hebben. Deze domeinen worden uitgesloten.
NON_AGENCY_DOMAINS = [
    "marktplaats.nl", "blauw.com", "funda.nl", "bol.com", "google.com",
    "facebook.com", "linkedin.com", "wikipedia.org", "kvk.nl", "ster.nl",
]

# Woorden in naam/website die op een niet-bureau wijzen (school, horeca, etc.).
# Valse treffers van de OSM-naamzoektocht worden hiermee geweerd.
NON_AGENCY_WORDS = [
    "kindcentrum", "basisschool", "pcbde", "schoolvereniging", "pizzeria",
    "restaurant", "eetcafe", "paviljoen", "brasserie", "camping",
    "kampeerboerderij", "strandpaviljoen", "parochie", "sportschool", "fysio",
    "tandarts", "manege", "dierenarts", "snackbar", "cafetaria",
]

# --- Scoring (0-100) ---------------------------------------------------------
WEIGHTS = {
    "reachable": 5,
    "photo_credit": 30,
    "priority_per_keyword": 12,   # voorkeurswoorden (food/instore) tellen dubbel zo zwaar
    "priority_cap": 36,
    "niche_per_keyword": 6,
    "niche_cap": 24,
    "does_campaign_work": 15,
    "visual_per_keyword": 9,      # beeld/fotografie-focus: stevige bonus
    "visual_cap": 27,
    "negative_per_keyword": -12,  # research/tech/platform: aftrek
    "negative_cap": -36,
    "inhouse_penalty": -20,
    "review_floor": 30,
    # NB: e-mail en stockbeeld tellen bewust NIET meer mee in de score.
    # E-mail = bereikbaarheid (aparte kolom), stockbeeld = te dubbelzinnig.
}
