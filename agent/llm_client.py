import os
from openai import OpenAI

def _get_keys() -> list[str]:
    """Collect all available OpenRouter keys from environment."""
    keys = []
    # Try numbered keys first (OPEN_ROUTER_KEY_0 through OPEN_ROUTER_KEY_5)
    for i in range(6):
        k = os.environ.get(f"OPEN_ROUTER_KEY_{i}", "").strip()
        if k:
            keys.append(k)
    # Fall back to single key
    if not keys:
        k = os.environ.get("OPEN_ROUTER_KEY", "").strip()
        if k:
            keys.append(k)
    return keys

_keys = _get_keys()
_key_index = 0

def get_client() -> OpenAI:
    """Return an OpenAI-compatible client pointed at OpenRouter."""
    global _keys, _key_index
    if not _keys:
        raise RuntimeError("No OpenRouter API keys found in environment.")
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=_keys[_key_index % len(_keys)],
    )

def call(client: OpenAI, prompt: str, system: str = "", max_tokens: int = 1024,
         model: str = "google/gemini-3-flash-preview") -> str:
    """Single LLM call with automatic key rotation on rate limit."""
    global _keys, _key_index
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    last_error = None
    for attempt in range(len(_keys)):
        try:
            current_key = _keys[_key_index % len(_keys)]
            c = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=current_key)
            response = c.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                messages=messages,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            last_error = e
            err_str = str(e).lower()
            if any(x in err_str for x in ['429', 'rate limit', 'quota', 'insufficient', 'limit exceeded']):
                print(f"[llm_client] Key {_key_index % len(_keys)} hit limit, rotating to next key...")
                _key_index += 1
            else:
                raise

    raise RuntimeError(f"All {len(_keys)} API keys exhausted. Last error: {last_error}")
