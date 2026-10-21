import requests


def get_weather_data_by_city(city: str) -> dict:
    """
    Get the current weather for a given city using the OpenWeatherMap API.

    Returns:
        dict: A dictionary containing the weather information for the specified city with the following keys:
            - METEO: str, a description of the current weather (e.g., 'beau', 'couvert', 'pluie givrante', 'pluie', 'chute de neige', 'autre').
            - ETAT ROUTE: str, a description of the current road conditions (e.g., 'sèche', 'humide', 'route enneigée', 'autre').
            - LUMIERE: str, a description of the current light conditions (e.g., 'aurore / crépuscule', 'jour', 'nuit', 'inconnu').
    Raises:
        ValueError: If the city name is not provided or if the city is not found.
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
            "current": "temperature_2m,snow_depth,snowfall,precipitation,cloud_cover",
            "timezone": "auto",
        },
    ).json()

    data = weather_data["current"]
    time = data["time"][-5:]  # prendre uniquement l'heure sans la date
    time_hour = int(time.split(":")[0])
    snow_depth = data["snow_depth"]
    snowfall = data["snowfall"]
    precipitation = data["precipitation"]
    cloud_cover = data["cloud_cover"]

    # info to return:
    # - METEO: ['beau', 'couvert', 'pluie givrante', 'autre', 'pluie', 'chute de neige', 'grêle']
    if cloud_cover < 30:
        meteo = "beau"
    elif precipitation > 0:
        if snowfall > 0:
            meteo = "chute de neige"
        elif precipitation > 0.5:
            meteo = "pluie givrante"
        else:
            meteo = "pluie"
    elif snowfall > 0:
        meteo = "chute de neige"
    else:
        meteo = "couvert"

    # - ETAT ROUTE: ['sèche', 'verglacée', 'humide', 'autre', 'mouillé', 'route enneigée']
    etat_route = (
        "sèche"
        if precipitation == 0 and snow_depth == 0
        else (
            "route enneigée"
            if snow_depth > 0
            else ("mouillée" if precipitation > 0 else "autre")
        )
    )

    # - LUMIERE: ['aurore / crépuscule', 'jour', 'nuit', 'inconnu']
    lumiere = (
        "aurore / crépuscule"
        if time_hour > 6 and time_hour < 7
        else (
            "jour"
            if time_hour < 19
            else "aurore / crépuscule" if time_hour < 20 else "nuit"
        )
    )

    return {
        "METEO": meteo,
        "ETAT ROUTE": etat_route,
        "LUMIERE": lumiere,
    }


# print(get_weather_by_city("Anaktuvuk Pass, Alaska"))


OVERPASS_HEADERS = {
    "User-Agent": "sosroutier/1.0",
    "Accept": "application/json",
}


def get_road_max_speed(rue, ville):
    """
    Overpass API query to get the maximum speed of a road in a given city.
    -> may not be used because of slow response time
    Returns a dictionary with the road's id, type, maxspeed, forward and backward maxspeed, and center coordinates.
    If no results are found, returns an empty list.
    """
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
