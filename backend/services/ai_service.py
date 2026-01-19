import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def astrology_ai(name, chart_json, lang="en"):

    prompt = f"""
You are a professional Indian astrologer.

User name: {name}

Planet Data:
{chart_json}

Write prediction in {lang} language.

Explain:
- Personality
- Career
- Marriage
- Money
- Health

Storytelling style.
Simple words.
No technical terms.
"""

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}]
    )

    return res.choices[0].message.content
