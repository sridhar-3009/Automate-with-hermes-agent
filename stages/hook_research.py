import anthropic
import json
import pathlib
import os

def run():
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    perf_file = pathlib.Path("data/hook_performance.jsonl")
    past_hooks = []
    if perf_file.exists() and perf_file.stat().st_size > 0:
        past_hooks = [json.loads(l) for l in perf_file.read_text().splitlines() if l.strip()]

    past_context = ""
    if past_hooks:
        top = sorted(past_hooks, key=lambda x: x.get("views", 0), reverse=True)[:10]
        past_context = f"Past top performing hooks:\n{json.dumps(top, indent=2)}\n\n"

    prompt = f"""{past_context}Generate content for a Stoicism/Mindset Instagram carousel. Every run must produce UNIQUE, DIFFERENT content — never repeat previous lessons or phrasing.

Return JSON only:
{{
  "hooks": [{{"text": "...", "archetype": "contrarian", "score": 8}}],
  "slides": ["tip text 1", "tip text 2", "tip text 3", "tip text 4", "tip text 5", "tip text 6", "tip text 7", "tip text 8"]
}}

hooks rules (generate 10):
- Under 80 characters
- Must work WITHOUT visual context
- Archetypes: contrarian, curiosity gap, transformation promise
- No clickbait, no engagement bait
- Score 1-10, sort descending

slides rules (generate exactly 8 tip texts):
- Each tip: 1-2 short lines, max 60 chars per line
- Unique Stoic lesson — pick from Marcus Aurelius, Seneca, Epictetus, Zeno, Cato
- DIFFERENT topic each slide, no repetition
- Direct, punchy, no filler words
- Use \\n to split across two lines if needed"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system="You are an expert Instagram content strategist. Return only valid JSON, no markdown. Generate fresh unique content every single time — never reuse previous lessons.",
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    result = json.loads(raw)

    top3 = result["hooks"][:3]
    slides = result["slides"][:8]

    out = pathlib.Path("data/current_run")
    out.mkdir(parents=True, exist_ok=True)
    (out / "hooks.json").write_text(json.dumps({
        "hooks": top3,
        "selected": top3[0],
        "slides": slides
    }, indent=2))
    print(f"Top hook: {top3[0]['text']} (score: {top3[0]['score']})")
    print(f"Generated {len(slides)} unique slide tips")

if __name__ == "__main__":
    run()
