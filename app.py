"""
Streamlit CRM dashboard voor bureau-leads.
Lokaal: data/leads.csv  |  Cloud: Supabase (via st.secrets)
Starten: streamlit run app.py
"""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))

from src.website_analyzer import analyze_website
from src.scoring import score_lead
from src.storage import _domain

try:
    from supabase import create_client
    _SUPABASE_LIB = True
except ImportError:
    _SUPABASE_LIB = False

# ─── Constanten ──────────────────────────────────────────────────────────────

DATA_PATH = Path(__file__).parent / "data" / "leads.csv"

STATUSES = ["niet benaderd", "benaderd", "geen interesse", "klant"]

ALL_FIELDS = [
    "score", "review", "name", "website", "city", "email",
    "reasons", "photo_credits", "niche_hits", "uses_stock", "phone",
    "status", "notes",
]

_USE_SUPABASE = _SUPABASE_LIB and "supabase_url" in st.secrets

# ─── Supabase helper ──────────────────────────────────────────────────────────

@st.cache_resource
def _db():
    return create_client(st.secrets["supabase_url"], st.secrets["supabase_key"])

# ─── Data helpers ─────────────────────────────────────────────────────────────

def load_leads() -> pd.DataFrame:
    if _USE_SUPABASE:
        result = _db().table("leads").select("*").order("score", desc=True).execute()
        df = pd.DataFrame(result.data) if result.data else pd.DataFrame(columns=ALL_FIELDS)
        df = df.drop(columns=["id"], errors="ignore")
    else:
        if not DATA_PATH.exists():
            return pd.DataFrame(columns=ALL_FIELDS)
        df = pd.read_csv(DATA_PATH, dtype=str).fillna("")

    for col in ("status", "notes"):
        if col not in df.columns:
            df[col] = ""
    df["score"] = pd.to_numeric(df["score"], errors="coerce").fillna(0).astype(int)
    df["status"] = df["status"].apply(lambda x: x if x in STATUSES else STATUSES[0])
    return df.sort_values("score", ascending=False).reset_index(drop=True)


def persist(df: pd.DataFrame):
    out = df.sort_values("score", ascending=False).copy()
    for col in ALL_FIELDS:
        if col not in out.columns:
            out[col] = ""
    out = out[ALL_FIELDS]

    if _USE_SUPABASE:
        records = out.fillna("").astype(str).to_dict("records")
        # score terug naar int voor de database
        for r in records:
            r["score"] = int(r["score"])
        _db().table("leads").upsert(records, on_conflict="website").execute()
    else:
        DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        out.to_csv(DATA_PATH, index=False)


def tier_icon(score: int) -> str:
    if score >= 70:
        return "🟢"
    if score >= 40:
        return "🟡"
    return "🔴"


def run_analyzer(url: str, name: str) -> tuple:
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url
    existing = st.session_state.df
    if len(existing):
        known = {_domain(w) for w in existing["website"].tolist() if w}
        if _domain(url) in known:
            return False, "Dit bureau staat al in de lijst.", {}
    signals = analyze_website(url)
    score, reasons, needs_review = score_lead(signals)
    lead = {
        "score": score,
        "review": "ja" if needs_review else "",
        "name": name.strip(),
        "website": url,
        "city": "",
        "phone": "",
        "email": signals["emails"][0] if signals["emails"] else "",
        "reasons": "; ".join(reasons),
        "photo_credits": ", ".join(signals.get("photo_credits", [])),
        "niche_hits": ", ".join(dict.fromkeys(
            signals.get("priority_hits", [])
            + signals.get("visual_hits", [])
            + signals["niche_hits"]
        )),
        "uses_stock": ", ".join(signals["used_stock"]),
        "status": STATUSES[0],
        "notes": "",
    }
    return True, f"Score {score} — {'; '.join(reasons[:2])}", lead


# ─── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(page_title="Bureau Leads CRM", layout="wide", page_icon="📋")

if "df" not in st.session_state:
    st.session_state.df = load_leads()

# ─── Sidebar filters ──────────────────────────────────────────────────────────

with st.sidebar:
    st.title("🔍 Filters")
    status_filter = st.multiselect("Status", STATUSES, default=STATUSES)
    niche_kw = st.text_input("Specialiteit zoekwoord", placeholder="food, retail …")
    st.divider()
    if st.button("🔄 Herladen", use_container_width=True):
        st.session_state.df = load_leads()
        st.rerun()
    st.caption("☁️ Supabase" if _USE_SUPABASE else "💾 Lokale CSV")

# ─── Apply filters ────────────────────────────────────────────────────────────

df: pd.DataFrame = st.session_state.df

mask = df["status"].isin(status_filter)
if niche_kw:
    kw = niche_kw.lower()
    mask &= (
        df["niche_hits"].str.lower().str.contains(kw, na=False)
        | df["reasons"].str.lower().str.contains(kw, na=False)
    )

