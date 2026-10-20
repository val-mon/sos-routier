import requests


def get_weather_by_city(city: str) -> dict:
    """
    Get the current weather for a given city using the OpenWeatherMap API.

    Returns:
        dict: A dictionary containing the weather information for the specified city with the following keys:
            - city (str): The name of the city.
            - time (str): The current time in the city (HH:MM format).
            - temperature (float): The current temperature in Celsius.
            - snow_depth (float): The current snow depth in meters.
            - snowfall (float): The current snowfall in meters.
            - precipitation (float): The current precipitation in millimeters.
    """
    # Implementation for fetching weather data from OpenWeatherMap API

    if city is None or city.strip() == "":
        raise ValueError("City name must be provided and cannot be empty.")

    city_data = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={
            "name": city,
            "count": 1,
        },
    ).json()

    if "results" not in city_data or len(city_data["results"]) == 0:
        raise ValueError(f"City '{city}' not found.")

    latitude = city_data["results"][0]["latitude"]
    longitude = city_data["results"][0]["longitude"]

    weather_data = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,snow_depth,snowfall,precipitation",
            "timezone": "auto",
        },
    ).json()

    data = weather_data["current"]
    time = data["time"][-5:]  # prendre uniquement l'heure sans la date
    temperature = data["temperature_2m"]
    snow_depth = data["snow_depth"]
    snowfall = data["snowfall"]
    precipitation = data["precipitation"]

    return {
        "city": city,
        "time": time,
        "temperature": temperature,
        "snow_depth": snow_depth,
        "snowfall": snowfall,
        "precipitation": precipitation,
    }


# print(get_weather_by_city("Anaktuvuk Pass, Alaska"))


OVERPASS_HEADERS = {
    "User-Agent": "sosroutier/1.0",
    "Accept": "application/json",
}


def get_road_max_speed(rue, ville):
    # https://bboxfinder.com/#45.740693,5.861206,47.931066,10.634766
    query = f"""
[out:json][timeout:25][bbox:45.740693,5.861206,47.931066,10.634766];
area["name"="{ville}"]["boundary"="administrative"]["admin_level"="8"]->.ville;
way["highway"]["name"~"{rue}",i](area.ville);
out tags center;
    """
    r = requests.post(
        "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
        data={"data": query},
        headers=OVERPASS_HEADERS,
    )
    r.raise_for_status()

    resultats = []
    for el in r.json()["elements"]:
        t = el["tags"]
        print(
            f"Route: {t.get('name')}, Type: {t.get('highway')}, Maxspeed: {t.get('maxspeed')}"
        )
        print(t)
        resultats.append(
            {
                "id": el["id"],
                "type_route": t.get("highway"),
                "maxspeed": t.get("maxspeed"),
                "forward": t.get("maxspeed:forward"),
                "backward": t.get("maxspeed:backward"),
                "centre": el.get("center"),
            }
        )
    return [] if len(resultats) == 0 else resultats[0]


# print(get_road_max_speed("rue de Lausanne", "Sion"))
