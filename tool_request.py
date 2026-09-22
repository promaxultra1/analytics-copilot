import os
import sqlite3
from dotenv import load_dotenv
from anthropic import Anthropic
import anthropic

load_dotenv()

client = anthropic.Anthropic()

DB_PATH = "data/chinook.db"

def get_schema(db_path):
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    conn.close()
    return "\n\n".join(row[0] for row in rows)

system_prompt = f"""You are a data analyst answering questions about a music store.
Use the run_sql tool to get data. Only write SQLite SELECT queries.

Database schema:
{get_schema(DB_PATH)}"""

tools = [
    {
        "name": "run_sql",
        "description": "Run a read-only SQLite query against the music store database and return the rows. Use this whenever you need data to answer a question.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "A single SQLite SELECT statement.",
                }
            },
            "required": ["query"],
        },
    }
]

response = client.messages.create(
    model="claude-sonnet-5",
    max_tokens=1000,
    system=system_prompt,
    tools=tools,
    messages=[{"role": "user", "content": "Which 5 countries spend the most?"}],
)

print("stop_reason:", response.stop_reason)
print("input tokens:", response.usage.input_tokens)
print()

for block in response.content:
    if block.type == "text":
        print("TEXT:", block.text)
    elif block.type == "tool_use":
        print("TOOL REQUEST:", block.name)
        print("  id:", block.id)
        print("  query:", block.input["query"])