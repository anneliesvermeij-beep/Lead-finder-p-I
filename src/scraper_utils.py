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
    Geeft de requests.Response terug, of None als het niet mag/lukt.
    """
    if not _robots_allows(url):
        return None
    _throttle()
    try:
        resp = _session.get(url, timeout=config.REQUEST_TIMEOUT)
        if resp.status_code == 200 and "text/html" in resp.headers.get("Content-Type", ""):
            return resp
    except requests.RequestException:
        return None
    return None
