"""
Analyseert de website van een bureau op signalen die ertoe doen voor jou:
- noemen ze een fotograaf bij naam? ("Fotografie: ...") -> koopt fotografie in (sterk!)
- gebruiken ze stockbeeld? (kans)
- noemen ze food/product/industrie? (past bij jou)
- doen ze campagne-/klantwerk? (hebben regelmatig beeld nodig)
- is er een contact-mailadres? (direct te benaderen)
- doen ze fotografie zelf in huis? (minder snel uitbesteden)
- is de site te 'dun' om te lezen? (vaak JS-site -> handmatig checken)

De zware logica zit in extract_signals_from_html(), die puur op een HTML-string
werkt. Daardoor is hij los te testen zonder internet.
"""
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

import config
from src.scraper_utils import polite_get

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
EMAIL_NOISE = (
    "example.", "sentry", "wixpress", "@2x", ".png", ".jpg", ".jpeg", ".webp",
    "@domain.com", "user@", "@sentry", "@email.com", "name@", "yourname@",
    "gebruiker@", "domein.com", "jouwnaam@", "voorbeeld@", "@example", "test@",
)

# Herkent een fotocredit zoals "Fotografie: Goffe Struiksma" of "Foto: Jan Jansen".
# Eis: een label, dan dubbele punt/streepje, dan TWEE woorden met een hoofdletter
# (voor- en achternaam) -> filtert losse onzin als "Foto: Beeld" eruit.
PHOTO_CREDIT_RE = re.compile(
    r"\b((?i:fotografie|fotograaf|photography|photographer|foto|photo|beeld))\s*[:\-–]\s*"
    r"([A-ZÀ-Þ][a-zà-ÿ]+\s+[A-ZÀ-Þ][a-zà-ÿ]+)"
)

# Woorden die op een naam lijken maar het niet zijn: als één van beide
# naamdelen hierin zit (of erop eindigt), is het geen echte fotocredit.
_NIET_NAAM = {
    "website", "websiteontwikkeling", "ontwikkeling", "duitstalig", "engelstalig",
    "beeld", "design", "fotografie", "video", "tekst", "concept", "campagne",
    "studio", "bureau", "agency", "media", "creatie", "branding", "online",
    "marketing", "communicatie", "webdesign", "drukwerk", "copyright",
}
_NIET_NAAM_EINDE = ("ontwikkeling", "talig", "bureau", "design", "fotografie")


def _is_echte_naam(naam: str) -> bool:
    """True als 'Voornaam Achternaam' op een echte persoonsnaam lijkt."""
    delen = naam.split()
    if len(delen) != 2:
        return False
    for d in delen:
        low = d.lower()
        if low in _NIET_NAAM or low.endswith(_NIET_NAAM_EINDE):
            return False
    return True


def _zoek_woorden(text: str, keywords) -> list:
    """Geeft de keywords terug die als héél woord/zinsdeel in de tekst staan.
    Zo matcht 'ict' niet binnen 'gericht' en 'beeld' niet binnen 'afbeelding'.
    (text moet al lowercase zijn.)
    """
    hits = []
    for kw in keywords:
        patroon = r"(?<![a-z0-9])" + re.escape(kw.lower().strip()) + r"(?![a-z0-9])"
        if re.search(patroon, text):
            hits.append(kw.strip())
    return sorted(set(hits))


def extract_signals_from_html(html: str, base_url: str) -> dict:
    """Haalt alle signalen uit één HTML-pagina. Pure functie, geen netwerk."""
    soup = BeautifulSoup(html, "html.parser")
    text_raw = soup.get_text(separator=" ", strip=True)   # met hoofdletters (voor namen)
    text = text_raw.lower()

    # 1) Stockbeeld?
    used_stock = []
    for tag in soup.find_all(["img", "source", "a"]):
        src = (tag.get("src") or tag.get("srcset") or tag.get("href") or "").lower()
        for dom in config.STOCK_DOMAINS:
            if dom in src and dom not in used_stock:
                used_stock.append(dom)

    # 2) Fotocredits ("Fotografie: Naam") -> bewijs dat ze fotografie inkopen.
    #    Alleen tellen als de naam echt op een persoonsnaam lijkt.
    photo_credits = []
    for label, name in PHOTO_CREDIT_RE.findall(text_raw):
        if not _is_echte_naam(name):
            continue
        credit = f"{label}: {name}"
        if credit not in photo_credits:
            photo_credits.append(credit)

    # 3) Niche-woorden. Op héle woorden matchen, zodat "ict" niet in "gericht"
    #    en "beeld" niet in "afbeelding" wordt gevonden. Voorkeurswoorden
    #    (food/instore) apart, want die wegen zwaarder.
    priority_hits = _zoek_woorden(text, config.PRIORITY_NICHE_KEYWORDS)
    niche_hits = _zoek_woorden(text, config.NICHE_KEYWORDS)
    visual_hits = _zoek_woorden(text, config.VISUAL_KEYWORDS)
    negative_hits = _zoek_woorden(text, config.NEGATIVE_KEYWORDS)

    # 4) Levert dit bureau campagne-/klantwerk?
    does_work = any(kw in text for kw in config.WORK_KEYWORDS)

    # 5) Doen ze fotografie zelf in huis?
    inhouse = any(kw in text for kw in config.INHOUSE_KEYWORDS)

    # 6) Contact-mailadressen.
    def _schoon(addr: str) -> str:
        # Strip URL-encoding (%20) en losse rommel aan de randen.
        return addr.replace("%20", "").strip(" .,-").lower()

    emails = set()
    for mail in EMAIL_RE.findall(html):
        low = _schoon(mail)
        if low and not any(n in low for n in EMAIL_NOISE):
            emails.add(low)
    for a in soup.find_all("a", href=True):
        if a["href"].lower().startswith("mailto:"):
            addr = _schoon(a["href"][7:].split("?")[0])
            if addr and not any(n in addr for n in EMAIL_NOISE):
                emails.add(addr)

    # 7) Interne links naar relevante pagina's om verder te kijken.
    internal_links = _relevant_internal_links(soup, base_url)

    return {
        "num_images": len(soup.find_all("img")),
        "text_length": len(text_raw),
        "used_stock": used_stock,
        "photo_credits": photo_credits,
        "priority_hits": priority_hits,
        "niche_hits": niche_hits,
        "visual_hits": visual_hits,
        "negative_hits": negative_hits,
        "does_campaign_work": does_work,
        "inhouse_photography": inhouse,
        "emails": sorted(emails),
        "internal_links": internal_links,
    }


