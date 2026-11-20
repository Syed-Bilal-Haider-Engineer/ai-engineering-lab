import json
import urllib.parse
import urllib.request

from endpoint import current_weather


def get_weather(location):
    # The weather API needs coordinates, so turn the city name into lat/lon first.
    query = urllib.parse.urlencode(
        {"name": location, "count": 1, "language": "en", "format": "json"}
    )
    with urllib.request.urlopen(
        f"https://geocoding-api.open-meteo.com/v1/search?{query}",
        timeout=20,
    ) as response:
        place = json.loads(response.read().decode())["results"][0]

    data = current_weather(place["latitude"], place["longitude"])
    current = data["current"]
    return json.dumps(
        {
            "location": place["name"],
            "temperature_c": current["temperatureC"],
            "condition": current["condition"],
        }
    )
