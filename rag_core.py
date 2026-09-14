"""
rag_core.py - Core RAG logic for the project.

This lives in one module because three entry points share the same pipeline:
  - assistant.py      (command-line interface)
  - test_qa.py        (automated tests)
  - app_streamlit.py  (web interface)
Keeping the logic in one place means a change here applies everywhere.

Pipeline:
  question -> embedding -> confidence threshold -> hybrid ranking (semantic + BM25)
           -> add neighboring paragraphs -> pass to chat model as context -> answer
           -> measure how well the answer is grounded in the source text
"""

import re
import json
import math
import sqlite3

from foundry_local_sdk import Configuration, FoundryLocalManager

# ---------- Settings ----------

DB_PATH = "knowledge_base_en.db"
EMBEDDING_ALIAS = "qwen3-embedding-0.6b"
CHAT_ALIAS = "phi-3.5-mini"

MIN_SCORE = 0.45      # calibrated against real test data: irrelevant question scored 0.411, lowest legitimate question scored 0.510
TOP_K = 5             # number of chunks to select (neighbor expansion adds to this)
NEIGHBOR_COUNT = 1    # how many paragraphs to add before/after each matched paragraph
SEMANTIC_WEIGHT = 0.6 # weight of semantic similarity in the hybrid score (remainder goes to BM25)

# Grounding thresholds - measured on real answers:
# clean answers scored 0.64-0.74, an answer containing a fabricated detail scored 0.44, a poor answer scored 0.33
GROUNDING_HIGH = 0.60
GROUNDING_LOW = 0.40

# Optional LLM-based relevance filter for retrieved chunks.
# Disabled by default: in testing, the chat model discarded 3-4 of every 5
# candidate chunks and often removed the correct one while keeping an
# incorrect one. A small model's binary relevance judgments were not
# reliable enough here. Kept for reference; set to True to re-enable.
USE_VERIFICATION = False

SYSTEM_PROMPT_TEMPLATE = """You are a helpful assistant that answers questions about TED University's undergraduate education regulation.
Only use the given context to answer - do not use outside knowledge. The context may contain several related points spread across different parts; read all of them carefully and combine every relevant detail into one complete answer, rather than stopping at the first relevant part you find. If the answer is not present in the context, say "I don't have that information in the provided context" instead of guessing.

Context:
{context}
"""

REFUSAL_TEXT = "I don't have that information in the provided context."


# ---------- Text helpers ----------

STOPWORDS = set(
    "a an the of to in for on at by and or is are be was were this that these those with as "
    "from it its their they you your i my we our not do does can may must shall which who "
    "whom what when where how if then than there here all any each such other same so also "
    "more most some no nor only own too very".split()
)


# Letter-grade and status codes used in this regulation (ARTICLE 21, ARTICLE 22).
# These are short (1-2 letters) and would normally be dropped by the length
# filter below. "I" (Incomplete) is deliberately left out: after lowercasing
# it is indistinguishable from the pronoun "i", which is already a stopword -
# keeping it would make every first-person question ("Can I...") match
# Incomplete-grade paragraphs.
GRADE_CODES = {"aa", "ba", "bb", "cb", "cc", "dc", "dd", "f", "fx", "p", "nc", "r", "w", "ip", "l"}


def tokenize(text):
    """
    Splits text into lowercase, meaningful words (drops very short and very
    common words). Uppercase grade/status codes (F, FX, DD, DC, ...) are kept
    even though they are short, since BM25 would otherwise never be able to
    match a question that mentions a specific grade.
    """
    words = re.findall(r"[a-zA-Z]+", text)
    tokens = []
    for w in words:
        lw = w.lower()
        if lw in STOPWORDS:
            continue
        if len(lw) > 2 or (w.isupper() and lw in GRADE_CODES):
            tokens.append(lw)
    return tokens


def get_article_prefix(chunk_text):
    """Returns the 'ARTICLE 13' part - used to avoid crossing article boundaries when adding neighbors."""
    match = re.match(r"(ARTICLE \d+)", chunk_text)
    return match.group(1) if match else None


def get_source_label(chunk_text):
    """Returns the 'ARTICLE 13 (2)' label - used for displaying the source."""
    match = re.match(r"(ARTICLE \d+\s*\(\d+\))", chunk_text)
    return match.group(1) if match else "unknown source"


# ---------- Database ----------

def load_documents(db_path=DB_PATH):
    """Loads all paragraphs and their embeddings into memory (fast enough for 160 records)."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT content, embedding FROM documents")
    rows = cursor.fetchall()
    conn.close()
    contents = [row[0] for row in rows]
    embeddings = [json.loads(row[1]) for row in rows]
    return contents, embeddings


# ---------- Semantic search ----------

def cosine_similarity(a, b):
    """Cosine similarity between two vectors (1.0 = same direction / very similar)."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0


