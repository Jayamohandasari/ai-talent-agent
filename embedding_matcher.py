import os
import re

try:
    import numpy as np
except ImportError:
    np = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


def _make_client():
    if OpenAI is None:
        return None
    if not os.getenv("OPENAI_API_KEY"):
        return None
    try:
        return OpenAI(max_retries=0, timeout=5.0)
    except Exception:
        return None


client = _make_client()


def get_embedding(text):
    global client

    if not client or np is None:
        return None
    try:
        res = client.embeddings.create(model="text-embedding-3-small", input=text)
        return np.array(res.data[0].embedding)
    except Exception:
        client = None
        return None


def cosine_similarity(a, b):
    if np is None or a is None or b is None:
        return 0
    denominator = np.linalg.norm(a) * np.linalg.norm(b)
    if denominator == 0:
        return 0
    return float(np.dot(a, b) / denominator)


def _tokenize(text):
    # Inside a character class [...], `.` is a literal dot, not a wildcard.
    return {
        token.lower()
        for token in re.split(r"[^A-Za-z0-9+#.]+", text or "")
        if token.strip()
    }


def _fallback_semantic_match(candidate, jd_text):
    candidate_text = f"{' '.join(candidate.get('skills', []))} {candidate.get('summary', '')}"
    candidate_tokens = _tokenize(candidate_text)
    jd_tokens = _tokenize(jd_text)
    if not candidate_tokens or not jd_tokens:
        return 0.0
    overlap = len(candidate_tokens & jd_tokens)
    union = len(candidate_tokens | jd_tokens)
    return round((overlap / union) * 100, 2) if union else 0.0


def semantic_match(candidate, jd_text):
    candidate_text = f"{' '.join(candidate.get('skills', []))} {candidate.get('summary', '')}"
    candidate_embedding = get_embedding(candidate_text)
    jd_embedding = get_embedding(jd_text)
    if candidate_embedding is None or jd_embedding is None:
        return _fallback_semantic_match(candidate, jd_text)
    return round(cosine_similarity(candidate_embedding, jd_embedding) * 100, 2)
