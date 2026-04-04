# ⚡ KalshiBot + Claude Vibe Coding Cheatsheet

The exact commands and prompt tricks you need to interact seamlessly with your KalshiBot infrastructure securely.

## 1. Local Environments & Setup
```bash
# Total Systems Install & Activation
bash kalshi-manager.sh setup

# Master Production Launch (Natively throws the Agent into the background)
bash kalshi-manager.sh launch

# Safe Stop (kills python daemon natively)
bash kalshi-manager.sh stop
```

## 2. 'Vibe Coding' Directly with Claude
Whenever you need to spin up the architecture to write new features, do NOT edit files manually. Boot the CLI native interface mapping the $CLAUDE.md memory safely.

```bash
# Automatically loads `/Kalshi/CLAUDE.md` and initializes your exact environment structure 
bash kalshi-manager.sh vibe
```

## 3. Claude Code Shortcuts
| Command | Action |
|---------|--------|
| `/compact` | Restructures memory window securely while persisting `CLAUDE.md` metadata |
| `/cost` | View exact local token expenditure natively |
| `[Tab] Keyboard` | Enable or disable Extended High-Latency AI Thinking logic |
| `/bug` | Natively captures context traces to log crashes |

## 4. Scaffold New Quantitative Trades
Bypassing the heavy Ollama LLM requires specific pure algorithmic logic. 

```bash
# Will inherently create 'src/strategies/sports_arb.py' formatted for Kalshi's asyncio loop!
bash kalshi-manager.sh scaffold sports_arb
```

## 5. Live Environment Monitoring 
Once `launch` is executed, tail your JSON ledger and your Dashboard natively from your iPad:
```bash
# Terminal Tailing
tail -f kalshi_trades.jsonlines | jq .

# iPad Streamlit Display Map 
bash kalshi-manager.sh dashboard
```

## 6. MCP Protocol Tricks (Model Context Protocol)
If scaling to Notion or Github databases for context ingestion natively dynamically via Claude Code:
```bash
# Connect Github repositories globally mapping the MCP loop natively:
claude mcp add --transport http github https://api.githubcopilot.com/mcp
```
