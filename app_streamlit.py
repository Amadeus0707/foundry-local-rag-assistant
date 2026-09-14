"""
app_streamlit.py - Web interface.

All RAG logic lives in rag_core.py; this file only handles display in the
browser.
Usage: streamlit run app_streamlit.py
(Opens in the browser at http://localhost:8501.)
"""

import html

import streamlit as st

import rag_core

st.set_page_config(
    page_title="Yonetmelik Asistani",
    page_icon="§",
    layout="wide",
)

# ---------- Theme ----------
# "dark" or "light". If you change this, also change the base setting in
# .streamlit/config.toml to match (that file styles Streamlit's own
# header/footer bars and the input box).
THEME = "dark"

PALETTES = {
    "dark": {
        "paper": "#171A21",     # background - deep ink navy
        "surface": "#1E222B",   # sidebar, cards
        "ink": "#E8E6E1",       # main text - warm off-white
        "slate": "#98A1AE",     # secondary text, labels
        "rule": "#2E333E",      # thin lines
        "seal": "#C25A6B",      # accent - citation labels, kicker
        "verified": "#6FA88F",  # high traceability
        "caution": "#C9A961",   # medium traceability
    },
    "light": {
        "paper": "#F4F3EF",
        "surface": "#EAE8E2",
        "ink": "#1A1F2E",
        "slate": "#5A6472",
        "rule": "#D6D3CB",
        "seal": "#8B2635",
        "verified": "#2D5F4F",
        "caution": "#8A6D1F",
    },
}

P = PALETTES[THEME]

ROOT_VARS = f"""
<style>
:root {{
  --paper:    {P['paper']};
  --surface:  {P['surface']};
  --ink:      {P['ink']};
  --slate:    {P['slate']};
  --rule:     {P['rule']};
  --seal:     {P['seal']};
  --verified: {P['verified']};
  --caution:  {P['caution']};
}}
"""

# Design: the language of a legal document - the article number is the most
# characteristic element of this domain, so citation labels are the
# interface's signature element.
STYLES = ROOT_VARS + """
@import url('https://fonts.googleapis.com/css2?family=Spectral:ital,wght@0,400;0,600;1,400&family=Source+Sans+3:wght@400;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

.stApp { background: var(--paper); }

/* Sidebar and header/footer bars: config.toml sets the theme, this is a
   safety net. Without it, a system-level dark theme would produce dark
   text on a dark background. */
[data-testid="stSidebar"],
[data-testid="stSidebarContent"] {
  background: var(--surface);
}
[data-testid="stSidebar"] * { color: var(--ink); }
[data-testid="stHeader"] { background: var(--paper); }
[data-testid="stBottomBlockContainer"],
[data-testid="stBottom"] > div { background: var(--paper); }

.stApp, .stApp p, .stApp li, .stApp label, .stApp div {
  font-family: 'Source Sans 3', system-ui, sans-serif;
  color: var(--ink);
}

/* Header block */
.masthead {
  border-bottom: 2px solid var(--ink);
  padding-bottom: 0.6rem;
  margin-bottom: 1.6rem;
}
.masthead h1 {
  font-family: 'Spectral', Georgia, serif;
  font-weight: 600;
  font-size: 2.1rem;
  line-height: 1.15;
  letter-spacing: -0.01em;
  margin: 0 0 0.25rem 0;
  color: var(--ink);
}
.masthead .kicker {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.72rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--seal);
  margin: 0.7rem 0 0 0;
}
.masthead .sub {
  font-size: 0.95rem;
  color: var(--slate);
  margin: 0;
}

/* Question block */
.turn-q {
  font-family: 'Spectral', Georgia, serif;
  font-size: 1.12rem;
  font-weight: 600;
  line-height: 1.45;
  margin: 2.2rem 0 0.9rem 0;
  padding-left: 0.9rem;
  border-left: 3px solid var(--ink);
}

/* Answer text */
.turn-a {
  font-size: 1rem;
  line-height: 1.65;
  margin: 0 0 1rem 0;
}
.turn-a.refused {
  color: var(--slate);
  font-style: italic;
}

/* Signature element: article-citation-style labels */
.cites { margin: 0.2rem 0 0.9rem 0; }
.cites .lead {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.68rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--slate);
  margin-right: 0.5rem;
}
.cite {
  display: inline-block;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.76rem;
  padding: 0.12rem 0.42rem;
  margin: 0.15rem 0.3rem 0.15rem 0;
  border: 1px solid var(--rule);
  border-left: 2px solid var(--seal);
  background: var(--surface);
  color: var(--ink);
  white-space: nowrap;
}
.cite.none {
  border-left-color: var(--slate);
  color: var(--slate);
}

/* Signature element: source-traceability bar */
.ground { display: flex; align-items: center; gap: 0.6rem; margin: 0 0 0.4rem 0; }
.ground .lbl {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.68rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--slate);
  min-width: 12.5rem;
}
.ground .track {
  flex: 1;
  height: 3px;
  background: var(--rule);
  max-width: 16rem;
}
.ground .fill { height: 3px; }
.ground .fill.high   { background: var(--verified); }
.ground .fill.medium { background: var(--caution); }
.ground .fill.low    { background: var(--seal); }
.ground .num {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.76rem;
  color: var(--ink);
}

/* Display of the retrieved paragraphs */
.clause {
  border-left: 2px solid var(--rule);
  padding: 0.35rem 0 0.35rem 0.85rem;
  margin: 0 0 0.9rem 0;
}
.clause .ref {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.72rem;
  color: var(--seal);
  display: block;
  margin-bottom: 0.2rem;
}
.clause .body {
  font-size: 0.88rem;
  line-height: 1.55;
  color: var(--ink);
}

/* Sidebar */
.side-h {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.68rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--slate);
  margin: 1.3rem 0 0.35rem 0;
  padding-bottom: 0.2rem;
  border-bottom: 1px solid var(--rule);
}
.side-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
  padding: 0.18rem 0;
}
.side-row .v {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.78rem;
  color: var(--slate);
}
.side-note {
  font-size: 0.78rem;
  line-height: 1.5;
  color: var(--slate);
  margin-top: 0.4rem;
}
.side-count {
  font-family: 'Spectral', Georgia, serif;
  font-size: 2.6rem;
  font-weight: 600;
  line-height: 1;
  color: var(--ink);
}
.side-count-unit {
  font-size: 0.8rem;
  color: var(--slate);
  margin-left: 0.3rem;
}
</style>
"""

