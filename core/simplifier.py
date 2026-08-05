"""
simplifier.py
-------------
Takes the entities found by ner_extractor.py and turns them into plain-English
explanations, then builds a full simplified report.

Strategy (2 layers, cheapest/most-reliable first):
1. DICTIONARY LOOKUP (fast, 100% accurate, no AI model needed):
   If the term exists in our medical_dictionary.json, just use that explanation.
   This covers most common terms and is instant.

2. AI FALLBACK (Hugging Face Transformers) for terms NOT in our dictionary:
   We use a small pretrained model to paraphrase/simplify the sentence
   containing the unknown term, so the system doesn't just say "unknown".

This mirrors exactly what your Gantt chart / architecture slide describes:
"Detected Entity -> Lookup/Model -> Simplified Text"
"""

from .ner_extractor import build_nlp, extract_entities, load_dictionary

_dictionary = load_dictionary()
_nlp = build_nlp()

# Lazy-loaded so the dictionary-only path stays fast and doesn't need
# to download a transformer model unless it's actually needed.
_hf_pipeline = None


def _get_hf_pipeline():
    global _hf_pipeline
    if _hf_pipeline is None:
        from transformers import pipeline
        # A small, general-purpose text2text model. Swap this out later for a
        # model fine-tuned on medical text simplification (see your Gantt chart
        # week 7-9 task) once you have training data.
        _hf_pipeline = pipeline("text2text-generation", model="google/flan-t5-small")
    return _hf_pipeline


def lookup_term(term: str):
    """Search all dictionary categories for a term, return explanation or None."""
    term = term.lower().strip()
    for category, terms in _dictionary.items():
        if term in terms:
            return terms[term]
    return None


def ai_simplify(term: str, context_sentence: str):
    """Fallback: ask a language model to explain an unknown medical term simply."""
    pipe = _get_hf_pipeline()
    prompt = (
        f"Explain the medical term '{term}' in one simple sentence "
        f"for a patient with no medical background. Context: {context_sentence}"
    )
    result = pipe(prompt, max_new_tokens=40)
    return result[0]["generated_text"].strip()


def simplify_report(text: str, use_ai_fallback: bool = True):
    """
    Main entry point. Returns a dict:
    {
        "original_text": ...,
        "entities": [ {text, label, explanation, source}, ... ],
        "simplified_summary": "..."
    }
    """
    entities = extract_entities(text, nlp=_nlp)

    enriched = []
    for ent in entities:
        explanation = lookup_term(ent["text"])
        source = "dictionary"

        if explanation is None:
            if use_ai_fallback:
                explanation = ai_simplify(ent["text"], text)
                source = "ai_model"
            else:
                explanation = "No simple explanation available yet for this term."
                source = "not_found"

        enriched.append({
            "text": ent["text"],
            "label": ent["label"],
            "explanation": explanation,
            "source": source,
        })

    summary_lines = [f"- {e['text'].title()} ({e['label']}): {e['explanation']}" for e in enriched]
    simplified_summary = "\n".join(summary_lines) if summary_lines else "No medical terms detected."

    return {
        "original_text": text.strip(),
        "entities": enriched,
        "simplified_summary": simplified_summary,
    }


if __name__ == "__main__":
    sample_report = """
    Patient presents with a history of Hypertension and Diabetes Mellitus.
    Current medications include Metformin and Atorvastatin.
    Lab results: HbA1c: 7.8%, Creatinine: 1.3 mg/dL, LDL: 145 mg/dL.
    Impression: Poorly controlled Diabetes Mellitus with early signs of
    Chronic Kidney Disease.
    """

    # First run WITHOUT the AI fallback so you can see the fast dictionary-only path
    result = simplify_report(sample_report, use_ai_fallback=False)
    print("=== SIMPLIFIED REPORT (dictionary-only) ===")
    print(result["simplified_summary"])