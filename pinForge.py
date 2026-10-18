import base64
import io
import json
import os
import re
import requests
from PIL import Image

# Where Ollama lives. Default is your laptop; override with an env var or the app sidebar.
DEFAULT_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
DEFAULT_MODEL = "gemma3"

# How much to generate. "Quick" is faster, "Full" gives more variety.
MODES = {
    "Quick": dict(angles=4, titles=2, overlays=1, keywords=10, descriptions=2),
    "Full":  dict(angles=5, titles=3, overlays=2, keywords=20, descriptions=3),
}

TASKS = {
    "angles": 'Write {n} content angles for promoting this product on Pinterest. Each angle '
              'is a different reason a buyer in the target audience would want THIS product, '
              'based only on the details above. Return ONLY JSON like '
              '{{"angles": [{{"name": "...", "hook": "...", "why_it_works": "..."}}]}}.',
    "pack": 'ANGLE: {angle} - {hook}\n'
            'For this angle only, write {nt} Pin titles, each 50-90 characters, main keyword '
            'first, mentioning the benefit or who it is for. Also write {no} text overlay(s): '
            'headline max 8 words, subtext max 6 words. Return ONLY JSON like '
            '{{"titles": ["..."], "overlays": [{{"headline": "...", "subtext": "..."}}]}}.',
    "keywords": 'List {n} long-tail phrases people type into Pinterest search to find this '
                'product. Return ONLY JSON like {{"keywords": ["...", "..."]}}.',
    "descriptions": 'Write {n} Pinterest descriptions, each 250-400 characters, natural '
                    'keywords, ending with a soft call to action. Return ONLY JSON like '
                    '{{"descriptions": ["...", "..."]}}.',
}


# ---------- Helpers ----------

def prepare_image(file_bytes, max_side=768):
    """Shrink the image, convert to JPEG and return it as base64 text."""
    img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    img.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode()


def parse_json(text):
    """Try a straight parse, then fall back to extracting the {...} block."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.S)
        if match:
            return json.loads(match.group(0))
        raise


def _chat(base_url, model, content, images=None, as_json=True, max_tokens=1200):
    """One call to Ollama. Returns (text, tokens_generated, seconds)."""
    message = {"role": "user", "content": content}
    if images:
        message["images"] = images
    body = {
        "model": model,
        "messages": [message],
        "stream": False,
        "keep_alive": "30m",
        "options": {"temperature": 0.8, "num_ctx": 2048, "num_predict": max_tokens},
    }
    if as_json:
        body["format"] = "json"
    r = requests.post(f"{base_url.rstrip('/')}/api/chat", json=body, timeout=900)
    r.raise_for_status()
    data = r.json()
    return (data["message"]["content"],
            data.get("eval_count", 0),
            data.get("eval_duration", 0) / 1e9)


# ---------- Main generator ----------

def generate_stream(name, details, audience, tone, image_bytes=None, mode="Quick",
                    model=DEFAULT_MODEL, base_url=DEFAULT_URL, retries=1):
    """Yields (section_name, data) as each part finishes, then ("_stats", {...})."""
    counts = MODES[mode]
    stats = {"tokens": 0, "secs": 0.0}

    def ask(prompt, key):
        """Call the model, parse JSON, retry on failure."""
        last_error = None
        for _ in range(retries + 1):
            try:
                text, tok, secs = _chat(base_url, model, prompt)
                parsed = parse_json(text)
                parsed[key]  # make sure the expected key exists
                stats["tokens"] += tok
                stats["secs"] += secs
                return parsed
            except Exception as e:
                last_error = e
        raise RuntimeError(f"Could not generate '{key}': {last_error}")

    # Optional: one vision call, then everything else is text-only.
    if image_bytes:
        text, tok, secs = _chat(
            base_url, model,
            "Describe this product image in 2 short sentences: colours, style, theme, "
            "and any readable text. Plain text only.",
            images=[prepare_image(image_bytes)], as_json=False, max_tokens=150)
        stats["tokens"] += tok
        stats["secs"] += secs
        details = f"{details}\nVisible in the product photo: {text.strip()}"
        yield "look", text.strip()

    base = (
        "You are a Pinterest SEO and content strategist. Pinterest is a visual search "
        "engine, so use natural, searchable keywords.\n\n"
        f"PRODUCT: {name}\nDETAILS: {details}\nAUDIENCE: {audience}\nTONE: {tone}\n"
        "Only talk about topics that appear in the product, details or audience above. "
        "Do not invent prices, discounts or claims.\n\n"
    )

    # 1) Angles first, because everything else is built per angle.
    angles = ask(base + TASKS["angles"].format(n=counts["angles"]), "angles")["angles"]
    angles = [a for a in angles if isinstance(a, dict) and a.get("name")]
    yield "angles", angles

    # 2) One small call per angle, so titles and overlays always match their angle.
    titles, overlays = [], []
    for a in angles:
        pack = ask(base + TASKS["pack"].format(
            angle=a["name"], hook=a.get("hook", ""),
            nt=counts["titles"], no=counts["overlays"]), "titles")
        for t in pack.get("titles", []):
            if isinstance(t, str) and t.strip() and len(t.strip()) <= 100:
                titles.append({"angle": a["name"], "title": t.strip()})
        for o in pack.get("overlays", []):
            if isinstance(o, dict):
                overlays.append({"angle": a["name"],
                                 "headline": o.get("headline", ""),
                                 "subtext": o.get("subtext", "")})
    yield "titles", titles
    yield "overlays", overlays

    # 3) Keywords and descriptions.
    yield "keywords", ask(base + TASKS["keywords"].format(n=counts["keywords"]),
                          "keywords")["keywords"]
    yield "descriptions", ask(base + TASKS["descriptions"].format(n=counts["descriptions"]),
                              "descriptions")["descriptions"]

    secs = stats["secs"]
    yield "_stats", {
        "tokens": stats["tokens"],
        "seconds": round(secs, 1),
        "tokens_per_sec": round(stats["tokens"] / secs, 1) if secs else 0,
        "model": model,
        "mode": mode,
    }


# ---------- Weekly plan (plain Python, no AI call) ----------

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
PIN_STYLES = [
    "Product mockup with big headline",
    "Text-only tip pin",
    "Lifestyle / flat-lay photo",
    "Checklist or how-it-works pin",
    "Progress / goal pin",
]
TIMES = ["12:00 PM", "8:00 PM", "9:00 AM", "6:00 PM"]  # starting guesses, tune with your analytics


def build_plan(result, pins_per_week):
    titles = result.get("titles", [])
    descriptions = result.get("descriptions", [])
    angles = result.get("angles", [])
    overlays = result.get("overlays", [])
    if not (titles and angles):
        return []

    plan = []
    for i in range(pins_per_week):
        angle_name = angles[i % len(angles)]["name"]
        round_no = i // len(angles)
        title_pool = [t for t in titles if t["angle"] == angle_name] or titles
        overlay_pool = [o for o in overlays if o["angle"] == angle_name] or overlays
        overlay = overlay_pool[round_no % len(overlay_pool)] if overlay_pool else {}
        plan.append({
            "day": DAYS[int(i * 7 / pins_per_week)],
            "time": TIMES[i % len(TIMES)],
            "angle": angle_name,
            "pin_style": PIN_STYLES[i % len(PIN_STYLES)],
            "title": title_pool[round_no % len(title_pool)]["title"],
            "overlay_headline": overlay.get("headline", ""),
            "overlay_subtext": overlay.get("subtext", ""),
            "description": descriptions[i % len(descriptions)] if descriptions else "",
        })
    return plan