st.markdown(STYLES, unsafe_allow_html=True)


@st.cache_resource(show_spinner=False)
def get_session():
    """Loads the models only once. Streamlit reruns the whole script on every
    interaction, so without this cache the models would reload on every question."""
    return rag_core.start_session()


def render_citations(sources, reason=None):
    if sources:
        chips = "".join(f'<span class="cite">{html.escape(s)}</span>' for s in sources)
        lead = '<span class="lead">Dayanak</span>'
    else:
        chips = f'<span class="cite none">{html.escape(reason or "kaynak yok")}</span>'
        lead = '<span class="lead">Dayanak yok</span>'
    st.markdown(f'<div class="cites">{lead}{chips}</div>', unsafe_allow_html=True)


def render_grounding(score, label):
    pct = max(0, min(100, int(round(score * 100))))
    st.markdown(
        f'<div class="ground">'
        f'<span class="lbl">Kaynaga izlenebilirlik</span>'
        f'<span class="track"><span class="fill {label}" style="display:block;width:{pct}%"></span></span>'
        f'<span class="num">{score:.2f}</span>'
        f"</div>",
        unsafe_allow_html=True,
    )


def render_turn(turn):
    st.markdown(f'<div class="turn-q">{html.escape(turn["question"])}</div>', unsafe_allow_html=True)

    result = turn["result"]
    answer_class = "turn-a refused" if result["refused"] else "turn-a"
    st.markdown(
        f'<div class="{answer_class}">{html.escape(result["answer"])}</div>',
        unsafe_allow_html=True,
    )

    render_citations(result["sources"], result.get("reason"))

    if result["grounding"] is not None:
        render_grounding(result["grounding"], result["grounding_label"])

    if result["context_chunks"]:
        with st.expander(f'Okunan {len(result["context_chunks"])} fikrayi goster'):
            for chunk in result["context_chunks"]:
                ref = rag_core.get_source_label(chunk)
                body = chunk[len(ref):].strip() if chunk.startswith(ref) else chunk
                st.markdown(
                    f'<div class="clause"><span class="ref">{html.escape(ref)}</span>'
                    f'<span class="body">{html.escape(body)}</span></div>',
                    unsafe_allow_html=True,
                )


# ---------- Page ----------

st.markdown(
    '<div class="masthead">'
    "<h1>Yerel Belge Soru-Cevap Asistani</h1>"
    '<p class="sub">Yuklenen belgeye dayanarak soru yanitlar. Tum islem bu bilgisayarda '
    "calisir, internete cikmaz.</p>"
    '<p class="kicker">Yuklenen dosya: TED Universitesi Lisans Egitim-Ogretim Yonetmeligi</p>'
    "</div>",
    unsafe_allow_html=True,
)

with st.spinner("Modeller yukleniyor, ilk acilis biraz surebilir..."):
    session = get_session()

if "history" not in st.session_state:
    st.session_state.history = []

with st.sidebar:
    st.markdown('<div class="side-h">Bilgi tabani</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div><span class="side-count">{len(session.contents)}</span>'
        '<span class="side-count-unit">fikra</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="side-note">40 madde, fikralarina ayrilmis. Her fikra ayri ayri '
        "aranabilir hale getirildi.</p>",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="side-h">Modeller</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="side-row"><span>Arama</span><span class="v">{rag_core.EMBEDDING_ALIAS}</span></div>'
        f'<div class="side-row"><span>Yanit</span><span class="v">{rag_core.CHAT_ALIAS}</span></div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="side-h">Arama ayarlari</div>', unsafe_allow_html=True)
    top_k = st.slider("Kac fikra getirilsin", 1, 10, rag_core.TOP_K)
    st.markdown(
        f'<div class="side-row"><span>Alaka esigi</span><span class="v">{rag_core.MIN_SCORE}</span></div>'
        f'<div class="side-row"><span>Komsu fikra</span><span class="v">+{rag_core.NEIGHBOR_COUNT}</span></div>'
        f'<div class="side-row"><span>Anlam / kelime</span>'
        f'<span class="v">{rag_core.SEMANTIC_WEIGHT:.1f} / {1 - rag_core.SEMANTIC_WEIGHT:.1f}</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="side-note">Esigi gecen fikra bulunamazsa soru modele hic '
        "gonderilmez, sistem dogrudan bilmedigini soyler.</p>",
        unsafe_allow_html=True,
    )

    if st.session_state.history:
        st.markdown('<div class="side-h">Oturum</div>', unsafe_allow_html=True)
        if st.button("Sohbeti temizle"):
            st.session_state.history = []
            st.rerun()

for turn in st.session_state.history:
    render_turn(turn)

question = st.chat_input("Ask a question about the document")

if question:
    with st.spinner("Yonetmelik taraniyor..."):
        result = rag_core.answer_query(session, question, top_k=top_k)
    st.session_state.history.append({"question": question, "result": result})
    st.rerun()