df_view = df[mask].copy()

# ─── Header & metrics ─────────────────────────────────────────────────────────

st.title("📋 Bureau Leads CRM")

if len(df) == 0:
    st.info(
        "Nog geen leads. Voeg een bureau toe via het formulier hieronder, "
        "of draai lokaal: `python main.py --seed data/seed_example.csv`."
    )
else:
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Totaal leads", len(df))
    c2.metric("Niet benaderd", int((df["status"] == "niet benaderd").sum()))
    c3.metric("Benaderd", int((df["status"] == "benaderd").sum()))
    c4.metric("Klant 🎉", int((df["status"] == "klant").sum()))
    c5.metric("Te checken ⚠️", int((df["review"] == "ja").sum()))

st.divider()

# ─── Add new agency ───────────────────────────────────────────────────────────

with st.expander("➕ Nieuw bureau toevoegen via URL"):
    with st.form("nieuw_bureau", clear_on_submit=True):
        col_url, col_name = st.columns([3, 1])
        url_in = col_url.text_input("Website URL *", placeholder="https://bureau.nl")
        name_in = col_name.text_input("Naam (optioneel)")
        submitted = st.form_submit_button("Analyseren & toevoegen", type="primary")

    if submitted:
        if not url_in:
            st.warning("Vul een URL in.")
        else:
            with st.spinner("Website analyseren … (kan 10–30 seconden duren)"):
                ok, msg, lead = run_analyzer(url_in, name_in)
            if ok:
                new_row = pd.DataFrame([lead])
                st.session_state.df = (
                    pd.concat([st.session_state.df, new_row], ignore_index=True)
                    .sort_values("score", ascending=False)
                    .reset_index(drop=True)
                )
                persist(st.session_state.df)
                st.success(f"✅ Toegevoegd! {msg}")
                st.rerun()
            else:
                st.error(f"❌ {msg}")

# ─── Leads table ──────────────────────────────────────────────────────────────

st.subheader(f"Leads — {len(df_view)} resultaten (van {len(df)} totaal)")

if len(df_view) == 0:
    st.warning("Geen leads gevonden met de huidige filters.")
else:
    tbl = df_view.copy()
    tbl.insert(0, "●", tbl["score"].apply(tier_icon))
    tbl["⚠️"] = tbl["review"].apply(lambda x: "⚠️" if x == "ja" else "")

    SHOW = ["●", "⚠️", "score", "name", "website", "city", "email", "niche_hits", "status", "notes"]

    edited = st.data_editor(
        tbl[SHOW],
        column_config={
            "●": st.column_config.TextColumn("", width=38),
            "⚠️": st.column_config.TextColumn("", width=35),
            "score": st.column_config.NumberColumn("Score", width=68),
            "name": st.column_config.TextColumn("Bureau", width=175),
            "website": st.column_config.LinkColumn("Website", width=175),
            "city": st.column_config.TextColumn("Stad", width=95),
            "email": st.column_config.TextColumn("E-mail", width=170),
            "niche_hits": st.column_config.TextColumn("Specialiteit", width=160),
            "status": st.column_config.SelectboxColumn(
                "Status", options=STATUSES, width=155, required=True
            ),
            "notes": st.column_config.TextColumn("Notities", width=260),
        },
        disabled=["●", "⚠️", "score", "name", "website", "city", "email", "niche_hits"],
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        key="tbl",
    )

    if st.button("💾 Wijzigingen opslaan", type="primary"):
        st.session_state.df.loc[df_view.index, "status"] = edited["status"].values
        st.session_state.df.loc[df_view.index, "notes"] = edited["notes"].values
        persist(st.session_state.df)
        st.success("✅ Opgeslagen!")

    # ─── Detail cards ─────────────────────────────────────────────────────────

    st.subheader("Details per bureau")
    for _, row in df_view.iterrows():
        icon = tier_icon(int(row["score"]))
        review_tag = "  ⚠️ *handmatig checken*" if row["review"] == "ja" else ""
        label = f"{icon} **{row['name'] or row['website']}** — score {row['score']}{review_tag}"
        with st.expander(label):
            left, right = st.columns(2)
            with left:
                st.markdown(f"**Website:** [{row['website']}]({row['website']})")
                st.markdown(f"**Stad:** {row['city'] or '—'}")
                st.markdown(f"**E-mail:** {row['email'] or '—'}")
                st.markdown(f"**Specialiteit:** {row['niche_hits'] or '—'}")
                st.markdown(f"**Stockbeeld:** {row['uses_stock'] or 'geen'}")
            with right:
                st.markdown(f"**Redenen:** {row['reasons'] or '—'}")
                st.markdown(f"**Fotocredits:** {row['photo_credits'] or 'geen'}")
                st.markdown(f"**Status:** `{row['status']}`")
                st.markdown(f"**Notities:** {row['notes'] or '*geen notities*'}")
