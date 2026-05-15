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

    prompt = f"""{past_context}Generate 10 Instagram carousel caption hooks for niche: Mindset/Stoicism.

Rules:
- Under 80 characters
- Must work WITHOUT visual context (reader hasn't seen image yet)
- Archetypes: contrarian, curiosity gap, transformation promise
- No clickbait ("You won't believe...")
- No engagement bait ("Like if you agree", "Tag a friend")
- Score each 1-10 on "would a 25yo stop scrolling"

Return JSON only:
{{"hooks": [{{"text": "...", "archetype": "contrarian", "score": 8}}]}}
Sorted by score descending."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system="You are an expert Instagram content strategist. Return only valid JSON, no markdown.",
        messages=[{"role": "user", "content": prompt}]
    )

    result = json.loads(message.content[0].text)
    top3 = result["hooks"][:3]

    out = pathlib.Path("data/current_run")
    out.mkdir(parents=True, exist_ok=True)
    (out / "hooks.json").write_text(json.dumps({"hooks": top3, "selected": top3[0]}, indent=2))
    print(f"Top hook: {top3[0]['text']} (score: {top3[0]['score']})")

if __name__ == "__main__":
    run()
