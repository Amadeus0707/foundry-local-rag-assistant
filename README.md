# Local RAG Assistant — TED University Undergraduate Regulation

A fully offline, retrieval-augmented question-answering assistant built with
**Microsoft Foundry Local**. It answers questions about TED University's
Undergraduate Education and Teaching Regulation, grounding every answer in
the actual regulation text and citing the specific articles it used.

Built for the Microsoft Turkey Summer School program (Foundry Local
RAG track).

## What it does

Ask a question like *"How many courses can I withdraw from in one
semester?"* and the assistant:

1. Finds the most relevant paragraphs of the regulation (combining semantic
   search and keyword search)
2. Gives that text to a local language model as context
3. Answers using only that context — citing the exact articles it relied on
4. If nothing relevant is found, it says so rather than guessing

Everything — embedding, retrieval, and generation — runs on-device through
Foundry Local. No internet connection is required after the models are
downloaded once.

## Architecture

```
question
  -> embedding (qwen3-embedding-0.6b)
  -> confidence threshold (below 0.45 -> refuse, no model call)
  -> hybrid ranking: semantic similarity (60%) + BM25 keyword search (40%)
  -> add neighboring paragraphs from the same article
  -> chat model (phi-3.5-mini) answers using only that context
  -> grounding score: how much of the answer is actually supported by the source
```

The regulation (a 10-page PDF) is split into 160 paragraph-level chunks —
first by `ARTICLE`, then by numbered sub-paragraph — and stored together
with their embeddings in a local SQLite database.

## Project structure

| File | Purpose |
|---|---|
| `rag_core.py` | All RAG logic: search, ranking, grounding, session management |
| `assistant.py` | Command-line interface |
| `app_streamlit.py` | Web interface (`streamlit run app_streamlit.py`) |
| `test_qa.py` | Automated test suite (13 cases), writes `test_results.md` |
| `ingest_en.py` | One-time script: reads the PDF, builds `knowledge_base_en.db` |
| `knowledge_base_en.db` | Pre-built database of 160 chunks + embeddings |
| `TED_UNIVERSITY_REGULATIONS.pdf` | Source document |
| `requirements.txt` | Python dependencies |
| `test_results.md` | Latest automated test run (13/13 passing) |
| `.streamlit/config.toml` | Theme configuration for the web interface |

## Setup

1. Install [Microsoft Foundry Local](https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-local/get-started)
   (Windows required — this project depends on `foundry-local-sdk-winml`).
2. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```
3. The database is already built (`knowledge_base_en.db`). To rebuild it
   from the PDF — for example, if you replace it with a different document —
   run:
   ```
   python ingest_en.py
   ```

## Usage

**Command line:**
```
python assistant.py
```

**Web interface:**
```
streamlit run app_streamlit.py
```
Opens at `http://localhost:8501`.

**Run the automated tests:**
```
python test_qa.py
```

## Notable engineering decisions

- **Chunking granularity.** Splitting by whole `ARTICLE` initially caused a
  single embedding to blend several unrelated sub-topics together — for
  example, one article covers GPA rounding rules, probation thresholds, and
  honor-roll thresholds all at once. Splitting further, by numbered
  paragraph, produced noticeably higher retrieval scores and much more
  precise matches.
- **Language.** The regulation exists in both Turkish and English. Testing
  showed that Phi-3.5-mini reliably answers correctly from the English
  text, but produces inconsistent, sometimes incoherent answers from the
  Turkish legal text — even though retrieval itself worked correctly in
  both cases. The English translation is therefore used as the source
  document.
- **Hybrid search.** Semantic search alone sometimes over-weighted an
  incidental word in a question — for example, the word "Turkish" in a
  question about course credit transfer pulled up the language-of-instruction
  article instead of the actual transfer-procedure article. Adding a BM25
  keyword-matching component, combined 60/40 with semantic similarity,
  fixed this.
- **Grounding score.** Measures what fraction of the meaningful words in a
  generated answer also appear in the retrieved context. It is deliberately
  simple — no extra model call — rather than an LLM-based relevance check:
  an LLM-based verification step was tried and discarded, because the
  small model's own relevance judgments were unreliable (it discarded the
  correct source paragraph in roughly half of the cases tested).
- **Refusal by design.** If no chunk passes the similarity threshold, the
  question is never sent to the chat model. The "I don't have that
  information" response is a property of the retrieval code, not something
  the model has to decide to say.

## Known limitations

- The development machine has an RTX 4070 GPU, but the installed Foundry
  Local catalog does not offer a GPU variant of the models used here, so
  inference runs on CPU. This appears to be a known upstream limitation,
  not a configuration issue.
- Questions whose answer is spread across many non-adjacent paragraphs of a
  long article (for example, a multi-step registration deadline) are
  sometimes answered incompletely, even though neighboring-paragraph
  expansion helps in most cases.
- The model's own in-text citations (e.g., "as stated in Article 15") are
  occasionally wrong. The citation list shown separately by the
  application is generated directly from the retrieved chunks and is
  reliable; the model's prose citations are not.

## Testing

13 automated test cases (`test_qa.py`) check both that answerable questions
are answered correctly and that questions outside the regulation's scope
are correctly refused rather than answered with fabricated information.
Current result: **13/13 passing** — see `test_results.md` for the full
report, including retrieval and grounding scores for every case.
