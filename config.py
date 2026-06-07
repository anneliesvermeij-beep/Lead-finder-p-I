"""
Centrale instellingen. Pas dit bestand aan om het zoekgedrag en de scoring
te tunen zonder de rest van de code aan te raken.
"""

# --- Ontdekking (Google Places) ---------------------------------------------

# Zoektermen waarmee we bureaus zoeken. Voeg gerust toe of haal weg.
SEARCH_TERMS = [
    "reclamebureau",
    "marketingbureau",
    "creatief bureau",
    "communicatiebureau",
    "designbureau",
    "branding bureau",
]

# Steden die we afgaan om heel Nederland te dekken. Places geeft per zoekopdracht
# maximaal ~60 resultaten, dus we zoeken per stad. Breid uit waar je meer dekking wilt.
CITIES = [
    "Amsterdam", "Rotterdam", "Den Haag", "Utrecht", "Eindhoven",
    "Groningen", "Tilburg", "Almere", "Breda", "Nijmegen",
    "Arnhem", "Haarlem", "Amersfoort", "Den Bosch", "Zwolle",
    "Maastricht", "Leiden", "Enschede", "Apeldoorn", "Deventer",
]

# --- Verzoeken (netjes scrapen) ----------------------------------------------

USER_AGENT = "BureauLeadFinder/1.0 (eigen onderzoek; contact via je-eigen-mail)"
REQUEST_TIMEOUT = 12          # seconden
THROTTLE_SECONDS = 1.5        # minimale pauze tussen twee verzoeken naar het web
MAX_PAGES_PER_SITE = 3        # hoeveel pagina's per bureau-site we maximaal bekijken

# --- Signaaldetectie ---------------------------------------------------------

# Als een site afbeeldingen van deze domeinen gebruikt, werken ze (deels) met
# stockbeeld -> kans voor jou.
STOCK_DOMAINS = [
    "shutterstock", "istockphoto", "gettyimages", "stock.adobe",
    "depositphotos", "unsplash", "pexels", "pixabay", "freepik",
]

# Woorden die wijzen op werk dat past bij jouw expertise (food / product / industrie).
NICHE_KEYWORDS = [
    "food", "foodfotografie", "culinair", "horeca",
    "product", "productfotografie", "packaging", "verpakking", "retail",
    "industrie", "industrieel", "machine", "technisch", "maakindustrie",
    "campagne", "branding", "merk", "visual", "beeld",
]

# Woorden die suggereren dat een bureau campagne-/productiewerk levert
# (dus regelmatig beeld nodig heeft).
WORK_KEYWORDS = ["case", "cases", "portfolio", "ons werk", "projecten", "campagne"]

# Sterk signaal dat ze fotografie zélf in huis doen -> minder snel uitbesteden.
INHOUSE_KEYWORDS = ["eigen fotostudio", "in-house fotografie", "eigen studio", "huisfotograaf"]

# --- Scoring (0-100) ---------------------------------------------------------
# Tune deze gewichten op basis van wat in de praktijk goede leads blijken.
WEIGHTS = {
    "reachable": 5,            # site werkt
    "uses_stock": 30,          # gebruikt stockbeeld -> opening
    "niche_per_keyword": 6,    # per gevonden niche-woord
    "niche_cap": 24,           # maximum dat niche-woorden mogen opleveren
    "does_campaign_work": 15,  # heeft cases/portfolio
    "has_contact_email": 15,   # je kunt ze direct mailen
    "inhouse_penalty": -20,    # doen fotografie zelf
}
