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

def run_sql(query):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(query)
    columns = [d[0] for d in cur.description]
    rows = cur.fetchall()
    conn.close()
    lines = [" | ".join(columns)]
    for row in rows:
        lines.append(" | ".join(str(value) for value in row))
    return "\n".join(lines)

messages = [{"role": "user", "content": "Which 5 countries spend the most?"}]

# Call 1: Claude asks for a query
response = client.messages.create(
    model="claude-sonnet-5",
    max_tokens=1000,
    system=system_prompt,
    tools=tools,
    messages=messages,
)
print("Call 1 stop_reason:", response.stop_reason)

# Save Claude's turn (including the tool request) in the history
messages.append({"role": "assistant", "content": response.content})

# Run each requested query and collect the results
tool_results = []
for block in response.content:
    if block.type == "tool_use":
        print("Running:", block.input["query"])
        result = run_sql(block.input["query"])
        print(result)
        tool_results.append({
            "type": "tool_result",
            "tool_use_id": block.id,
            "content": result,
        })

# Send the results back as the next "user" message
messages.append({"role": "user", "content": tool_results})

# Call 2: Claude sees the rows and answers
final = client.messages.create(
    model="claude-sonnet-5",
    max_tokens=1000,
    system=system_prompt,
    tools=tools,
    messages=messages,
)
print()
print("Call 2 stop_reason:", final.stop_reason)
print("Call 2 input tokens:", final.usage.input_tokens)
for block in final.content:
    if block.type == "text":
        print(block.text)