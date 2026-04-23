import argparse
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console

from utils import (
    ensure_dir,
    list_input_files,
    load_text,
    normalize_title,
    page_path_for_title,
    scan_wiki_entities,
    write_markdown,
)
from processor import create_or_update_page, inline_cross_references

console = Console()


def load_system_prompt(prompt_path: Path) -> str:
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8").strip()
    raise FileNotFoundError(f"System prompt file not found: {prompt_path}")


def build_config() -> dict:
    load_dotenv()
    root = Path(os.getcwd())
    return {
        "raw_dir": Path(os.getenv("WIKI_RAW_DIR", root / "data" / "raw")),
        "wiki_dir": Path(os.getenv("WIKI_OUTPUT_DIR", root / "data" / "wiki")),
        "prompt_path": Path(os.getenv("SYSTEM_PROMPT_PATH", root / "schema" / "system_prompt.md")),
        "ollama_model": os.getenv("OLLAMA_MODEL", "llama2"),
    }


def process_raw_file(file_path: Path, raw_dir: Path, wiki_dir: Path, model: str, system_prompt: str, entity_titles: list[str]) -> None:
    raw_text = load_text(file_path)
    title = normalize_title(file_path.stem)
    page_path = page_path_for_title(wiki_dir, title)
    existing_content = page_path.read_text(encoding="utf-8") if page_path.exists() else None
    console.print(f"[yellow]Calling LLM[/yellow] {model} {file_path.name} → {page_path.name}")
    new_page = create_or_update_page(model, system_prompt, title, raw_text, existing_content, entity_titles)
    new_page = inline_cross_references(new_page, title, entity_titles)
    write_markdown(page_path, new_page)
    console.print(f"[green]Created/updated:[/green] {page_path.name}")

    processed_dir = raw_dir / "processed"
    ensure_dir(processed_dir)
    destination = processed_dir / file_path.name
    file_path.replace(destination)
    console.print(f"[blue]Moved processed raw file to:[/blue] {destination}")


def refresh_cross_references(wiki_dir: Path, entity_titles: list[str]) -> None:
    for page_file in wiki_dir.glob("*.md"):
        page_title = page_file.stem.replace("-", " ")
        current_text = page_file.read_text(encoding="utf-8")
        updated_text = inline_cross_references(current_text, page_title, entity_titles)
        if updated_text != current_text:
            write_markdown(page_file, updated_text)
            console.print(f"[cyan]Updated links in:[/cyan] {page_file.name}")


def process_all(raw_dir: Path, wiki_dir: Path, model: str, system_prompt: str) -> None:
    ensure_dir(raw_dir)
    ensure_dir(wiki_dir)
    raw_files = list_input_files(raw_dir)
    if not raw_files:
        console.print("[yellow]No new files found in data/raw. Waiting for input...[/yellow]")
        return

    entity_titles = scan_wiki_entities(wiki_dir)
    for raw_file in raw_files:
        console.print(f"[green]Processing raw file:[/green] {raw_file.name}")
        process_raw_file(raw_file, raw_dir, wiki_dir, model, system_prompt, entity_titles)
        entity_titles = scan_wiki_entities(wiki_dir)

    console.print(f"[green]Processed data[/green] {len(raw_files)} files")
    refresh_cross_references(wiki_dir, entity_titles)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the LLM Wiki ingestion pipeline.")
    parser.add_argument("--watch", action="store_true", help="Continuously watch the raw data folder for new files.")
    parser.add_argument("--interval", type=int, default=12, help="Polling interval in seconds when watching for new files.")
    parser.add_argument("--once", action="store_true", help="Process raw files once and exit.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = build_config()
    system_prompt = load_system_prompt(config["prompt_path"])
    model = config["ollama_model"]

    if args.once:
        process_all(config["raw_dir"], config["wiki_dir"], model, system_prompt)
        return

    console.print("[bold green]Starting LLM Wiki watcher...[/bold green]")
    console.print(f"Watching: {config['raw_dir']}  →  {config['wiki_dir']}")
    while True:
        try:
            process_all(config["raw_dir"], config["wiki_dir"], model, system_prompt)
            time.sleep(args.interval)
        except KeyboardInterrupt:
            console.print("[red]Stopping watcher.[/red]")
            break
        except Exception as exc:
            console.print(f"[red]Error:[/red] {exc}")
            time.sleep(args.interval)


if __name__ == "__main__":
    main()
