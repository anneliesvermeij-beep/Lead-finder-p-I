"""
Zet de gevonden signalen om in een score van 0-100 plus een uitleg ('waarom').
De gewichten staan in config.WEIGHTS, zodat je kunt tunen zonder hier te wijzigen.
"""
import config


def score_lead(signals: dict):
    """Geeft (score 0-100, lijst met redenen) terug."""
    w = config.WEIGHTS
    score = 0
    reasons = []

    if signals["reachable"]:
        score += w["reachable"]
    else:
        return 0, ["Website niet bereikbaar"]

    if signals["used_stock"]:
        score += w["uses_stock"]
        reasons.append("Gebruikt stockbeeld (" + ", ".join(signals["used_stock"]) + ")")

    if signals["niche_hits"]:
        bonus = min(len(signals["niche_hits"]) * w["niche_per_keyword"], w["niche_cap"])
        score += bonus
        reasons.append("Past bij jouw werk: " + ", ".join(signals["niche_hits"]))

    if signals["does_campaign_work"]:
        score += w["does_campaign_work"]
        reasons.append("Levert campagne-/cases-werk")

    if signals["emails"]:
        score += w["has_contact_email"]
        reasons.append("Direct te mailen: " + signals["emails"][0])

    if signals["inhouse_photography"]:
        score += w["inhouse_penalty"]
        reasons.append("Doet fotografie mogelijk zelf in huis (-)")

    score = max(0, min(100, score))
    if not reasons:
        reasons.append("Bereikbaar, maar weinig concrete signalen")
    return score, reasons
