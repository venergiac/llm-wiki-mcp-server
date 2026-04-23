# Quick Start Guide

## Prerequisites

- Docker and Docker Compose installed
- Ollama with a model pulled (e.g., `ollama pull qwen3` or `ollama pull llama2`)

## Running the LLM Wiki System

### 1. Start the Services

```bash
# Navigate to the project directory
cd llm-wiki-framework

# Build and start all services (wiki processor + MCP server + Ollama)
docker compose up --build
```

This will:
- Build the Python environment
- Start the Ollama LLM engine
- Launch the LLM Wiki watcher (ingests documents)
- Launch the MCP server (enables Claude integration)

### 2. Inject Documents

Add markdown or text files to `data/raw/`:

```bash
# Create a sample document
echo "# Machine Learning Guide
Machine learning is a subset of artificial intelligence..." > data/raw/ml-intro.txt

# The wiki system will automatically:
# 1. Detect the new file
# 2. Process it through the LLM
# 3. Create/update wiki pages in data/wiki/
# 4. Extract cross-references automatically
```

### 3. Using with Claude Desktop

1. Copy the configuration file to your Claude Desktop config:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

2. Update the paths in `claude_desktop_config.json` to match your installation

3. Restart Claude Desktop to enable LLM Wiki tools

4. In Claude, you can now:
   - Inject content: "Add this research paper to the wiki"
   - Query pages: "What does the Machine Learning page say?"
   - Search: "Find all mentions of neural networks"
   - Monitor: "Show me wiki statistics"

### 4. Accessing Wiki Pages

Wiki pages are stored as markdown files in `data/wiki/`:

```bash
# List all wiki pages
ls data/wiki/

# Read a wiki page
cat data/wiki/machine-learning.md
```

## Project Structure

```
llm-wiki-framework/
├── src/
│   ├── main.py              # Watches and processes raw documents
│   ├── processor.py         # LLM-based page creation/merging
│   ├── mcp_server.py        # MCP server for Claude integration
│   └── utils.py             # File I/O and utilities
├── data/
│   ├── raw/                 # Drop documents here
│   │   └── processed/       # Automatically moved here after processing
│   └── wiki/                # Generated wiki pages (markdown)
├── schema/
│   └── system_prompt.md     # LLM instructions for wiki architect
├── docker-compose.yml       # Multi-container orchestration
├── Dockerfile               # Python environment
├── requirements.txt         # Python dependencies
├── claude_desktop_config.json # MCP server configuration
├── MCP_GUIDE.md            # Detailed MCP server documentation
└── README.md               # Project overview
```

## Configuration

### Environment Variables

- `OLLAMA_MODEL`: LLM model to use (default: `qwen3`)
- `OLLAMA_HOST`: Ollama server address (default: `http://ollama:11434`)
- `WIKI_RAW_DIR`: Input directory (default: `/app/data/raw`)
- `WIKI_OUTPUT_DIR`: Output directory (default: `/app/data/wiki`)

### Changing LLM Models

Edit `docker-compose.yml`:

```yaml
environment:
  OLLAMA_MODEL: llama2  # or mistral, neural-chat, etc.
```

Then restart:

```bash
docker compose down
docker compose up --build
```

## Monitoring

### Check System Status

```bash
# View running containers
docker compose ps

# View logs from the wiki processor
docker compose logs llm-wiki -f

# View logs from the MCP server
docker compose logs mcp-server -f

# View logs from Ollama
docker compose logs ollama -f
```

### Wiki Statistics

Use the MCP server's `get_wiki_stats` tool to see:
- Total wiki pages
- Raw documents pending processing
- Processed documents
- All known entities

## Troubleshooting

### "Connection refused" when connecting to Ollama

The Ollama service may not be fully started. Wait 10-15 seconds and retry:

```bash
docker compose logs ollama
```

Ensure the model is pulled locally:

```bash
ollama pull llama2
```

### "No new files found in data/raw"

Drop a markdown or text file into the `data/raw/` directory:

```bash
echo "Test content" > data/raw/test.md
```

The processor checks every 12 seconds (configurable with `--interval` flag).

### Files not being processed

Check if the raw directory permissions are correct:

```bash
chmod -R 777 data/raw/
```

View the processor logs:

```bash
docker compose logs llm-wiki -f
```

## Next Steps

1. **Add domain knowledge**: Inject domain-specific documents to build a specialized wiki
2. **Customize the prompt**: Edit `schema/system_prompt.md` to change wiki architect behavior
3. **Integrate with workflows**: Use the MCP tools in Claude to augment your documents
4. **Monitor growth**: Track wiki expansion with `get_wiki_stats`

## Advanced Usage

### Process Single File Only

```bash
docker compose run llm-wiki python src/main.py --once
```

### Custom Polling Interval

```bash
docker compose run llm-wiki python src/main.py --watch --interval 5
```

### Copy Config for Claude Desktop

For macOS:
```bash
cp claude_desktop_config.json ~/Library/Application\ Support/Claude/
```

For Windows (PowerShell):
```powershell
Copy-Item claude_desktop_config.json $env:APPDATA\Claude\claude_desktop_config.json
```

## Support

For detailed MCP tool documentation, see [MCP_GUIDE.md](MCP_GUIDE.md)
