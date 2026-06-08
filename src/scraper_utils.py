"""
Netjes verzoeken doen: één globale snelheidsrem, een nette User-Agent, en
respect voor robots.txt. Hierdoor belast je servers niet en blijf je netjes.
"""
import time
import urllib.robotparser
from urllib.parse import urlparse

import requests

import config

_session = requests.Session()
_session.headers.update({"User-Agent": config.USER_AGENT})

_last_request_at = 0.0          # tijdstip van laatste verzoek (globale rem)
_robots_cache = {}              # domein -> RobotFileParser (gecachet)


def _throttle():
    """Wacht zo nodig zodat we niet sneller gaan dan THROTTLE_SECONDS."""
    global _last_request_at
    elapsed = time.time() - _last_request_at
    if elapsed < config.THROTTLE_SECONDS:
        time.sleep(config.THROTTLE_SECONDS - elapsed)
    _last_request_at = time.time()


def _robots_allows(url: str) -> bool:
    """Checkt of robots.txt het ophalen van deze URL toestaat."""
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    if base not in _robots_cache:
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(f"{base}/robots.txt")
        try:
            rp.read()
        except Exception:
            # Geen leesbare robots.txt -> we gaan ervan uit dat het mag,
            # maar blijven netjes door de throttle.
            rp = None
        _robots_cache[base] = rp
    rp = _robots_cache[base]
    if rp is None:
        return True
    return rp.can_fetch(config.USER_AGENT, url)


def polite_get(url: str):
    """
    Haalt een pagina op met respect voor robots.txt en snelheidsrem.
    Volgt redirects, accepteert HTML-pagina's ook zonder nette Content-Type,
    en probeert het bij een time-out/netwerkfout één keer opnieuw.
    Geeft de requests.Response terug, of None als het niet mag/lukt.
    """
    if not _robots_allows(url):
        return None

    for poging in range(2):  # één retry bij tijdelijke fouten
        _throttle()
        try:
            resp = _session.get(url, timeout=config.REQUEST_TIMEOUT, allow_redirects=True)
            ctype = resp.headers.get("Content-Type", "").lower()
            # Accepteer als het HTML is, of als de server geen type meldt maar
            # de inhoud op HTML lijkt (veel bureausites zetten geen header).
            looks_html = "html" in ctype or (not ctype and "<html" in resp.text[:2000].lower())
            if resp.status_code == 200 and looks_html:
                return resp
            return None  # 404/403 etc.: opnieuw proberen heeft geen zin
        except requests.RequestException:
            if poging == 0:
                continue  # tweede poging
            return None
    return None
