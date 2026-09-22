from dotenv import load_dotenv
import anthropic

load_dotenv()
client = anthropic.Anthropic()

SYSTEM = "You are a senior data analyst. Answer in at most 2 sentences of plain text."

# Call 1: tell Claude a fact
first = client.messages.create(
    model="claude-sonnet-5",
    max_tokens=300,
    system=SYSTEM,
    messages=[
        {"role": "user", "content": "My company's average order value last month was $42. Please remember that."}
    ],
)
print("Call 1:", first.content[0].text)

# Call 2: a separate request asking about that fact
second = client.messages.create(
    model="claude-sonnet-5",
    max_tokens=300,
    system=SYSTEM,
        messages=[
        {"role": "user", "content": "My company's average order value last month was $42. Please remember that."},
        {"role": "assistant", "content": first.content[0].text},
        {"role": "user", "content": "What was my average order value last month?"}
    ],
)
print("Call 2:", second.content[0].text)
print("Call 2 input tokens:", second.usage.input_tokens)