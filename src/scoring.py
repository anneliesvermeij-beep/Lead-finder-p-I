"""
Zet de gevonden signalen om in een score van 0-100, een lijst met redenen, en
een vlag of het bureau handmatig gecheckt moet worden (dunne/JS-site).
Gewichten staan in config.WEIGHTS, zodat je kunt tunen zonder hier te wijzigen.
"""
import config


def score_lead(signals: dict):
    """Geeft (score 0-100, redenen, needs_review) terug."""
    w = config.WEIGHTS
    score = 0
    reasons = []
    needs_review = False

    if not signals["reachable"]:
        return 0, ["Website niet bereikbaar"], False
    score += w["reachable"]

    # Sterkste signaal: noemt een fotograaf bij naam -> koopt fotografie in.
    if signals.get("photo_credits"):
        score += w["photo_credit"]
        reasons.append("Noemt een fotograaf bij naam: " + signals["photo_credits"][0])

    if signals["used_stock"]:
        score += w["uses_stock"]
        reasons.append("Gebruikt stockbeeld (" + ", ".join(signals["used_stock"]) + ")")

    # Voorkeurswoorden (food/instore) tellen zwaarder mee.
    priority = signals.get("priority_hits", [])
    if priority:
        bonus = min(len(priority) * w["priority_per_keyword"], w["priority_cap"])
        score += bonus
        reasons.append("Sterke match (jouw specialiteit): " + ", ".join(priority))

    # Overige niche-woorden (zonder de voorkeurswoorden dubbel te tellen).
    general = [x for x in signals["niche_hits"] if x not in priority]
    if general:
        bonus = min(len(general) * w["niche_per_keyword"], w["niche_cap"])
        score += bonus
        reasons.append("Past bij jouw werk: " + ", ".join(general))

    # Beeld-/fotografiefocus: sterkste teken dat ze fotografie nodig hebben.
    visual = signals.get("visual_hits", [])
    if visual:
        bonus = min(len(visual) * w["visual_per_keyword"], w["visual_cap"])
        score += bonus
        reasons.append("Beeld-/fotografiefocus: " + ", ".join(visual))

    # Research-/tech-/platformbureau: kopen zelden fotografie in -> aftrek.
    # Maar: een bureau met duidelijke beeldfocus (2+ visual-woorden) straffen we
    # niet voor een incidentele 'platform'-vermelding; alleen echte tech-bureaus.
    negative = signals.get("negative_hits", [])
    if negative and len(visual) < 2:
        straf = max(len(negative) * w["negative_per_keyword"], w["negative_cap"])
        score += straf
        reasons.append("Minder passend (research/tech/platform): " + ", ".join(negative))

    if signals["does_campaign_work"]:
        score += w["does_campaign_work"]
        reasons.append("Levert campagne-/klantwerk")

    if signals["emails"]:
        score += w["has_contact_email"]
        reasons.append("Direct te mailen: " + signals["emails"][0])

    if signals["inhouse_photography"]:
        score += w["inhouse_penalty"]
        reasons.append("Doet fotografie mogelijk zelf in huis (-)")

    # Dunne/JS-site: niet afschrijven, maar markeren voor handmatige check.
    if signals.get("low_content"):
        needs_review = True
        reasons.append("Weinig leesbare inhoud (mogelijk JS-site) - handmatig checken")
        score = max(score, w["review_floor"])

    score = max(0, min(100, score))
    if not reasons:
        reasons.append("Bereikbaar, maar weinig concrete signalen")
    return score, reasons, needs_review