def _relevant_internal_links(soup, base_url):
    targets = ("case", "werk", "portfolio", "dienst", "service",
               "contact", "over", "about", "project", "merk", "klant")
    domain = urlparse(base_url).netloc
    found = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        full = urljoin(base_url, href)
        if urlparse(full).netloc != domain:
            continue
        if any(t in href.lower() for t in targets) and full not in found:
            found.append(full)
    return found[: config.MAX_PAGES_PER_SITE]


def _url_varianten(url: str):
    """Geeft te proberen URL-varianten in volgorde van waarschijnlijkheid.
    Zo vangen we 'niet bereikbaar' op die eigenlijk http/https of www betreft.
    """
    url = url.strip().rstrip("/")
    # Haal een eventueel schema en www. weg om de kale host te krijgen.
    kaal = re.sub(r"^https?://", "", url, flags=re.I)
    kaal = re.sub(r"^www\.", "", kaal, flags=re.I)
    varianten = [
        "https://" + kaal,
        "https://www." + kaal,
        "http://" + kaal,
        "http://www." + kaal,
    ]
    # Behoud een eventueel oorspronkelijk volledig adres vooraan.
    if url.lower().startswith("http") and url not in varianten:
        varianten.insert(0, url)
    # Ontdubbel met behoud van volgorde.
    gezien, uniek = set(), []
    for v in varianten:
        if v not in gezien:
            gezien.add(v)
            uniek.append(v)
    return uniek


def analyze_website(url: str) -> dict:
    """Haalt de homepage (+ enkele subpagina's) op en bundelt de signalen."""
    result = {
        "reachable": False, "num_images": 0, "text_length": 0, "used_stock": [],
        "photo_credits": [], "priority_hits": [], "niche_hits": [], "visual_hits": [],
        "negative_hits": [], "does_campaign_work": False,
        "inhouse_photography": False, "emails": [], "low_content": False,
    }
    if not url:
        return result

    # Probeer meerdere varianten: een 'niet bereikbaar' is vaak alleen het
    # verkeerde schema (http/https) of het ontbreken van www.
    home = None
    for kandidaat in _url_varianten(url):
        home = polite_get(kandidaat)
        if home is not None:
            url = str(home.url) or kandidaat   # gebruik de uiteindelijke URL na redirect
            break
    if home is None:
        return result

    result["reachable"] = True
    signals = extract_signals_from_html(home.text, url)
    total_text = signals["text_length"]

    pages_seen = 1
    for link in signals["internal_links"]:
        if pages_seen >= config.MAX_PAGES_PER_SITE:
            break
        sub = polite_get(link)
        pages_seen += 1
        if sub is None:
            continue
        s = extract_signals_from_html(sub.text, link)
        signals["used_stock"] = list(set(signals["used_stock"]) | set(s["used_stock"]))
        signals["photo_credits"] = list(dict.fromkeys(signals["photo_credits"] + s["photo_credits"]))
        signals["niche_hits"] = sorted(set(signals["niche_hits"]) | set(s["niche_hits"]))
        signals["priority_hits"] = sorted(set(signals["priority_hits"]) | set(s["priority_hits"]))
        signals["visual_hits"] = sorted(set(signals["visual_hits"]) | set(s["visual_hits"]))
        signals["negative_hits"] = sorted(set(signals["negative_hits"]) | set(s["negative_hits"]))
        signals["does_campaign_work"] |= s["does_campaign_work"]
        signals["inhouse_photography"] |= s["inhouse_photography"]
        signals["emails"] = sorted(set(signals["emails"]) | set(s["emails"]))
        result["num_images"] += s["num_images"]
        total_text += s["text_length"]

    result.update({
        "num_images": result["num_images"] + signals["num_images"],
        "text_length": total_text,
        "used_stock": signals["used_stock"],
        "photo_credits": signals["photo_credits"],
        "priority_hits": signals["priority_hits"],
        "niche_hits": signals["niche_hits"],
        "visual_hits": signals["visual_hits"],
        "negative_hits": signals["negative_hits"],
        "does_campaign_work": signals["does_campaign_work"],
        "inhouse_photography": signals["inhouse_photography"],
        "emails": signals["emails"],
        "low_content": total_text < config.LOW_CONTENT_CHARS,
    })
    return result
