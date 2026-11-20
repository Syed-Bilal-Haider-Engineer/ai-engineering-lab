# Weather agent workflow

This agent answers a question you type. Gemini (`gemini-2.5-flash`) decides whether the question is about weather. Only a weather question calls the weather tool. Every other question is answered by the model alone.

## Files

| File | Role |
| --- | --- |
| `main.py` | Runs the conversation: load keys, call Gemini, decide if a tool is needed, print the result. |
| `prompt.py` | The system instructions. This is the only place the rules live. |
| `weather.py` | The tool `get_weather`. Turns a city name into coordinates, then asks the endpoint for conditions. |
| `endpoint.py` | The HTTP call to the weather API. It does not know about cities or Gemini. |
| `.env` | `GEMINI_KEY`, `KEY_WEATHER`, and `URL_WEATHER`. These stay out of the Python files. |

## What happens when you start the program

`python main.py` does three things before it asks you anything.

1. `load_env()` reads `.env` and puts each `NAME=value` line into `os.environ`.
2. A Gemini client is created with `GEMINI_KEY`.
3. `input("Ask: ")` waits for one question. That string becomes the user message.

The first message list is always:

```text
system: SYSTEM_PROMPT
user:   the question you typed
```

## How a model call is sent

`call_model(messages)` does not send the list exactly as stored. Gemini wants `user` and `model` parts, not `system` and `assistant`.

- The system message is pasted onto the front of the first user message.
- An `assistant` message is sent as role `model`.
- A `user` message stays role `user`.

`client.models.generate_content` returns `response.text`. That text is the model's reply.

## Path A — the question is not about weather

Example: `Tell me one fact about Paris.`

The system prompt says: call `get_weather` only for weather. For a city question that is not about weather, answer directly and do not call a tool.

The model replies in this shape:

```text
Thought: I now know the final answer
Final Answer: ...
```

`weather_location()` looks through that reply for a JSON object whose `action` is `get_weather`. There is none, so the function returns `None`.

`main` prints the model reply and stops. `get_weather` is never called. `endpoint.py` is never called.

## Path B — the question is about weather

Example: `What's the weather in London?`

### Step 1. The model chooses one action

The system prompt requires this format, and only one action at a time:

```text
Thought: ...
Action:
```json
{
  "action": "get_weather",
  "action_input": {"location": "London"}
}
```
```

The model must stop there. It must not invent the Observation. The observation is added by our code.

### Step 2. The code reads the action

`weather_location()` scans the reply for `{ ... }` blocks, including nested braces. It `json.loads` each block. It returns a city only when:

- `action` is exactly `get_weather`
- `action_input.location` is present

Any other JSON is ignored. If the action is not `get_weather`, the tool is not called.

### Step 3. The tool runs

`get_weather("London")` in `weather.py`:

1. Asks the Open-Meteo geocoder for the place name. The weather API needs latitude and longitude, not a city string.
2. Takes the first result (`name`, `latitude`, `longitude`).
3. Calls `current_weather(latitude, longitude)` in `endpoint.py`.

`endpoint.py` builds:

```text
GET {URL_WEATHER}?lat=...&lon=...
Header: X-Api-Key: {KEY_WEATHER}
```

`URL_WEATHER` and `KEY_WEATHER` come from `.env`. The response body is JSON. The useful fields are:

```text
data["current"]["temperatureC"]
data["current"]["condition"]
```

`get_weather` returns those as a JSON string, for example:

```json
{"location": "London", "temperature_c": 8.3, "condition": "Overcast"}
```

### Step 4. The observation is attached

The assistant message is the model's action text plus the tool result:

```text
{model reply}
Observation:
{JSON from get_weather}
```

That matches the rule in the prompt: the Observation is the source of truth, and our program writes it, not the model.

The message list is now:

```text
system:    SYSTEM_PROMPT
user:      What's the weather in London?
assistant: Thought / Action JSON + Observation + tool JSON
user:      Use the Observation and reply with the Final Answer.
```

### Step 5. The model writes the final answer

`call_model` is called again with that full list. The model must end with:

```text
Thought: I now know the final answer
Final Answer: ...
```

The final sentence is allowed to use only the Observation. It should not invent a temperature.

## Why there are two model calls for weather

The first call only decides the action. The model does not have the weather yet.

The second call happens after the tool result is in the conversation. That is the call that produces `Final Answer`.

A non-weather question needs only the first call.

## What each piece is not allowed to do

- The model does not fetch weather. It only names the tool and the city.
- `weather.py` does not talk to Gemini. It only turns a city into a weather string.
- `endpoint.py` does not geocode and does not decide when to run. It only requests one coordinate pair.
- A question that is not about weather must not reach `get_weather`.

## Run it

From `Weather-Agent`:

```powershell
python main.py
```

Type a question at `Ask:`.
