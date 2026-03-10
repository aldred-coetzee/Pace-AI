# withings-mcp

MCP server for Withings body composition and health metrics — weight, body fat, blood pressure.

## Setup

```bash
pip install -e .
```

## Configuration

Copy `.env.example` to `.env` and fill in your Withings API credentials.

## Usage

```bash
withings-mcp  # starts on localhost:8004
```

On first run, use the `authenticate` tool to complete the OAuth2 flow.
