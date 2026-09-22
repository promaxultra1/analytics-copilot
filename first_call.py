from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-sonnet-5",
    max_tokens=500,
       system="You are a senior data analyst. Answer in at most 3 sentences of plain text. No markdown, headers, or tables.",
    messages=[
        {"role": "user", "content": "What's the difference between average order value and revenue per customer?"}
    ],
)

print(response.content[0].text)
print("---")
print(response.usage)
print(response.stop_reason)