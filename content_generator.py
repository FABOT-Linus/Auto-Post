"""
content_generator.py
Sends the article/newsletter text to an LLM using the Social Media Content
Automation Agent prompt, then parses the structured response into a dict
so each platform's content can be posted programmatically.

Uses Groq's free-tier API (OpenAI-compatible), which hosts fast open models
like Llama 3.3 at no cost within generous rate limits.
Get a free API key at: https://console.groq.com/keys
"""

import os
import re
from groq import Groq

SYSTEM_PROMPT = """You are a Social Media Content Automation Agent.

Your task is to analyze the article/feed provided and automatically create platform-specific content for LinkedIn, Instagram, and Reddit.

GENERAL RULES:
- Read and understand the entire article.
- Identify the most important insight, news, trend, or takeaway.
- Maintain factual accuracy.
- Adapt tone, length, and formatting to each platform.
- Never simply copy and paste the same content across platforms.
- Maximize engagement for each platform's audience.

OUTPUT THE FOLLOWING, using EXACTLY these section headers and the ⸻ separator
between sections, with no extra commentary before or after:

LinkedIn:
[Optimized LinkedIn post - 75-200 words, strong hook, key insights, ends with
a question, 3-5 hashtags, uses line breaks]

⸻
Instagram Image Prompt:
[Detailed image generation prompt suitable for DALL-E, Midjourney, Flux, or
Stable Diffusion]

Instagram Caption:
[50-150 word caption, natural emojis, a call-to-action, 10-20 hashtags]

⸻
Reddit Title:
[Short attention-grabbing title]

Reddit Post:
[1-3 sentence opening post - do NOT summarize the whole article, leave room
for discussion, encourage comments naturally]

⸻
Reddit First Comment:
[Expanded, comment-friendly summary of the article. Bullet points where
appropriate, conversational, no marketing language. This will be posted as
the first comment under the Reddit post.]
"""


def generate_social_content(article_text: str, model: str = "llama-3.3-70b-versatile") -> str:
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    completion = client.chat.completions.create(
        model=model,
        max_tokens=2000,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"ARTICLE:\n{article_text}"},
        ],
    )
    return completion.choices[0].message.content


def parse_content(raw_text: str) -> dict:
    """Splits Claude's structured response into a dict keyed by platform."""

    def grab(pattern, text, flags=re.DOTALL):
        m = re.search(pattern, text, flags)
        return m.group(1).strip() if m else ""

    linkedin = grab(r"LinkedIn:\s*(.*?)\s*⸻", raw_text)
    ig_image_prompt = grab(r"Instagram Image Prompt:\s*(.*?)\s*Instagram Caption:", raw_text)
    ig_caption = grab(r"Instagram Caption:\s*(.*?)\s*⸻", raw_text)
    reddit_title = grab(r"Reddit Title:\s*(.*?)\s*Reddit Post:", raw_text)
    reddit_post = grab(r"Reddit Post:\s*(.*?)\s*⸻", raw_text)
    reddit_comment = grab(r"Reddit First Comment:\s*(.*)", raw_text)

    return {
        "linkedin": linkedin,
        "instagram_image_prompt": ig_image_prompt,
        "instagram_caption": ig_caption,
        "reddit_title": reddit_title,
        "reddit_post": reddit_post,
        "reddit_comment": reddit_comment,
    }


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    sample = "OpenAI released a new model today that..."
    raw = generate_social_content(sample)
    print(raw)
    print("\n\nPARSED:\n", parse_content(raw))
