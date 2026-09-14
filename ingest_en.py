"""
ingest_en.py

Reads the source PDF (TED_UNIVERSITY_REGULATIONS.pdf), splits it into
paragraph-level chunks (first by ARTICLE, then by numbered paragraph within
each article), generates an embedding for each chunk, and stores the
result in a SQLite database (knowledge_base_en.db) used by the other
scripts in this project.

Usage: python ingest_en.py
"""

import re
import json
import sqlite3
from pypdf import PdfReader
from foundry_local_sdk import Configuration, FoundryLocalManager

PDF_PATH = "TED_UNIVERSITY_REGULATIONS.pdf"
DB_PATH = "knowledge_base_en.db"


def extract_text(pdf_path):
    reader = PdfReader(pdf_path)
    return "\n".join(page.extract_text() for page in reader.pages)


def chunk_by_article(full_text):
    parts = re.split(r"\n(?=ARTICLE \d+\s*[-\u2013\u2014])", full_text)
    return [part.strip() for part in parts if part.strip()]


def split_into_paragraphs(article_text):
    header_match = re.match(r"(ARTICLE \d+\s*[-\u2013\u2014])\s*", article_text)
    if not header_match:
        return [article_text]
    header = header_match.group(1).rstrip("-\u2013\u2014 ").strip()
    body = article_text[header_match.end():]
    pieces = re.split(r"\s(?=\(\d+\)\s)", body)
    pieces = [p.strip() for p in pieces if p.strip()]
    return [f"{header} {p}" for p in pieces]


def chunk_by_paragraph(full_text):
    articles = chunk_by_article(full_text)
    paragraphs = []
    for a in articles:
        paragraphs.extend(split_into_paragraphs(a))
    return paragraphs


def setup_database(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY,
            content TEXT,
            embedding TEXT
        )
    """)
    conn.commit()
    return conn


def main():
    full_text = extract_text(PDF_PATH)
    chunks = chunk_by_paragraph(full_text)
    print(f"{len(chunks)} chunk hazir (Ingilizce, fikra bazinda).\n")

    conn = setup_database(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM documents")
    if cursor.fetchone()[0] > 0:
        cursor.execute("DELETE FROM documents")
        conn.commit()

    config = Configuration(app_name="foundry_local_rag")
    FoundryLocalManager.initialize(config)
    manager = FoundryLocalManager.instance

    embedding_model = manager.catalog.get_model("qwen3-embedding-0.6b")
    embedding_model.load()
    embedding_client = embedding_model.get_embedding_client()

    print("Chunk'lar embedleniyor...")
    response = embedding_client.generate_embeddings(chunks)
    embeddings = [item.embedding for item in response.data]
    print(f"{len(embeddings)} embedding uretildi.\n")

    for content, embedding in zip(chunks, embeddings):
        cursor.execute(
            "INSERT INTO documents (content, embedding) VALUES (?, ?)",
            (content, json.dumps(embedding)),
        )
    conn.commit()
    print(f"{len(chunks)} chunk '{DB_PATH}' dosyasina kaydedildi.")

    embedding_model.unload()
    conn.close()


if __name__ == "__main__":
    main()
