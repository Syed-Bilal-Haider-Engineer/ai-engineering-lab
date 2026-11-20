import json
import os

from google import genai

from prompt import SYSTEM_PROMPT
from weather import get_weather


def load_env():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    with open(env_path, encoding="utf-8") as env_file:
        for line in env_file:
            line = line.strip()
            if not line:
                continue
            name, value = line.split("=", 1)
            os.environ[name.strip()] = value.strip().strip('"')


load_env()
client = genai.Client(api_key=os.environ["GEMINI_KEY"])
MODEL = "gemini-2.5-flash"


def call_model(messages):
    contents = []
    system_text = ""
    for message in messages:
        if message["role"] == "system":
            system_text = message["content"]
            continue
        text = message["content"]
        if system_text and not contents:
            text = system_text + "\n\n" + text
        role = "model" if message["role"] == "assistant" else "user"
        contents.append({"role": role, "parts": [{"text": text}]})

    response = client.models.generate_content(model=MODEL, contents=contents)
    return response.text.strip()


def weather_location(text):
    """Return the city only when the model chose the get_weather action."""
    start = text.find("{")
    while start != -1:
        depth = 0
        for index in range(start, len(text)):
            if text[index] == "{":
                depth += 1
            elif text[index] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        action = json.loads(text[start : index + 1])
                    except json.JSONDecodeError:
                        break
                    if isinstance(action, dict) and action.get("action") == "get_weather":
                        return (action.get("action_input") or {}).get("location")
                    break
        start = text.find("{", start + 1)
    return None


def main():
    question = input("Ask: ").strip()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    model_reply = call_model(messages)
    print("\n1. Model:\n", model_reply)

    city = weather_location(model_reply)
    if not city:
        print("\n2. No weather tool. The model answered directly.")
        return

    messages.append(
        {
            "role": "assistant",
            "content": model_reply + "\nObservation:\n" + get_weather(city),
        }
    )
    print("\n2. Weather tool called for:", city)

    messages.append({"role": "user", "content": "Use the Observation and reply with the Final Answer."})
    final_reply = call_model(messages)
    print("\n3. Final:\n", final_reply)


if __name__ == "__main__":
    main()
