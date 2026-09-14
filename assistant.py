"""
assistant.py - Command-line interface.

All RAG logic lives in rag_core.py; this file only talks to the user:
take a question, ask rag_core, print the answer and diagnostic information.

Usage: python assistant.py
Type 'exit' to quit.
"""

import rag_core


def main():
    session = rag_core.start_session(on_progress=lambda msg: print(msg))
    print("\nSorunu yaz, cikmak icin 'exit' yaz.\n")

    try:
        while True:
            question = input("Soru: ").strip()
            if question.lower() in ("exit", "quit", "q"):
                break
            if not question:
                continue

            result = rag_core.answer_query(session, question)

            # Diagnostic lines - so we can see how each decision was made
            print(f"  (en yuksek semantik skor: {result['top_semantic']:.3f} | esik: {rag_core.MIN_SCORE})")
            if result["picked"]:
                print(f"  (hibrit siralama secti: {', '.join(result['picked'])})")
            if result["context_chunks"]:
                print(f"  (context'e giden: {len(result['context_chunks'])} parca, {result['context_chars']} karakter)")

            print(f"\nCevap: {result['answer']}")

            if result["refused"]:
                print(f"(Kaynak: {result['reason']})\n")
            else:
                print(f"(Kaynak: {', '.join(result['sources'])})")
                print(f"(Kaynak dayanagi: {result['grounding_label']} - {result['grounding']:.2f})\n")
    finally:
        session.unload()
        print("Gorusuruz!")


if __name__ == "__main__":
    main()
