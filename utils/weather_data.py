# weather_data.py
# Copyright @ISmartDevs
# Channel t.me/TheSmartDev

def get_weather_conditions():
    """Returns a dictionary of weather condition codes and their descriptions"""
    return {
        0: ("Clear sky", "clear sky"),
        1: ("Mainly clear", "mainly clear"),
        2: ("Partly cloudy", "partly cloudy"),
        3: ("Overcast", "overcast"),
        45: ("Fog", "fog"),
        48: ("Depositing rime fog", "depositing rime fog"),
        51: ("Drizzle: Light intensity", "light drizzle"),
        53: ("Drizzle: Moderate intensity", "moderate drizzle"),
        55: ("Drizzle: Dense intensity", "dense drizzle"),
        56: ("Freezing Drizzle: Light intensity", "light freezing drizzle"),
        57: ("Freezing Drizzle: Dense intensity", "dense freezing drizzle"),
        61: ("Rain: Slight intensity", "slight rain"),
        63: ("Rain: Moderate intensity", "moderate rain"),
        65: ("Rain: Heavy intensity", "heavy rain"),
        66: ("Freezing Rain: Light intensity", "light freezing rain"),
        67: ("Freezing Rain: Heavy intensity", "heavy freezing rain"),
        71: ("Snow fall: Slight intensity", "slight snow fall"),
        73: ("Snow fall: Moderate intensity", "moderate snow fall"),
        75: ("Snow fall: Heavy intensity", "heavy snow fall"),
        77: ("Snow grains", "snow grains"),
        80: ("Rain showers: Slight intensity", "slight rain showers"),
        81: ("Rain showers: Moderate intensity", "moderate rain showers"),
        82: ("Rain showers: Violent intensity", "violent rain showers"),
        85: ("Snow showers: Slight intensity", "slight snow showers"),
        86: ("Snow showers: Heavy intensity", "heavy snow showers"),
        95: ("Thunderstorm: Slight or moderate", "slight or moderate thunderstorm"),
        96: ("Thunderstorm with slight hail", "thunderstorm with slight hail"),
        99: ("Thunderstorm with heavy hail", "thunderstorm with heavy hail"),
    }