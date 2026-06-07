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
EMAIL_NOISE = ("example.", "sentry.", "@2x", ".png", ".jpg", ".webp")

# Herkent een fotocredit zoals "Fotografie: Goffe Struiksma" of "Foto: Jan Jansen".
# Eis: een label, dan dubbele punt/streepje, dan een naam met hoofdletter.
PHOTO_CREDIT_RE = re.compile(
    r"\b((?i:fotografie|fotograaf|photography|photo|foto|beeld))\s*[:\-–]\s*"
    r"([A-ZÀ-Þ][\wÀ-ÿ]+(?:\s+[A-ZÀ-Þ][\wÀ-ÿ]+)?)"
)


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
    photo_credits = []
    for label, name in PHOTO_CREDIT_RE.findall(text_raw):
        credit = f"{label}: {name}"
        if credit not in photo_credits:
            photo_credits.append(credit)

    # 3) Niche-woorden. Voorkeurswoorden (food/instore) apart, want die wegen zwaarder.
    priority_hits = sorted({kw for kw in config.PRIORITY_NICHE_KEYWORDS if kw in text})
    niche_hits = sorted({kw for kw in config.NICHE_KEYWORDS if kw in text})

    # 4) Levert dit bureau campagne-/klantwerk?
    does_work = any(kw in text for kw in config.WORK_KEYWORDS)

    # 5) Doen ze fotografie zelf in huis?
    inhouse = any(kw in text for kw in config.INHOUSE_KEYWORDS)

    # 6) Contact-mailadressen.
    emails = set()
    for mail in EMAIL_RE.findall(html):
        low = mail.lower()
        if not any(n in low for n in EMAIL_NOISE):
            emails.add(low)
    for a in soup.find_all("a", href=True):
        if a["href"].lower().startswith("mailto:"):
            addr = a["href"][7:].split("?")[0].strip().lower()
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


def analyze_website(url: str) -> dict:
    """Haalt de homepage (+ enkele subpagina's) op en bundelt de signalen."""
    result = {
        "reachable": False, "num_images": 0, "text_length": 0, "used_stock": [],
        "photo_credits": [], "priority_hits": [], "niche_hits": [], "does_campaign_work": False,
        "inhouse_photography": False, "emails": [], "low_content": False,
    }
    if not url:
        return result
    if not url.startswith("http"):
        url = "https://" + url

    home = polite_get(url)
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
        "does_campaign_work": signals["does_campaign_work"],
        "inhouse_photography": signals["inhouse_photography"],
        "emails": signals["emails"],
        "low_content": total_text < config.LOW_CONTENT_CHARS,
    })
    return result
