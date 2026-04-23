import json
import re
from pathlib import Path
from typing import List, Optional

import ollama


def build_prompt(title: str, raw_text: str, existing_page: Optional[str], references: List[str]) -> str:
    prompt = [
        f"You are building or updating a markdown wiki page for the entity: {title}.",
        "Use the raw content exactly as source material and create a clean, human-readable page.",
        "Preserve existing page content when present, and merge any new details without losing previously captured facts.",
        "Include a short summary, clear section headings, and a brief reference section if applicable.",
        "Use markdown links between pages if a referenced topic already exists in the wiki.",
        "Do not invent facts beyond the provided source text.",
        "If the entity already has a page, merge the information into the existing page and avoid duplicate sections.",
        "Produce output as a markdown file only.",
        "---",
        f"RAW TEXT:\n{raw_text}",
    ]

    if existing_page:
        prompt.append("---\nEXISTING PAGE:\n" + existing_page)

    if references:
        prompt.append("---\nKNOWN WIKI ENTITIES:\n" + "\n".join(sorted(references)))

    return "\n".join(prompt)


def create_or_update_page(
    model: str,
    system_prompt: str,
    title: str,
    raw_text: str,
    existing_page: Optional[str],
    references: List[str],
) -> str:
    user_prompt = build_prompt(title, raw_text, existing_page, references)
    response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        options={"temperature": 0.0},
    )
    return response["message"]["content"].strip()


def inline_cross_references(page_text: str, page_title: str, all_titles: List[str]) -> str:
    def replace_match(match: re.Match, target: str) -> str:
        link = f"[{target}]({safe_filename(target)})"
        return link

    modified = page_text
    for title in sorted(all_titles, key=lambda t: -len(t)):
        if title == page_title:
            continue
        pattern = rf"(?<!\[)\b{re.escape(title)}\b(?!\])"
        replacement = f"[{title}]({safe_filename(title)})"
        modified = re.sub(pattern, replacement, modified)
    return modified


def safe_filename(title: str) -> str:
    slug = re.sub(r"[^\w\- ]+", "", title)
    slug = slug.strip().replace(" ", "-")
    if not slug.lower().endswith(".md"):
        slug = f"{slug}.md"
    return slug
