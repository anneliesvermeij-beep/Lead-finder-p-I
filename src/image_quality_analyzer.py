"""
Beeldkwaliteit-analyse: detecteert SLECHTE fotografie op een website. Dat is
voor een fotograaf juist een kans — een bureau met zwak beeld heeft baat bij
betere fotografie.

Vier criteria:
  - stockfoto          : gebruikt stockbeeld (domein / alt-tekst / bestandsnaam)
  - geen_fotos         : geen of nauwelijks (eigen) foto's
  - slechte_belichting : gemiddeld te donker of overbelicht
  - lage_kwaliteit     : onscherp of lage resolutie

Gebruikt Pillow + numpy. Faalt nooit hard: bij twijfel geen criterium.
"""
import io
from urllib.parse import urljoin

import numpy as np
import requests
from bs4 import BeautifulSoup
from PIL import Image

import config

# Aanwijzingen voor stockbeeld in URL of alt-tekst.
STOCK_HINTS = (
    "stock", "shutterstock", "istock", "gettyimages", "getty", "unsplash",
    "pexels", "pixabay", "depositphotos", "adobe", "123rf", "dreamstime", "freepik",
)
# Afbeeldingen die geen 'foto' zijn (logo's, iconen, etc.).
ICON_HINTS = (
    "logo", "icon", "icoon", "sprite", "favicon", "avatar", "placeholder",
    "spinner", "loader", "badge", "pictogram",
)

MAX_BEELDEN = 6        # zoveel foto's downloaden en meten
MIN_FOTOS = 3          # minder dan dit -> 'geen_fotos'
DONKER = 55            # gem. helderheid (0-255) onder dit -> te donker
OVERBELICHT = 205      # boven dit -> overbelicht
MIN_MEGAPIXELS = 0.08  # gem. resolutie onder dit -> lage resolutie
MIN_SCHERPTE = 60.0    # Laplace-variantie onder dit -> onscherp

_sessie = requests.Session()
_sessie.headers.update({"User-Agent": config.USER_AGENT})


def _is_foto(url: str, alt: str) -> bool:
    low = (url + " " + (alt or "")).lower()
    if url[:5].lower().startswith("data:") or ".svg" in low:
        return False
    return not any(h in low for h in ICON_HINTS)


def _is_stock(url: str, alt: str) -> bool:
    # data:-URI's (base64) niet meewegen: hun ruis matcht toevallig hints.
    if url[:5].lower().startswith("data:"):
        return False
    low = (url + " " + (alt or "")).lower()
    if any(d in low for d in config.STOCK_DOMAINS):
        return True
    return any(h in low for h in STOCK_HINTS)


def _laplace_variantie(grijs: np.ndarray) -> float:
    """Variantie van de Laplace (onscherpe beelden = lage variantie)."""
    a = grijs.astype(np.float32)
    lap = (-4 * a[1:-1, 1:-1]
           + a[:-2, 1:-1] + a[2:, 1:-1]
           + a[1:-1, :-2] + a[1:-1, 2:])
    return float(lap.var())


def analyze_image_quality(html: str, base_url: str) -> dict:
    """Analyseert de beelden van een pagina. Geeft {'criteria', 'details'}."""
    soup = BeautifulSoup(html, "html.parser")
    criteria: list = []
    details: dict = {}

    # 1) Verzamel foto-URLs (zonder logo's/iconen/svg) + stockbronnen.
    fotos, stock_bronnen = [], []
    for img in soup.find_all("img"):
        src = img.get("src") or ""
        if not src and img.get("srcset"):
            src = img["srcset"].split(",")[0].split()[0]
        if not src:
            continue
        url = urljoin(base_url, src)
        alt = img.get("alt", "")
        if _is_stock(url, alt):
            stock_bronnen.append(url)
        if _is_foto(url, alt):
            fotos.append(url)

    details["aantal_fotos"] = len(fotos)

    if stock_bronnen:
        criteria.append("stockfoto")
        details["stock_bronnen"] = stock_bronnen[:5]

    if len(fotos) < MIN_FOTOS:
        criteria.append("geen_fotos")

    # 2) Steekproef downloaden en belichting + scherpte/resolutie meten.
    helderheden, scherptes, megapixels = [], [], []
    for url in fotos[:MAX_BEELDEN]:
        try:
            r = _sessie.get(url, timeout=8)
            if r.status_code != 200 or "image" not in r.headers.get("Content-Type", ""):
                continue
            im = Image.open(io.BytesIO(r.content)).convert("L")
            w, h = im.size
            if w < 32 or h < 32:
                continue  # te klein om iets te zeggen
            megapixels.append((w * h) / 1_000_000)
            arr = np.asarray(im)
            helderheden.append(float(arr.mean()))
            if arr.shape[0] > 2 and arr.shape[1] > 2:
                scherptes.append(_laplace_variantie(arr))
        except Exception:
            continue

    # Criterium: slechte belichting (helft of meer van de steekproef slecht).
    if helderheden:
        details["gem_helderheid"] = round(sum(helderheden) / len(helderheden), 1)
        slecht = sum(1 for x in helderheden if x < DONKER or x > OVERBELICHT)
        if slecht >= max(1, len(helderheden) // 2):
            criteria.append("slechte_belichting")

    # Criterium: lage kwaliteit (onscherp of lage resolutie).
    if scherptes:
        details["gem_scherpte"] = round(sum(scherptes) / len(scherptes), 1)
    if megapixels:
        details["gem_megapixels"] = round(sum(megapixels) / len(megapixels), 2)
    onscherp = bool(scherptes) and (sum(scherptes) / len(scherptes)) < MIN_SCHERPTE
    laag_res = bool(megapixels) and (sum(megapixels) / len(megapixels)) < MIN_MEGAPIXELS
    if onscherp or laag_res:
        criteria.append("lage_kwaliteit")

    return {"criteria": criteria, "details": details}
