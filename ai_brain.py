import os
from dotenv import load_dotenv
from sarvamai import SarvamAI

load_dotenv()

api_key = os.getenv("SARVAM_API_SUBSCRIPTION_KEY")

if not api_key:
    raise ValueError(
        "API key not found. Check your .env file."
    )

client = SarvamAI(api_subscription_key=api_key)

messages = [
    {
        "role": "system",
        "content": """
You are a friendly Telugu customer support voice agent.
Speak naturally and politely, like a helpful human.
Understand Telugu and Telugu-English mixed language.
Keep answers short and easy to speak aloud.
Ask a follow-up question when information is missing.
Never invent prices, policies, or business information.
If you do not know an answer, say so honestly.
Reply in the language the customer uses.
"""
    }
]

print("Telugu AI Agent is ready!")
print("Type 'exit' to stop.\n")

while True:
    question = input("Customer: ").strip()

    if question.lower() == "exit":
        print("Agent: ధన్యవాదాలు! మళ్లీ కలుద్దాం.")
        break

    if not question:
        continue

    messages.append({
        "role": "user",
        "content": question
    })

    try:
        response = client.chat.completions(
            model="sarvam-105b-conversations",
            messages=messages,
            max_tokens=180,
            reasoning_effort=None,
        )

        answer = response.choices[0].message.content
        print("\nAI Agent:", answer, "\n")

        messages.append({
            "role": "assistant",
            "content": answer
        })

    except Exception as error:
        print("\nCould not get a response.")
        print("Error:", error)

        messages.pop()