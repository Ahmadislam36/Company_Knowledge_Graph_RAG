"""
Groq (LLM) + fastembed (local embeddings) ka simple wrapper.

Poore project mein LLM aur embeddings ka single entry point.
Baaki files sirf generate_text(), generate_json() aur embed_text()
ko use karti hain — inke signatures pehle jaise hi hain, isliye upar
ki koi file badalne ki zaroorat nahi.

Note: Groq sirf chat/completions (LLM) deta hai, embeddings API nahi
deta. Isliye embeddings ke liye 'fastembed' (local, ONNX-based, koi
API key ya internet call nahi chahiye) use kar rahe hain.
"""

import json
import time

from groq import Groq

from src.config import (
    GROQ_API_KEY,
    GROQ_MODEL_NAME,
    EMBEDDING_MODEL_NAME,
)

_client = None
_embedding_model = None


def _get_client() -> Groq:
    """Groq client create karta hai."""

    global _client

    if _client is None:
        if not GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY nahi mila. "
                ".env file mein GROQ_API_KEY=your_key daalein. "
                "Free key yahan se milti hai: https://console.groq.com/keys"
            )

        _client = Groq(api_key=GROQ_API_KEY)

    return _client


def _get_embedding_model():
    """fastembed ka local embedding model lazily load karta hai (sirf ek dafa)."""

    global _embedding_model

    if _embedding_model is None:
        from fastembed import TextEmbedding

        _embedding_model = TextEmbedding(model_name=EMBEDDING_MODEL_NAME)

    return _embedding_model


def _safe_error_message(error: Exception) -> str:
    """
    Windows console encoding issues se bachne ke liye
    exception ko safe ASCII text mein convert karta hai.
    """
    try:
        return str(error).encode(
            "ascii", "backslashreplace"
        ).decode("ascii")
    except Exception:
        return repr(error)


def generate_text(prompt: str, retries: int = 3) -> str:
    """
    Groq ko prompt bhejta hai aur plain text response return karta hai.
    """

    client = _get_client()
    last_error = None

    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=GROQ_MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
            )

            text = response.choices[0].message.content

            if text:
                return text.strip()

            raise RuntimeError(
                "Groq ne empty response return kiya."
            )

        except Exception as exc:
            last_error = exc

            if attempt < retries - 1:
                time.sleep(2 * (attempt + 1))

    error_message = _safe_error_message(last_error)

    raise RuntimeError(
        f"Groq se response nahi mila: {error_message}"
    )


def generate_json(prompt: str):
    """
    Groq se JSON response leta hai.

    Agar response mein ```json ... ``` ho to
    code fences remove karke JSON parse karta hai.
    """

    raw = generate_text(prompt)

    cleaned = raw.strip()

    # Markdown code fences remove karein
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()

        if lines and lines[0].strip().lower() in (
            "```",
            "```json",
        ):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        cleaned = "\n".join(lines).strip()

    try:
        return json.loads(cleaned)

    except json.JSONDecodeError:
        print(
            "[llm_client] JSON parse fail hui, "
            "is response ko skip kar rahe hain."
        )

        # Console encoding issue se bachne ke liye
        try:
            print(raw[:300])
        except UnicodeEncodeError:
            safe_raw = raw[:300].encode(
                "ascii", "backslashreplace"
            ).decode("ascii")
            print(safe_raw)

        return []


def embed_text(text: str) -> list:
    """
    Ek text ko embedding vector mein convert karta hai (local, fastembed se).
    """

    model = _get_embedding_model()

    embeddings = list(model.embed([text]))

    if not embeddings:
        raise RuntimeError(
            "fastembed ne embedding return nahi ki."
        )

    return embeddings[0].tolist()