# ---------- Lexical search (BM25) ----------

def build_bm25_index(contents):
    """Computes the statistics BM25 needs, once."""
    tokenized = [tokenize(c) for c in contents]
    df = {}
    for tokens in tokenized:
        for word in set(tokens):
            df[word] = df.get(word, 0) + 1
    avgdl = sum(len(t) for t in tokenized) / len(tokenized) if tokenized else 0.0
    return {"tokenized": tokenized, "df": df, "avgdl": avgdl, "n": len(contents)}


def bm25_score(index, query_tokens, idx, k1=1.5, b=0.75):
    """BM25 score for a single chunk. Rarer words contribute more to the score."""
    tokens = index["tokenized"][idx]
    if not tokens:
        return 0.0
    tf = {}
    for w in tokens:
        tf[w] = tf.get(w, 0) + 1
    dl = len(tokens)
    score = 0.0
    for word in query_tokens:
        if word not in tf:
            continue
        n_q = index["df"].get(word, 0)
        idf = math.log(1 + (index["n"] - n_q + 0.5) / (n_q + 0.5))
        score += idf * (tf[word] * (k1 + 1)) / (tf[word] + k1 * (1 - b + b * dl / index["avgdl"]))
    return score


def normalize(values):
    """Scales scores into the 0-1 range so two differently-scaled scores can be added together."""
    lo, hi = min(values), max(values)
    if hi - lo < 1e-9:
        return [0.0] * len(values)
    return [(v - lo) / (hi - lo) for v in values]


# ---------- Hybrid ranking ----------

def get_top_indices(query, query_embedding, embeddings, bm25_index,
                    top_k=TOP_K, min_score=MIN_SCORE, semantic_weight=SEMANTIC_WEIGHT):
    """
    Combines semantic and lexical scores and returns the indices of the top_k chunks.

    The threshold check uses the RAW SEMANTIC score (0.45 was calibrated against
    it): semantic similarity decides "should we answer at all", the hybrid score
    decides "which chunks to use". Returns an empty list if nothing passes the
    threshold.
    """
    semantic = [cosine_similarity(query_embedding, emb) for emb in embeddings]

    if max(semantic) < min_score:
        return [], semantic

    query_tokens = tokenize(query)
    lexical = [bm25_score(bm25_index, query_tokens, i) for i in range(len(embeddings))]

    sem_n = normalize(semantic)
    lex_n = normalize(lexical)
    hybrid = [semantic_weight * s + (1 - semantic_weight) * l for s, l in zip(sem_n, lex_n)]

    ranked = sorted(range(len(hybrid)), key=lambda i: hybrid[i], reverse=True)
    return ranked[:top_k], semantic


def expand_with_neighbors(matched_indices, contents, neighbor_count=NEIGHBOR_COUNT):
    """
    Adds the paragraph immediately before/after each matched paragraph - but
    only within the same ARTICLE. This helps multi-paragraph questions (such
    as "by when at the latest") where the answer is spread across neighboring
    paragraphs.
    """
    expanded = set(matched_indices)
    for idx in matched_indices:
        own_article = get_article_prefix(contents[idx])
        for offset in range(-neighbor_count, neighbor_count + 1):
            neighbor_idx = idx + offset
            if 0 <= neighbor_idx < len(contents) and neighbor_idx != idx:
                if get_article_prefix(contents[neighbor_idx]) == own_article:
                    expanded.add(neighbor_idx)
    return sorted(expanded)


# ---------- Grounding: is the answer actually based on the source? ----------

def grounding_score(answer, context_chunks):
    """
    What fraction of the meaningful words in the answer also appear in the
    source text? A low score suggests the model may have added something that
    was not in the context.

    Deterministic and fast - no extra model call involved. (Asking the LLM
    "is this relevant" was tried and was not reliable; this approach is
    simpler and measurable.)
    """
    answer_tokens = set(tokenize(answer))
    if not answer_tokens:
        return 1.0
    context_tokens = set()
    for chunk in context_chunks:
        context_tokens.update(tokenize(chunk))
    return len(answer_tokens & context_tokens) / len(answer_tokens)


def grounding_label(score):
    """Converts the score into a readable label (thresholds calibrated against real answers)."""
    if score >= GROUNDING_HIGH:
        return "high"
    if score >= GROUNDING_LOW:
        return "medium"
    return "low"


# ---------- Verification (disabled - see note above) ----------

VERIFY_PROMPT = """You are checking whether a regulation excerpt is relevant to a question.
Answer with exactly one word: YES or NO.

Question: {question}

Excerpt: {chunk}

Does this excerpt directly help answer the question? Answer YES or NO."""


