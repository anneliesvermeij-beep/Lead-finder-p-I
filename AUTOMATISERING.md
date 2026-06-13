# Hoe vaak zoekt het systeem nieuwe leads?

Een overzicht van wat er **automatisch** gebeurt, en wanneer. Alle tijden zijn
Nederlandse tijd. Je hoeft hier zelf niets voor te doen — het draait vanzelf in
de cloud (GitHub Actions).

---

## 🗓️ Elke maandag, 07:00 — nieuwe bureaus zoeken

Eén keer per week zoekt het systeem nieuwe reclame-/designbureaus en zet die
klaar:

1. **Zoeken** via meerdere bronnen: OpenStreetMap, Dutch Digital Agencies, en
   de seedlijsten (food, industrie, awards, merken, directories).
2. **Analyseren**: elke nieuwe site krijgt een score (food/instore-focus,
   beeldkwaliteit, enz.).
3. **Opschonen**: dode links, dubbelen en niet-bureaus (scholen, horeca) eruit.
4. **Naar de CRM**: nieuwe bureaus komen als **voorraad** in "Alle leads"
   (zonder opvolgdatum, dus ze overspoelen je werklijst niet).

> Workflow: `.github/workflows/weekly_scan.yml`

---

## 📰 Elke dag, 07:30 — werkstapel + nieuws

Elke ochtend gebeuren er twee dingen:

1. **20 nieuwe leads klaarzetten** in "Deze week" — een mix van sterke en
   zwakke scores, uit je voorraad. Zo werk je je hele lijst in een behapbaar
   tempo door (~20 per dag).
2. **Nieuws-check** op je actieve leads — wint een bureau een klant of award,
   dan springt het met een 📰-label naar boven in "Deze week".

> Workflow: `.github/workflows/daily_news.yml`

---

## ✋ Handmatig (wanneer jij wilt)

Deze bronnen ververs ik op verzoek (niet automatisch, want de data is lastig
betrouwbaar te scrapen):

- **Groeibedrijven** (FD Gazellen / D2C-merken met zwakke fotografie) —
  zeg "zoek meer groeibedrijven".
- **Meer bureaus** uit een specifieke niche — zeg bijv. "zoek food-bureaus".

---

## Samengevat

| Wanneer | Wat |
|---|---|
| **Maandag 07:00** | Nieuwe bureaus zoeken → als voorraad in "Alle leads" |
| **Dagelijks 07:30** | 20 leads klaarzetten in "Deze week" + nieuws-check |
| **Op verzoek** | Groeibedrijven & niche-bureaus bijwerken |

Je krijgt dus **elke dag ~20 leads** voorgeschoteld, en je voorraad groeit
**elke week** vanzelf aan.
