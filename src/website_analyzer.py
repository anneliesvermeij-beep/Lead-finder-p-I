"""
Analyseert de website van een bureau op signalen die ertoe doen voor jou:
- gebruiken ze stockbeeld? (kans)
- noemen ze food/product/industrie? (past bij jou)
- doen ze campagne-/cases-werk? (hebben regelmatig beeld nodig)
- is er een contact-mailadres? (direct te benaderen)
- doen ze fotografie zelf in huis? (minder snel uitbesteden)

De zware logica zit in extract_signals_from_html(), die puur op een HTML-string
werkt. Daardoor is hij los te testen zonder internet.
"""
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

import config
from src.scraper_utils import polite_get

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
# Adressen die we negeren (voorbeelden, afbeeldingen die op een mail lijken, enz.)
EMAIL_NOISE = ("example.", "sentry.", "@2x", ".png", ".jpg", ".webp")


def extract_signals_from_html(html: str, base_url: str) -> dict:
    """Haalt alle signalen uit één HTML-pagina. Pure functie, geen netwerk."""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator=" ", strip=True).lower()

    # 1) Stockbeeld? Kijk naar img-bronnen en links.
    used_stock = []
    for tag in soup.find_all(["img", "source", "a"]):
        src = (tag.get("src") or tag.get("srcset") or tag.get("href") or "").lower()
        for dom in config.STOCK_DOMAINS:
            if dom in src and dom not in used_stock:
                used_stock.append(dom)

    # 2) Niche-woorden die bij jouw expertise passen.
    niche_hits = sorted({kw for kw in config.NICHE_KEYWORDS if kw in text})

    # 3) Levert dit bureau campagne-/productiewerk?
    does_work = any(kw in text for kw in config.WORK_KEYWORDS)

    # 4) Doen ze fotografie zelf in huis?
    inhouse = any(kw in text for kw in config.INHOUSE_KEYWORDS)

    # 5) Contact-mailadressen (publiek op de site).
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

    # 6) Interne links naar relevante pagina's (cases/diensten/contact) om verder te kijken.
    internal_links = _relevant_internal_links(soup, base_url)

    return {
        "num_images": len(soup.find_all("img")),
        "used_stock": used_stock,
        "niche_hits": niche_hits,
        "does_campaign_work": does_work,
        "inhouse_photography": inhouse,
        "emails": sorted(emails),
        "internal_links": internal_links,
    }


def _relevant_internal_links(soup, base_url):
    """Vindt links op dezelfde site naar cases/diensten/contact-achtige pagina's."""
    targets = ("case", "werk", "portfolio", "dienst", "service",
               "contact", "over", "about", "project")
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
        "reachable": False, "num_images": 0, "used_stock": [],
        "niche_hits": [], "does_campaign_work": False,
        "inhouse_photography": False, "emails": [],
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

    # Bekijk een paar relevante subpagina's mee (cases/contact e.d.).
    pages_seen = 1
    for link in signals["internal_links"]:
        if pages_seen >= config.MAX_PAGES_PER_SITE:
            break
        sub = polite_get(link)
        pages_seen += 1
        if sub is None:
            continue
        sub_signals = extract_signals_from_html(sub.text, link)
        # Voeg de signalen samen (set-achtig).
        signals["used_stock"] = list(set(signals["used_stock"]) | set(sub_signals["used_stock"]))
        signals["niche_hits"] = sorted(set(signals["niche_hits"]) | set(sub_signals["niche_hits"]))
        signals["does_campaign_work"] |= sub_signals["does_campaign_work"]
        signals["inhouse_photography"] |= sub_signals["inhouse_photography"]
        signals["emails"] = sorted(set(signals["emails"]) | set(sub_signals["emails"]))
        result["num_images"] += sub_signals["num_images"]

    result.update({
        "num_images": result["num_images"] + signals["num_images"],
        "used_stock": signals["used_stock"],
        "niche_hits": signals["niche_hits"],
        "does_campaign_work": signals["does_campaign_work"],
        "inhouse_photography": signals["inhouse_photography"],
        "emails": signals["emails"],
    })
    return result
