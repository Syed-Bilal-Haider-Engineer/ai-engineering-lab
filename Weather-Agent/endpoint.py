import json
import os
import urllib.parse
import urllib.request


def current_weather(lat, lon):
    query = urllib.parse.urlencode({"lat": lat, "lon": lon})
    request = urllib.request.Request(
        f"{os.environ['URL_WEATHER']}?{query}",
        headers={"X-Api-Key": os.environ["KEY_WEATHER"]},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode())
