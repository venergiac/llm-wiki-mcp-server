from pathlib import Path
import re
from typing import List


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def list_input_files(raw_dir: Path) -> List[Path]:
    ensure_dir(raw_dir)
    return [path for path in raw_dir.iterdir() if path.is_file() and path.suffix.lower() in {".md", ".txt"}]


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore").strip()


def write_markdown(path: Path, content: str) -> None:
    path.write_text(content.strip() + "\n", encoding="utf-8")


def normalize_title(raw_name: str) -> str:
    raw_name = raw_name.strip()
    raw_name = re.sub(r"\.md$|\.txt$", "", raw_name, flags=re.IGNORECASE)
    raw_name = raw_name.replace("_", " ").replace("-", " ").strip()
    if not raw_name:
        return "Untitled"
    return " ".join(raw_name.split())


def safe_filename(title: str) -> str:
    slug = re.sub(r"[^\w\- ]+", "", title)
    slug = slug.strip().replace(" ", "-")
    if not slug.lower().endswith(".md"):
        slug = f"{slug}.md"
    return slug


def page_path_for_title(wiki_dir: Path, title: str) -> Path:
    ensure_dir(wiki_dir)
    return wiki_dir / safe_filename(title)


def scan_wiki_entities(wiki_dir: Path) -> List[str]:
    ensure_dir(wiki_dir)
    titles = []
    for file_path in wiki_dir.glob("*.md"):
        titles.append(file_path.stem.replace("-", " "))
    return titles
