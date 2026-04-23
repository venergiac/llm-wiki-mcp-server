# LLM Wiki MCP Server Guide

## Overview

The MCP (Model Context Protocol) Server for LLM Wiki enables Claude and other AI assistants to interact with your wiki system. It provides tools to inject content and retrieve information from the wiki knowledge base.

## Available Tools

### 1. inject_raw_content
Inject markdown or text content into the raw data folder for wiki processing.

**Parameters:**
- `title` (string, required): Filename or title for the content (e.g., "Python Basics", "Machine Learning Guide")
- `content` (string, required): The raw text or markdown content to ingest

**Example:**
```
Use tool: inject_raw_content
title: "Introduction to Neural Networks"
content: "Neural networks are computational models inspired by biological neural networks..."
```

**Response:**
```json
{
  "status": "success",
  "message": "Content injected successfully",
  "file": "/app/data/raw/introduction-to-neural-networks.md",
  "title": "Introduction to Neural Networks",
  "size": 1024,
  "timestamp": "2026-04-23T19:30:00"
}
```

### 2. list_wiki_pages
List all markdown pages currently in the wiki knowledge base.

**Example:**
```
Use tool: list_wiki_pages
```

**Response:**
```json
{
  "status": "success",
  "total_pages": 5,
  "pages": [
    {
      "title": "Machine Learning",
      "filename": "machine-learning.md",
      "size_bytes": 2048,
      "last_modified": "2026-04-23T19:00:00"
    },
    {
      "title": "Python Basics",
      "filename": "python-basics.md",
      "size_bytes": 1536,
      "last_modified": "2026-04-23T18:45:00"
    }
  ]
}
```

### 3. read_wiki_page
Retrieve the full content of a specific wiki page.

**Parameters:**
- `page_title` (string, required): The title or name of the wiki page (e.g., "Python", "Machine Learning")

**Example:**
```
Use tool: read_wiki_page
page_title: "Machine Learning"
```

**Response:**
```json
{
  "status": "success",
  "title": "Machine Learning",
  "filename": "machine-learning.md",
  "content": "# Machine Learning\n\nMachine learning is a subset of artificial intelligence...",
  "size_bytes": 2048,
  "last_modified": "2026-04-23T19:00:00"
}
```

### 4. search_wiki
Search for text patterns across all wiki pages. Returns matching pages and snippets.

**Parameters:**
- `query` (string, required): Search query (case-insensitive text or regex pattern)
- `use_regex` (boolean, optional): If true, query is treated as regex pattern; otherwise as literal text (default: false)

**Example:**
```
Use tool: search_wiki
query: "neural network"
use_regex: false
```

**Response:**
```json
{
  "status": "success",
  "query": "neural network",
  "total_matches": 3,
  "pages_with_matches": 2,
  "results": [
    {
      "page_title": "Machine Learning",
      "filename": "machine-learning.md",
      "match_count": 2,
      "snippets": [
        {
          "match": "neural network",
          "snippet": "...A neural network is a computational model inspired by biological...",
          "position": 245
        }
      ]
    }
  ]
}
```

### 5. get_wiki_stats
Get statistics about the wiki: total pages, entities, and summary of content.

**Example:**
```
Use tool: get_wiki_stats
```

**Response:**
```json
{
  "status": "success",
  "wiki": {
    "total_pages": 5,
    "total_size_bytes": 8192,
    "entities": ["Machine Learning", "Python", "Neural Networks", "Data Science", "Statistics"]
  },
  "raw_data": {
    "pending_files": 2,
    "total_size_bytes": 1024
  },
  "processed_data": {
    "total_processed": 15
  },
  "timestamp": "2026-04-23T19:30:00"
}
```

## Integration with Claude Desktop

To use this MCP server with Claude Desktop:

1. **Update your Claude Desktop configuration:**
   - For macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - For Windows: `%APPDATA%\Claude\claude_desktop_config.json`

2. **Add the LLM Wiki server:**
   ```json
   {
     "mcpServers": {
       "llm-wiki": {
         "command": "python",
         "args": ["/path/to/llm_wiki/src/mcp_server.py"],
         "env": {
           "WIKI_RAW_DIR": "/path/to/llm_wiki/data/raw",
           "WIKI_OUTPUT_DIR": "/path/to/llm_wiki/data/wiki"
         }
       }
     }
   }
   ```

3. **Restart Claude Desktop** to enable the LLM Wiki tools.

## Docker Deployment

The MCP server runs as a separate container in the docker-compose setup:

```bash
# Start the entire system including MCP server
docker compose up --build

# Or run just the MCP server
docker compose up mcp-server
```

## Usage Patterns

### Build Knowledge Base
1. Use `inject_raw_content` to add raw documents
2. The wiki processor automatically converts them to structured pages
3. Use `list_wiki_pages` or `search_wiki` to discover content

### Query and Augment
1. Use `read_wiki_page` to get detailed information
2. Use `search_wiki` for pattern matching
3. Use `get_wiki_stats` to understand the knowledge base

### Monitor Wiki State
1. Check `get_wiki_stats` for overall health
2. Monitor `raw_data.pending_files` to see processing queue
3. Track growth with `total_pages` and `total_size_bytes`

## Error Handling

All tools return status codes:
- `"status": "success"` - Operation completed successfully
- `"status": "error"` - An error occurred (check the `message` field)
- `"status": "not_found"` - Resource not found (e.g., wiki page doesn't exist)

Example error response:
```json
{
  "status": "not_found",
  "message": "Wiki page 'Nonexistent' not found",
  "available_pages": ["Machine Learning", "Python Basics"]
}
```

## File Organization

The MCP server interacts with:
- `/app/data/raw/` - Incoming raw documents
- `/app/data/raw/processed/` - Processed raw documents
- `/app/data/wiki/` - Generated wiki pages

## Environment Variables

- `WIKI_RAW_DIR` - Directory for incoming documents (default: `data/raw`)
- `WIKI_OUTPUT_DIR` - Directory for wiki pages (default: `data/wiki`)

## Notes

- All file operations are UTF-8 encoded
- Wiki page titles are case-insensitive during lookup
- Filenames are automatically slugified (spaces to hyphens, lowercase)
- Cross-references between wiki pages are maintained