def verify_relevance(chat_client, question, chunk):
    """Asks the model, one chunk at a time, whether it is relevant. Not currently used."""
    messages = [{"role": "user", "content": VERIFY_PROMPT.format(question=question, chunk=chunk)}]
    result = chat_client.complete_chat(messages)
    return result.choices[0].message.content.strip().upper().startswith("YES")


# ---------- Session: load models once, reuse them ----------

class RagSession:
    """Holds the loaded models, the database contents, and the BM25 index together."""

    def __init__(self, contents, embeddings, bm25_index,
                 embedding_client, chat_client, embedding_model, chat_model):
        self.contents = contents
        self.embeddings = embeddings
        self.bm25_index = bm25_index
        self.embedding_client = embedding_client
        self.chat_client = chat_client
        self._embedding_model = embedding_model
        self._chat_model = chat_model

    def unload(self):
        """Unloads the models from memory."""
        self._embedding_model.unload()
        self._chat_model.unload()


def start_session(db_path=DB_PATH, on_progress=None):
    """
    Reads the database, builds the BM25 index, and loads the Foundry Local models.
    on_progress: optional callback for interfaces that want progress messages.
    """
    def report(message):
        if on_progress:
            on_progress(message)

    report("Veritabani okunuyor...")
    contents, embeddings = load_documents(db_path)
    bm25_index = build_bm25_index(contents)

    report("Foundry Local baslatiliyor...")
    config = Configuration(app_name="foundry_local_rag")
    FoundryLocalManager.initialize(config)
    manager = FoundryLocalManager.instance

    report("Embedding modeli hazirlaniyor...")
    embedding_model = manager.catalog.get_model(EMBEDDING_ALIAS)
    embedding_model.download(lambda p: None)
    embedding_model.load()
    embedding_client = embedding_model.get_embedding_client()

    report("Sohbet modeli hazirlaniyor...")
    chat_model = manager.catalog.get_model(CHAT_ALIAS)
    chat_model.download(lambda p: None)
    chat_model.load()
    chat_client = chat_model.get_chat_client()
    chat_client.settings.temperature = 0.0

    report(f"Hazir - {len(contents)} parca yuklendi.")
    return RagSession(contents, embeddings, bm25_index,
                      embedding_client, chat_client, embedding_model, chat_model)


# ---------- Main function: question -> answer ----------

def answer_query(session, question, top_k=TOP_K):
    """
    Processes a question end to end and returns a dictionary with all
    intermediate information. A dictionary is used because the CLI, the tests,
    and the web interface each need to display different fields (scores,
    sources, grounding, etc.).
    """
    query_response = session.embedding_client.generate_embedding(question)
    query_embedding = query_response.data[0].embedding

    matched_indices, semantic_scores = get_top_indices(
        question, query_embedding, session.embeddings, session.bm25_index, top_k=top_k
    )
    top_semantic = max(semantic_scores) if semantic_scores else 0.0

    # Nothing passed the threshold: refuse without calling the model
    if not matched_indices:
        return {
            "answer": REFUSAL_TEXT,
            "refused": True,
            "reason": f"no source passed the {MIN_SCORE} confidence threshold",
            "top_semantic": top_semantic,
            "picked": [],
            "sources": [],
            "context_chunks": [],
            "context_chars": 0,
            "grounding": None,
            "grounding_label": None,
        }

    picked = [get_source_label(session.contents[i]) for i in matched_indices]

    if USE_VERIFICATION:
        verified = [i for i in matched_indices
                    if verify_relevance(session.chat_client, question, session.contents[i])]
        if not verified:
            return {
                "answer": REFUSAL_TEXT,
                "refused": True,
                "reason": "no excerpt passed the relevance check",
                "top_semantic": top_semantic,
                "picked": picked,
                "sources": [],
                "context_chunks": [],
                "context_chars": 0,
                "grounding": None,
                "grounding_label": None,
            }
    else:
        verified = matched_indices

    expanded_indices = expand_with_neighbors(verified, session.contents)
    context_chunks = [session.contents[i] for i in expanded_indices]
    context = "\n\n".join(context_chunks)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_TEMPLATE.format(context=context)},
        {"role": "user", "content": question},
    ]
    result = session.chat_client.complete_chat(messages)
    answer = result.choices[0].message.content.strip()

    ground = grounding_score(answer, context_chunks)

    return {
        "answer": answer,
        "refused": False,
        "reason": None,
        "top_semantic": top_semantic,
        "picked": picked,
        "sources": list(dict.fromkeys(get_source_label(c) for c in context_chunks)),
        "context_chunks": context_chunks,
        "context_chars": len(context),
        "grounding": ground,
        "grounding_label": grounding_label(ground),
    }
