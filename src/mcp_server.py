import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import mcp.server.stdio
import mcp.types as types
from mcp.server import Server
from dotenv import load_dotenv

from utils import ensure_dir, list_input_files, load_text, safe_filename, scan_wiki_entities

load_dotenv()

# Initialize MCP Server
server = Server("llm-wiki-mcp")

# Configuration
RAW_DIR = Path(os.getenv("WIKI_RAW_DIR", "data/raw"))
WIKI_DIR = Path(os.getenv("WIKI_OUTPUT_DIR", "data/wiki"))


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """List all available tools for the wiki system."""
    return [
        types.Tool(
            name="inject_raw_content",
            description="Inject markdown or text content into the raw data folder for wiki processing. The content will be ingested and converted into wiki pages.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Filename or title for the raw content (without extension, it will be saved as .md)",
                    },
                    "content": {
                        "type": "string",
                        "description": "The raw text or markdown content to inject for wiki ingestion",
                    },
                },
                "required": ["title", "content"],
            },
        ),
        types.Tool(
            name="list_wiki_pages",
            description="List all markdown pages currently in the wiki knowledge base.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        types.Tool(
            name="read_wiki_page",
            description="Retrieve the full content of a specific wiki page.",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_title": {
                        "type": "string",
                        "description": "The title or name of the wiki page to read (e.g., 'Python', 'Machine Learning')",
                    },
                },
                "required": ["page_title"],
            },
        ),
        types.Tool(
            name="search_wiki",
            description="Search for text patterns across all wiki pages. Returns matching pages and snippets.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (case-insensitive text or regex pattern)",
                    },
                    "use_regex": {
                        "type": "boolean",
                        "description": "If true, query is treated as regex pattern; otherwise as literal text",
                        "default": False,
                    },
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="get_wiki_stats",
            description="Get statistics about the wiki: total pages, entities, and summary of content.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> Any:
    """Process tool calls from MCP clients."""
    if name == "inject_raw_content":
        return await inject_raw_content(arguments["title"], arguments["content"])
    elif name == "list_wiki_pages":
        return await list_wiki_pages()
    elif name == "read_wiki_page":
        return await read_wiki_page(arguments["page_title"])
    elif name == "search_wiki":
        query = arguments.get("query", "")
        use_regex = arguments.get("use_regex", False)
        return await search_wiki(query, use_regex)
    elif name == "get_wiki_stats":
        return await get_wiki_stats()
    else:
        return {"error": f"Unknown tool: {name}"}


async def inject_raw_content(title: str, content: str) -> dict:
    """Inject content into the raw data folder for processing."""
    try:
        ensure_dir(RAW_DIR)
        filename = safe_filename(title)
        file_path = RAW_DIR / filename

        file_path.write_text(content, encoding="utf-8")

        return {
            "status": "success",
            "message": f"Content injected successfully",
            "file": str(file_path),
            "title": title,
            "size": len(content),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def list_wiki_pages() -> dict:
    """List all wiki pages."""
    try:
        ensure_dir(WIKI_DIR)
        pages = []
        for page_file in sorted(WIKI_DIR.glob("*.md")):
            page_title = page_file.stem.replace("-", " ")
            file_size = page_file.stat().st_size
            pages.append(
                {
                    "title": page_title,
                    "filename": page_file.name,
                    "size_bytes": file_size,
                    "last_modified": datetime.fromtimestamp(page_file.stat().st_mtime).isoformat(),
                }
            )

        return {
            "status": "success",
            "total_pages": len(pages),
            "pages": pages,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def read_wiki_page(page_title: str) -> dict:
    """Read the content of a wiki page."""
    try:
        ensure_dir(WIKI_DIR)

        # Try exact match first
        filename = safe_filename(page_title)
        page_path = WIKI_DIR / filename

        # If not found, try case-insensitive search
        if not page_path.exists():
            for f in WIKI_DIR.glob("*.md"):
                if f.stem.lower().replace("-", " ") == page_title.lower():
                    page_path = f
                    break

        if not page_path.exists():
            return {
                "status": "not_found",
                "message": f"Wiki page '{page_title}' not found",
                "available_pages": [p.stem.replace("-", " ") for p in WIKI_DIR.glob("*.md")],
            }

        content = page_path.read_text(encoding="utf-8")
        return {
            "status": "success",
            "title": page_path.stem.replace("-", " "),
            "filename": page_path.name,
            "content": content,
            "size_bytes": len(content),
            "last_modified": datetime.fromtimestamp(page_path.stat().st_mtime).isoformat(),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def search_wiki(query: str, use_regex: bool = False) -> dict:
    """Search for content across all wiki pages."""
    try:
        ensure_dir(WIKI_DIR)
        results = []

        if use_regex:
            try:
                pattern = re.compile(query, re.IGNORECASE)
            except re.error as e:
                return {"status": "error", "message": f"Invalid regex: {e}"}
        else:
            pattern = re.compile(re.escape(query), re.IGNORECASE)

        for page_file in WIKI_DIR.glob("*.md"):
            page_title = page_file.stem.replace("-", " ")
            content = page_file.read_text(encoding="utf-8")

            matches = list(pattern.finditer(content))
            if matches:
                # Extract context snippets around matches
                snippets = []
                for match in matches[:5]:  # Limit to 5 matches per page
                    start = max(0, match.start() - 100)
                    end = min(len(content), match.end() + 100)
                    snippet = content[start:end].strip()
                    snippets.append({
                        "match": match.group(),
                        "snippet": snippet,
                        "position": match.start(),
                    })

                results.append({
                    "page_title": page_title,
                    "filename": page_file.name,
                    "match_count": len(matches),
                    "snippets": snippets,
                })

        return {
            "status": "success",
            "query": query,
            "total_matches": sum(r["match_count"] for r in results),
            "pages_with_matches": len(results),
            "results": results,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def get_wiki_stats() -> dict:
    """Get statistics about the wiki."""
    try:
        ensure_dir(WIKI_DIR)
        ensure_dir(RAW_DIR)

        wiki_pages = list(WIKI_DIR.glob("*.md"))
        raw_files = list_input_files(RAW_DIR)
        processed_files = list((RAW_DIR / "processed").glob("*")) if (RAW_DIR / "processed").exists() else []

        total_wiki_size = sum(f.stat().st_size for f in wiki_pages)
        total_raw_size = sum(f.stat().st_size for f in raw_files)

        return {
            "status": "success",
            "wiki": {
                "total_pages": len(wiki_pages),
                "total_size_bytes": total_wiki_size,
                "entities": scan_wiki_entities(WIKI_DIR),
            },
            "raw_data": {
                "pending_files": len(raw_files),
                "total_size_bytes": total_raw_size,
            },
            "processed_data": {
                "total_processed": len(processed_files),
            },
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def main():
    """Run the MCP server."""
    async with mcp.server.stdio.stdio_server() as streams:
        await server.run(streams[0], streams[1], None)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
