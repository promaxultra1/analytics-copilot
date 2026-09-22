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

MAX_ROWS = 50

def run_sql(query):
    """Run a query read-only. Returns (text, is_error)."""
    try:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        try:
            cur = conn.execute(query)
            if cur.description is None:
                return "Query returned no result set.", True
            columns = [d[0] for d in cur.description]
            rows = cur.fetchmany(MAX_ROWS + 1)
        finally:
            conn.close()
    except sqlite3.Error as e:
        return f"SQL error: {e}", True

    truncated = len(rows) > MAX_ROWS
    rows = rows[:MAX_ROWS]
    lines = [" | ".join(columns)]
    for row in rows:
        lines.append(" | ".join(str(value) for value in row))
    if truncated:
        lines.append(f"(Truncated to {MAX_ROWS} rows. Aggregate or add a LIMIT.)")
    return "\n".join(lines), False

MAX_STEPS = 10

def ask(question):
    messages = [{"role": "user", "content": question}]

    for step in range(1, MAX_STEPS + 1):
        response = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=1000,
            system=system_prompt,
            tools=tools,
            messages=messages,
        )
        print(f"\n--- Call {step}: stop_reason={response.stop_reason}, "
              f"input tokens={response.usage.input_tokens}")

        messages.append({"role": "assistant", "content": response.content})

        # Claude is done (or got cut off): return its text
        if response.stop_reason != "tool_use":
            if response.stop_reason == "max_tokens":
                print("WARNING: answer was cut off by max_tokens")
            return "".join(b.text for b in response.content if b.type == "text")

        # Otherwise, run every requested query and send the results back
        tool_results = []
        for block in response.content:
            if block.type == "text":
                print("Claude:", block.text)
            elif block.type == "tool_use":
                print("Running:", block.input["query"])
                result, is_error = run_sql(block.input["query"])
                print(result)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                    "is_error": is_error,
                })
        messages.append({"role": "user", "content": tool_results})

    return "Stopped: hit the step limit without a final answer."


# print(ask("Which genre earns the most revenue, and who is the biggest customer within that genre?"))

print(run_sql("DELETE FROM Customer"))
print(run_sql("SELECT * FROM Customers"))   # wrong table name
print(run_sql("SELECT * FROM Track"))       # 3,503 rows