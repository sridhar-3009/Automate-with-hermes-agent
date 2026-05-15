import anthropic
import json
import pathlib
import os

BANNED_PHRASES = [
    "follow for more", "like if you agree", "tag a friend",
    "comment below", "double tap", "share with", "drop a",
]

def run():
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    hooks_data = json.loads(pathlib.Path("data/current_run/hooks.json").read_text())
    hook = hooks_data["selected"]["text"]

    prompt = f"""Write an Instagram carousel caption for niche: Stoicism/Mindset.

Hook (first line, use exactly as-is): {hook}

Required format — copy this structure exactly:
[hook text]


[3-5 lines of value: what the carousel teaches, conversational tone]

Save this.

#stoicism #mindset #philosophy #discipline #growth

Rules:
- Exactly 5 hashtags, all niche-specific
- No engagement bait whatsoever
- CTA must be exactly "Save this." on its own line
- Blank lines between sections exactly as shown
- Tone: direct, grounded, not preachy

Return JSON only, no markdown:
{{"caption": "full caption text here", "hashtags": ["stoicism", "mindset", "philosophy", "discipline", "growth"]}}"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system="You are an expert Instagram content strategist. Return only valid JSON, no markdown code blocks.",
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    result = json.loads(raw)

    caption = result["caption"]
    flagged = [p for p in BANNED_PHRASES if p.lower() in caption.lower()]
    if flagged:
        print(f"WARNING: Banned phrases detected: {flagged}")

    pathlib.Path("data/current_run/caption.json").write_text(json.dumps(result, indent=2))
    print(f"Caption written. Hook: {hook}")
    print(f"Hashtags: {result['hashtags']}")

if __name__ == "__main__":
    run()
