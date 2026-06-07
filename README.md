# Bureau Lead Finder

Vindt reclame- en marketingbureaus in heel Nederland en scoort ze als
fotografie-lead. Per bureau kijkt de tool naar de website en zoekt signalen die
ertoe doen: gebruiken ze stockbeeld, doen ze campagne-/cases-werk, noemen ze
food/product/industrie, en is er een mailadres om ze te benaderen?

De uitkomst is een gesorteerde CSV (`data/leads.csv`) met de beste leads bovenaan,
inclusief een korte uitleg *waarom* elk bureau interessant is.

## Wat het wél en niet doet

Dit is bewust een **eenvoudige pijplijn**, geen "agent-zwerm". Het verzamelt en
scoort bureaus. Het benadert niemand automatisch — jij beslist wie je mailt.
De tool scrapet geen LinkedIn (tegen hun voorwaarden) en houdt zich aan
`robots.txt` met een rustige snelheid tussen verzoeken.

## Installatie

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Gebruik

**Optie A — direct testen, zonder API-sleutel** (analyseert een eigen lijstje):

```bash
python main.py --seed data/seed_example.csv
```

Vul `seed_example.csv` met bureaus die je al kent (kolommen: `name,website,city`)
om de scoring meteen te zien werken.

**Optie B — heel Nederland ontdekken** (Google Places):

1. Maak een Google Cloud-project en zet de **Places API (New)** aan.
2. Maak een API-sleutel.
3. Kopieer `.env.example` naar `.env` en zet je sleutel erin.
4. Draai:

```bash
python main.py --discover
```

> Let op: Places rekent per zoekopdracht af. De stedenlijst in `config.py`
> bepaalt hoeveel zoekopdrachten je doet (steden × zoektermen). Begin klein
> (bijv. 3 steden) om de kosten te zien voor je heel Nederland afgaat.

## De uitvoer (`data/leads.csv`)

| kolom | betekenis |
|-------|-----------|
| `score` | 0-100, hoger = interessanter |
| `name`, `website`, `city`, `phone` | basisgegevens |
| `email` | publiek mailadres van de site (voor je outreach) |
| `reasons` | waarom dit een lead is |
| `niche_hits` | gevonden woorden die bij jouw werk passen |
| `uses_stock` | gedetecteerde stockbeeld-bronnen |

Draai je de tool nog eens, dan worden al bekende bureaus (op domein) overgeslagen.

## Tunen

Alle knoppen zitten in `config.py`:
- `CITIES` / `SEARCH_TERMS` — waar en waarop je zoekt.
- `PRIORITY_NICHE_KEYWORDS` — jouw sterkste specialiteit (bv. food, instore). Deze
  woorden tellen zwaarder dan gewone niche-woorden; verschuif je focus door woorden
  hier toe te voegen of weg te halen.
- `NICHE_KEYWORDS` — overige woorden die bij je werk passen (product/industrie/enz.).
- `WEIGHTS` — hoe zwaar elk signaal meetelt. `priority_per_keyword` en `priority_cap`
  bepalen hoe hard food/instore meewegen.

Bekijk na een eerste run welke bureaus terecht hoog/laag scoren en stel de
gewichten bij. Dat is de snelste manier om de lijst beter te maken.

## Projectstructuur

```
bureau-lead-finder/
├── main.py                 # start hier (CLI)
├── config.py               # alle instellingen
├── src/
│   ├── discovery.py        # bureaus zoeken via Google Places
│   ├── website_analyzer.py # site ophalen + signalen eruit halen
│   ├── scoring.py          # signalen -> score + redenen
│   ├── scraper_utils.py    # netjes ophalen (robots.txt, snelheidsrem)
│   └── storage.py          # CSV lezen/schrijven + ontdubbelen
└── data/                   # uitvoer komt hier
```

## Volgende stap

De logische uitbreiding is een **trigger-monitor**: een dagelijkse check op
Adformatie/Emerce en de vacaturepagina's van bureaus uit je lijst, zodat je hoort
wanneer een bureau een nieuwe klant wint of een producer/fotograaf zoekt — het
juiste moment om aan te kloppen.
