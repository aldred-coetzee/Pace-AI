# notion-mcp

MCP server for reading a Notion running diary database. Caches entries to SQLite and exposes them to the Pace-AI coaching system.

## Setup

1. Create a Notion internal integration at https://www.notion.so/my-integrations
2. Share your running diary database with the integration
3. Copy `.env.example` to `.env` and fill in `NOTION_TOKEN` and `NOTION_DIARY_DATABASE_ID`

## Usage

```bash
pip install -e .
notion-mcp
```

Server starts on `localhost:8005` by default.
