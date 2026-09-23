
from langchain.tools import tool
import os
import sqlite3
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

load_dotenv()  # loads ANTHROPIC_API_KEY from .env

DB_PATH = "data/olist.db"

MAX_ROWS = 50

@tool(parse_docstring=True)

def run_sql(query: str) -> str:
    """
    Results are capped at 50 rows.
    Never write or suggest data-modifying SQL (INSERT, UPDATE, DELETE, DROP, ALTER) for the user.
    If asked to change data, explain that this tool is read-only and suggest they contact their data team.

    Args:
        query: A single SQLite SELECT statement.
    """
    try:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        try:
            cur = conn.execute(query)
            if cur.description is None:
                return "SQL error: Query returned no result set."
            columns = [d[0] for d in cur.description]
            rows = cur.fetchmany(MAX_ROWS + 1)
        finally:
            conn.close()
    except sqlite3.Error as e:
        return f"SQL error: {e}"

    truncated = len(rows) > MAX_ROWS
    rows = rows[:MAX_ROWS]
    lines = [" | ".join(columns)]
    for row in rows:
        lines.append(" | ".join(str(value) for value in row))
    if truncated:
        lines.append(f"(Truncated to {MAX_ROWS} rows. Aggregate or add a LIMIT.)")
    return "\n".join(lines)


def load_schema() -> str:
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    rows = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL"
    ).fetchall()
    conn.close()
    return "\n\n".join(r[0] for r in rows)


SYSTEM_PROMPT = f"""You are a data analyst answering questions about the Olist Brazilian e-commerce marketplace database.
Use the run_sql tool to get data. Only write SQLite SELECT queries.


Database schema:
{load_schema()}"""

model = ChatAnthropic(model="claude-sonnet-5", max_tokens=1000)

agent = create_agent(
    model=model, 
    tools=[run_sql], 
    system_prompt=SYSTEM_PROMPT,
    checkpointer=InMemorySaver()
    )

def ask(question: str, thread_id: str = "default"):
    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 20,
    }

    # How many messages this thread already has, so we only print the new ones
    before = len(agent.get_state(config).values.get("messages", []))

    result = agent.invoke(
        {"messages": [{"role": "user", "content": question}]},
        config=config,
    )

    for msg in result["messages"][before:]:
        msg.pretty_print()
        if msg.type == "ai":
            print("tokens:", msg.usage_metadata,
                  "| stop:", msg.response_metadata.get("stop_reason"))
    return result


if __name__ == "__main__":
    ask("How many unique customers are there?", thread_id="A")
    ask("Which state has the most of them?", thread_id="A")
    ask("Which state has the most of them?", thread_id="B")