"""
Ontdekt bureaus via de ledenlijst van Dutch Digital Agencies (DDA).
DDA bundelt ~147 gevestigde Nederlandse digitale/creatieve bureaus — echte,
actieve bureaus met kloppende websites.

De ledenpagina zelf is JavaScript (niet uit te lezen), maar elke profielpagina
is wél server-side en bevat de echte website. We bezoeken per lid het profiel
en halen daar de website op. De ledenlijst (slugs) staat hieronder; die verandert
maar langzaam. Voeg nieuwe leden toe als DDA er bij krijgt.
"""
import requests

import config

BASIS = "https://dutchdigitalagencies.com/leden/"

# Domeinen die geen bureauwebsite zijn (social, CDN, parent company, etc.).
NIET_WEBSITE = (
    "dutchdigitalagencies", "linkedin", "instagram", "facebook", "twitter",
    "x.com", "youtube", "google", "maps", "datocms-assets", "vimeo",
    "spotify", "apple.com", "play.google", "wa.me", "whatsapp",
)

# DDA-leden (slugs van de profiel-URL). Bijwerken als DDA nieuwe leden krijgt.
DDA_SLUGS = [
    "bold-digital", "webleads", "the-digital-club", "pangaea", "finalist",
    "the-brink-agency", "elastique", "nobears", "gravity", "zuiderlicht",
    "snakeware", "bolden", "cube", "admix", "empathylab", "endeavour", "dpdk",
    "tres", "conclusion", "webbio", "zuid", "uselab", "sturdy-digital", "zooma",
    "yard-digital-agency", "van-ons", "redmatters", "freshheads", "redkiwi",
    "pionect", "de-voorhoede", "kaliber", "faraday", "de-nieuwe-zaak", "norday",
    "info", "we-are-brain", "truelime", "orange-juice", "synetic", "frmwrk",
    "x-interactive", "powerkraut", "new-orange", "bright-digital", "dpi",
    "ontwerpwerk", "bravoure", "axendo", "loyals-groep", "clever-franke",
    "web-nl", "elephant", "framna", "media-monks", "moddit", "social-brothers",
    "harborn", "dept", "level-level", "ennovate", "fourdigits", "fresk-digital",
    "new-story", "frontis", "ronder", "blue-flamingos", "2manydots", "miyagami",
    "digital-natives", "letink-design", "strix", "assist-digital", "keen-design",
    "white", "good-news", "us-media", "unc-inc", "betawerk", "apperium", "lyfter",
    "koos", "x-com-b-v", "qstylez", "icit", "rox-digital-agency", "happy-horizon",
    "dawn-technology", "exitable", "lemone", "steamtalmark", "stimmt",
    "hypersolid", "nedbase", "incentro", "dutchwebdesign", "inventus-online",
    "elgentos-commerce-configurators", "q42", "xsarus", "acato", "i-o", "flink",
    "swis", "alientrick", "handpicked", "supercharge", "bttr", "friday", "trimm",
    "lab-digital", "partout-digital", "youwe", "hoppinger", "digital-impact",
    "september", "dot-control", "stuurlui", "nowonline", "valtech", "maker-street",
    "dij", "greenberry", "enrise", "fabrique", "rb2", "wp-masters", "macaw",
    "buro26", "driebit", "reversed-digital", "maxserv", "hike-one", "valsplat",
    "nextly", "afdeling-online", "icatt", "big-fat-internet", "bluebird-day",
    "adwise-your-digital-brain", "sqli-digital-experience", "linku",
    "mooore-digital", "toon", "jungle-minds", "wirelab", "ranj",
]


def _website_uit_profiel(html: str) -> str:
    """Eerste externe link die een echte bureauwebsite is (geen social/CDN/PDF)."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        low = href.lower()
        if not low.startswith("http"):
            continue
        if low.endswith(".pdf"):
            continue
        if any(s in low for s in NIET_WEBSITE):
            continue
        return href
    return ""


def discover_agencies_dda() -> list:
    """Geeft een lijst bureaus terug: {name, website}. Alleen met gevonden website."""
    print(f"Bureaus ophalen uit Dutch Digital Agencies ({len(DDA_SLUGS)} leden)…")
    headers = {"User-Agent": config.USER_AGENT}
    bureaus = []
    for i, slug in enumerate(DDA_SLUGS, 1):
        try:
            r = requests.get(BASIS + slug + "/", headers=headers, timeout=config.REQUEST_TIMEOUT)
            if r.status_code != 200:
                continue
            website = _website_uit_profiel(r.text)
            if website:
                naam = slug.replace("-", " ").title()
                bureaus.append({"name": naam, "website": website, "city": "", "phone": ""})
        except requests.RequestException:
            continue
        if i % 25 == 0:
            print(f"  {i}/{len(DDA_SLUGS)} profielen bekeken…")

    print(f"  {len(bureaus)} bureaus met website gevonden.")
    return bureaus
