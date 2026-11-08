"""
Activity metadata and the weather Scorers used by each activity.

All rules, thresholds and key messages are defined here for each activity following the structure:
    - ACTIVITIES_CFG: dictionary containing all information about all activities
        structure:
        ----------
            {activity_name (str) : 
                {
                    id : str
                    icon: str
                    label: str
                    parameters:  {
                                input: str (ex. temperature_celsuis) name found in the database
                                scorer: function (computes score and decides what message to show)
                                }
                
                }
            }
            dict[str, ActivityConfig]

WARNING: the inputs of each variable in the database is hardcoded here, these names should be centralised            
"""

import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypedDict

from src.forecast.activities.activity_scoring import MessageBand, Scorer

INF = math.inf
ScoreFunction = Callable[[float | int | None], tuple[float, str]]


@dataclass(frozen=True)
class Param:
    input: str
    scorer: ScoreFunction


class ActivityConfig(TypedDict):
    id: str
    icon: str
    label: str
    parameters: dict[str, Param]


def _score_driving_wind(value: float | int | None) -> tuple[float, str]:
    if value is None:
        return _DRIVING_WIND(value)
    return _DRIVING_WIND(value, kmh=float(value) * 3.6)


_DRIVING_WIND = Scorer(
    points=((15.0, 1.0), (20.0, 0.8), (25.0, 0.5), (30.0, 0.2), (35.0, 0.0)),
    messages=(
        MessageBand(15.0, "gusts {v:.0f} m/s ({kmh:.0f} km/h)   no significant effect on driving"),
        MessageBand(20.0, "gusts {v:.0f} m/s ({kmh:.0f} km/h)   take care on bridges and open roads"),
        MessageBand(25.0, "gusts {v:.0f} m/s ({kmh:.0f} km/h)   strong gusts, high-sided vehicles at risk"),
        MessageBand(30.0, "gusts {v:.0f} m/s ({kmh:.0f} km/h)   very strong gusts, dangerous for trucks and caravans"),
        MessageBand(INF, "gusts {v:.0f} m/s ({kmh:.0f} km/h)   extreme gusts, avoid driving if possible"),
    ),
    unknown="Gust data unknown",
)

ACTIVITIES_CFG: dict[str, ActivityConfig] = {
    'cycling': {
        "id": 'cycling',
        "icon": '🚴',
        "label": 'Cycling',
        "parameters": {
            'temperature': Param('temperature_celsius', Scorer(
                points=((-5.0, 0.0), (2.0, 0.1), (7.0, 0.4), (10.0, 0.7), (14.0, 1.0), (28.0, 1.0), (33.0, 0.5), (38.0, 0.2)),
                messages=(
                    MessageBand(2.0, '{v:.1f}°C   dangerously cold for cycling, risk of ice'),
                    MessageBand(7.0, '{v:.1f}°C   cold, dress in thermal layers'),
                    MessageBand(10.0, '{v:.1f}°C   cool, arm warmers recommended'),
                    MessageBand(28.0, '{v:.1f}°C   comfortable cycling temperature', inclusive=True),
                    MessageBand(33.0, '{v:.1f}°C   warm, carry extra water', inclusive=True),
                    MessageBand(INF, '{v:.1f}°C   too hot, risk of heat exhaustion'),
                ),
                unknown='Temperature unknown'
            )),
            'wind': Param('wind_speed_m_per_s', Scorer(
                points=((3.4, 1.0), (5.5, 0.8), (8.0, 0.7), (10.8, 0.5), (13.9, 0.2), (14.0, 0.0)),
                messages=(
                    MessageBand(3.4, '{v:.0f} m/s   light breeze or calmer, easy riding'),
                    MessageBand(5.5, '{v:.0f} m/s   gentle breeze, slight resistance on open roads'),
                    MessageBand(8.0, '{v:.0f} m/s   moderate breeze, noticeable resistance on open roads'),
                    MessageBand(10.8, '{v:.0f} m/s   fresh breeze, hard going into the wind'),
                    MessageBand(13.9, '{v:.0f} m/s   strong breeze, very tiring, handling affected'),
                    MessageBand(INF, '{v:.0f} m/s   near gale or stronger, dangerous for cycling'),
                ),
                unknown='Wind unknown'
            )),
            'gust': Param('wind_gust_m_per_s', Scorer(
                points=((11.0, 1.0), (14.0, 0.7), (17.0, 0.4), (21.0, 0.2), (22.0, 0.0)),
                messages=(
                    MessageBand(11.0, '{v:.0f} m/s   light gusts, no concern'),
                    MessageBand(14.0, '{v:.0f} m/s   moderate gusts, gusts may unsettle the bike'),
                    MessageBand(17.0, '{v:.0f} m/s   strong gusts, risky on exposed roads'),
                    MessageBand(21.0, '{v:.0f} m/s   very strong gusts, very risky, avoid exposed roads'),
                    MessageBand(INF, '{v:.0f} m/s   extreme gusts, dangerous, do not cycle'),
                ),
                unknown='Gust unknown'
            )),
            'rain': Param('precipitation_mm', Scorer(
                points=((0.1, 1.0), (1.3, 0.6), (2.5, 0.4), (7.6, 0.2), (8.0, 0.0)),
                messages=(
                    MessageBand(0.1, 'Dry   good grip on roads'),
                    MessageBand(1.3, '{v:.1f} mm   drizzle, damp roads'),
                    MessageBand(2.5, '{v:.1f} mm   light rain, longer braking distances'),
                    MessageBand(7.6, '{v:.1f} mm   moderate rain, wet roads, reduced grip and visibility'),
                    MessageBand(INF, '{v:.1f} mm   heavy rain, unsafe to ride'),
                ),
                unknown='Precipitation unknown'
            )),
            'snow': Param('snow_precipitation_mm', Scorer(
                points=((0.0, 1.0), (0.05, 1.0), (0.12, 0.3), (0.5, 0.1), (1.0, 0.0)),
                messages=(
                    MessageBand(0.05, 'No snowfall'),
                    MessageBand(0.12, '{v:.1f} mm light snow   slippery roads, extreme caution'),
                    MessageBand(0.5, '{v:.1f} mm moderate snow   slippery and poor visibility'),
                    MessageBand(INF, '{v:.1f} mm snow   do not cycle, roads dangerous'),
                ),
                unknown='No snowfall'
            )),
        },
    },
    'running': {
        "id": 'running',
        "icon": '🏃',
        "label": 'Running',
        "parameters": {
            'temperature': Param('temperature_celsius', Scorer(
                points=((-10.0, 0.0), (-5.0, 0.1), (0.0, 0.3), (5.0, 0.6), (8.0, 1.0), (18.0, 1.0), (24.0, 0.7), (30.0, 0.4), (35.0, 0.1)),
                messages=(
                    MessageBand(-5.0, '{v:.0f}°C   extreme cold, risk of hypothermia'),
                    MessageBand(0.0, '{v:.0f}°C   freezing, icy paths likely'),
                    MessageBand(5.0, '{v:.0f}°C   cold, warm up thoroughly'),
                    MessageBand(18.0, '{v:.0f}°C   ideal running temperature'),
                    MessageBand(24.0, '{v:.0f}°C   warm, hydrate well'),
                    MessageBand(30.0, '{v:.0f}°C   hot, reduce your pace and carry water'),
                    MessageBand(INF, '{v:.0f}°C   dangerous heat, avoid running outdoors'),
                ),
                unknown='Temperature unknown'
            )),
            'wind': Param('wind_speed_m_per_s', Scorer(
                points=((3.4, 1.0), (5.5, 1.0), (8.0, 0.8), (10.8, 0.5), (13.9, 0.3), (14.0, 0.1)),
                messages=(
                    MessageBand(3.4, '{v:.0f} m/s    light breeze or calmer: no effect'),
                    MessageBand(5.5, '{v:.0f} m/s    gentle breeze: little effect'),
                    MessageBand(8.0, '{v:.0f} m/s    moderate breeze: noticeable on exposed sections'),
                    MessageBand(10.8, '{v:.0f} m/s    fresh breeze: slows you down'),
                    MessageBand(13.9, '{v:.0f} m/s    strong breeze: hard going'),
                    MessageBand(INF, '{v:.0f} m/s    near gale or stronger: not recommended'),
                ),
                unknown='Wind unknown'
            )),
            'rain': Param('precipitation_mm', Scorer(
                points=((0.1, 1.0), (1.3, 0.7), (2.5, 0.5), (7.6, 0.3), (8.0, 0.1)),
                messages=(
                    MessageBand(0.1, 'Dry: good conditions'),
                    MessageBand(1.3, '{v:.1f} mm/h   drizzle: a light waterproof helps'),
                    MessageBand(2.5, '{v:.1f} mm/h   light rain: wet, slippery paths'),
                    MessageBand(7.6, '{v:.1f} mm/h   moderate rain: poor visibility, slippery'),
                    MessageBand(INF, '{v:.1f} mm/h   heavy rain: not recommended'),
                ),
                unknown='Precipitation unknown'
            )),
        },
    },
    'hiking': {
        "id": 'hiking',
        "icon": '🥾',
        "label": 'Hiking',
        "parameters": {
            'temperature': Param('temperature_celsius', Scorer(
                points=((-15.0, 0.0), (-10.0, 0.1), (0.0, 0.4), (5.0, 0.6), (8.0, 1.0), (22.0, 1.0), (28.0, 0.6), (34.0, 0.2)),
                messages=(
                    MessageBand(-10.0, '{v:.0f}°C   extreme cold, dangerous at altitude'),
                    MessageBand(0.0, '{v:.0f}°C   freezing, pack warm layers (and crampons in the mountains)'),
                    MessageBand(5.0, '{v:.0f}°C   cold, thermal layers essential'),
                    MessageBand(22.0, '{v:.0f}°C   ideal hiking temperature'),
                    MessageBand(28.0, '{v:.0f}°C   warm, carry at least 2 L of water'),
                    MessageBand(INF, '{v:.0f}°C   too hot for strenuous hiking'),
                ),
                unknown='Temperature unknown'
            )),
            'wind': Param('wind_speed_m_per_s', Scorer(
                points=((3.4, 1.0), (5.5, 1.0), (8.0, 1.0), (10.8, 0.7), (13.9, 0.4), (14.0, 0.1)),
                messages=(
                    MessageBand(3.4, '{v:.0f} m/s    light breeze or calmer, comfortable'),
                    MessageBand(5.5, '{v:.0f} m/s    gentle breeze, comfortable'),
                    MessageBand(8.0, '{v:.0f} m/s    moderate breeze, comfortable'),
                    MessageBand(10.8, '{v:.0f} m/s    fresh breeze, breezy on open terrain'),
                    MessageBand(13.9, '{v:.0f} m/s    take care on ridges and exposed terrain'),
                    MessageBand(INF, '{v:.0f} m/s    dangerous on exposed terrain'),
                ),
                unknown='Wind unknown'
            )),
            'gust': Param('wind_gust_m_per_s', Scorer(
                points=((11.0, 1.0), (14.0, 0.8), (17.0, 0.5), (21.0, 0.2), (22.0, 0.0)),
                messages=(
                    MessageBand(11.0, '{v:.0f} m/s   light gusts, no concern'),
                    MessageBand(14.0, '{v:.0f} m/s   moderate gusts, gusty on ridges'),
                    MessageBand(17.0, '{v:.0f} m/s   strong gusts, take care on ridges'),
                    MessageBand(21.0, '{v:.0f} m/s   very strong gusts, dangerous on exposed terrain'),
                    MessageBand(INF, '{v:.0f} m/s   do not hike on ridges'),
                ),
                unknown='Gust unknown'
            )),
            'rain': Param('precipitation_mm', Scorer(
                points=((0.1, 1.0), (1.3, 0.7), (2.5, 0.5), (7.6, 0.3), (8.0, 0.1)),
                messages=(
                    MessageBand(0.1, 'Dry: good trail conditions'),
                    MessageBand(1.3, '{v:.1f} mm/h   drizzle: trails getting damp'),
                    MessageBand(2.5, '{v:.1f} mm/h   light rain: slippery trails'),
                    MessageBand(7.6, '{v:.1f} mm/h   moderate rain: slippery trails, reduced visibility'),
                    MessageBand(INF, '{v:.1f} mm/h   heavy rain: avoid exposed trails'),
                ),
                unknown='Precipitation unknown'
            )),
            'snow': Param('snow_precipitation_mm', Scorer(
                points=((0.0, 1.0), (0.05, 1.0), (0.12, 0.5), (0.5, 0.2), (1.0, 0.0)),
                messages=(
                    MessageBand(0.05, 'No snowfall'),
                    MessageBand(0.2, '{v:.1f} mm/h snow (water eq.)   light snow: paths may be icy'),
                    MessageBand(0.8, '{v:.1f} mm/h snow (water eq.)   moderate snow: paths treacherous'),
                    MessageBand(INF, '{v:.1f} mm/h snow (water eq.)   heavy snow: do not hike'),
                ),
                unknown='No snowfall'
            )),
        },
    },
    'picnic': {
        "id": 'picnic',
        "icon": '🧺',
        "label": 'Picnic',
        "parameters": {
            'temperature': Param('temperature_celsius', Scorer(
                points=((0.0, 0.0), (5.0, 0.15), (10.0, 0.45), (13.0, 0.65), (18.0, 0.9), (22.0, 1.0), (26.0, 1.0), (30.0, 0.7), (34.0, 0.35), (38.0, 0.1)),
                messages=(
                    MessageBand(5.0, '{v:.0f}°C   too cold for a comfortable picnic'),
                    MessageBand(10.0, '{v:.0f}°C   chilly, bring warm clothes and a blanket'),
                    MessageBand(15.0, '{v:.0f}°C   cool but pleasant in sunshine'),
                    MessageBand(26.0, '{v:.0f}°C   ideal temperature for a picnic'),
                    MessageBand(30.0, '{v:.0f}°C   warm, find some shade'),
                    MessageBand(34.0, '{v:.0f}°C   hot, seek shade and stay hydrated'),
                    MessageBand(INF, '{v:.0f}°C   too hot for a comfortable picnic'),
                ),
                unknown='Temperature unknown'
            )),
            'wind': Param('wind_speed_m_per_s', Scorer(
                points=((3.4, 1.0), (5.5, 0.8), (8.0, 0.5), (10.8, 0.2), (13.9, 0.0), (14.0, 0.0)),
                messages=(
                    MessageBand(3.4, '{v:.0f} m/s    light breeze or calmer: ideal'),
                    MessageBand(5.5, '{v:.0f} m/s    gentle breeze: pleasant, light items may move'),
                    MessageBand(8.0, '{v:.0f} m/s    moderate breeze: napkins and light items will blow away'),
                    MessageBand(10.8, '{v:.0f} m/s    fresh breeze: uncomfortable outdoors'),
                    MessageBand(13.9, '{v:.0f} m/s    strong breeze: too windy'),
                    MessageBand(INF, '{v:.0f} m/s    near gale or stronger: too windy'),
                ),
                unknown='Wind unknown'
            )),
            'rain': Param('precipitation_mm', Scorer(
                points=((0.1, 1.0), (1.3, 0.5), (2.5, 0.2), (7.6, 0.0), (8.0, 0.0)),
                messages=(
                    MessageBand(0.1, 'Dry: ideal'),
                    MessageBand(1.3, '{v:.1f} mm/h   drizzle: bring a shelter'),
                    MessageBand(2.5, '{v:.1f} mm/h   light rain: likely to spoil the picnic'),
                    MessageBand(7.6, '{v:.1f} mm/h   moderate rain: not suitable'),
                    MessageBand(INF, '{v:.1f} mm/h   heavy rain: not suitable'),
                ),
                unknown='Precipitation unknown'
            )),
        },
    },
    'fishing': {
        "id": 'fishing',
        "icon": '🎣',
        "label": 'Fishing',
        "parameters": {
            'wind': Param('wind_speed_m_per_s', Scorer(
                points=((3.4, 1.0), (5.5, 0.8), (8.0, 0.5), (10.8, 0.2), (13.9, 0.0), (14.0, 0.0)),
                messages=(
                    MessageBand(3.4, '{v:.0f} m/s    light breeze or calmer: excellent casting conditions'),
                    MessageBand(5.5, '{v:.0f} m/s    gentle breeze: good casting conditions'),
                    MessageBand(8.0, '{v:.0f} m/s    moderate breeze: casting more difficult'),
                    MessageBand(10.8, '{v:.0f} m/s    fresh breeze: difficult to fish'),
                    MessageBand(13.9, '{v:.0f} m/s    strong breeze: too windy'),
                    MessageBand(INF, '{v:.0f} m/s    near gale or stronger: too windy'),
                ),
                unknown='Wind unknown'
            )),
            'rain': Param('precipitation_mm', Scorer(
                points=((0.1, 0.9), (1.3, 0.9), (2.5, 0.6), (7.6, 0.3), (8.0, 0.1)),
                messages=(
                    MessageBand(0.1, 'Dry: comfortable'),
                    MessageBand(1.3, '{v:.1f} mm/h   drizzle: manageable with waterproofs'),
                    MessageBand(2.5, '{v:.1f} mm/h   light rain: wet but workable'),
                    MessageBand(7.6, '{v:.1f} mm/h   moderate rain: uncomfortable, poor visibility'),
                    MessageBand(INF, '{v:.1f} mm/h   heavy rain: unsafe, seek shelter'),
                ),
                unknown='Precipitation unknown'
            )),
        },
    },
    'photography': {
        "id": 'photography',
        "icon": '📷',
        "label": 'Photography',
        "parameters": {
            'cloud_cover': Param('total_cloud_cover', Scorer(
                points=((0.0, 0.6), (15.0, 0.7), (30.0, 0.9), (55.0, 1.0), (80.0, 0.7), (90.0, 0.5), (100.0, 0.3)),
                messages=(
                    MessageBand(15.0, '{v:.0f}% cloud   clear sky, harsh direct light at midday'),
                    MessageBand(40.0, '{v:.0f}% cloud   light cloud, soft even light'),
                    MessageBand(70.0, '{v:.0f}% cloud   overcast, ideal diffused light for portraits'),
                    MessageBand(90.0, '{v:.0f}% cloud   heavy cloud, may be too dark'),
                    MessageBand(INF, '{v:.0f}% cloud   dense overcast, very flat light'),
                ),
                unknown='Cloud cover unknown'
            )),
            'rain': Param('precipitation_mm', Scorer(
                points=((0.1, 1.0), (1.3, 0.6), (2.5, 0.3), (7.6, 0.1), (8.0, 0.0)),
                messages=(
                    MessageBand(0.1, 'Dry: equipment safe'),
                    MessageBand(1.3, '{v:.1f} mm/h   drizzle: protect your equipment'),
                    MessageBand(2.5, '{v:.1f} mm/h   light rain: risk to camera equipment'),
                    MessageBand(7.6, '{v:.1f} mm/h   moderate rain: do not expose your camera'),
                    MessageBand(INF, '{v:.1f} mm/h   heavy rain: do not expose your camera'),
                ),
                unknown='Precipitation unknown'
            )),
        },
    },
    'stargazing': {
        "id": 'stargazing',
        "icon": '📷',
        "label": 'Stargazing',
        "parameters": {
            'cloud_cover': Param('total_cloud_cover', Scorer(
                points=((0.0, 1.0), (10.0, 0.9), (25.0, 0.7), (50.0, 0.4), (75.0, 0.1), (90.0, 0.0)),
                messages=(
                    MessageBand(10.0, '{v:.0f}% cloud   near clear sky, excellent visibility'),
                    MessageBand(25.0, '{v:.0f}% cloud   mostly clear, good stargazing'),
                    MessageBand(50.0, '{v:.0f}% cloud   partial cloud, interrupted views'),
                    MessageBand(75.0, '{v:.0f}% cloud   heavy cloud, poor visibility'),
                    MessageBand(INF, '{v:.0f}% cloud   overcast, no stargazing possible'),
                ),
                unknown='Cloud cover unknown'
            )),
            'humidity': Param('humidity_percentage', Scorer(
                points=((0.0, 1.0), (50.0, 1.0), (70.0, 0.8), (85.0, 0.5), (100.0, 0.2)),
                messages=(
                    MessageBand(50.0, '{v:.0f}% humidity   dry air, sharp visibility'),
                    MessageBand(70.0, '{v:.0f}% humidity   good transparency'),
                    MessageBand(85.0, '{v:.0f}% humidity   some atmospheric blurring'),
                    MessageBand(INF, '{v:.0f}% humidity   very humid, hazy sky'),
                ),
                unknown='Humidity unknown'
            )),
            'rain': Param('precipitation_mm', Scorer(
                points=((0.1, 1.0), (1.3, 0.0), (2.5, 0.0), (7.6, 0.0), (8.0, 0.0)),
                messages=(
                    MessageBand(0.1, 'Dry: no precipitation'),
                    MessageBand(1.3, '{v:.1f} mm/h   drizzle: no stargazing possible'),
                    MessageBand(2.5, '{v:.1f} mm/h   light rain: no stargazing possible'),
                    MessageBand(7.6, '{v:.1f} mm/h   moderate rain: no stargazing possible'),
                    MessageBand(INF, '{v:.1f} mm/h   heavy rain: no stargazing possible'),
                ),
                unknown='Precipitation unknown'
            )),
        },
    },
    'gardening': {
        "id": 'gardening',
        "icon": '🌱',
        "label": 'Gardening',
        "parameters": {
            'temperature': Param('temperature_celsius', Scorer(
                points=((-5.0, 0.0), (0.0, 0.1), (5.0, 0.3), (10.0, 0.7), (13.0, 1.0), (25.0, 1.0), (32.0, 0.6), (36.0, 0.2)),
                messages=(
                    MessageBand(0.0, '{v:.0f}°C   frozen ground, do not garden'),
                    MessageBand(5.0, '{v:.0f}°C   very cold, essential tasks only'),
                    MessageBand(10.0, '{v:.0f}°C   cool, suitable for light gardening'),
                    MessageBand(25.0, '{v:.0f}°C   ideal gardening temperature'),
                    MessageBand(32.0, '{v:.0f}°C   warm, garden early morning or evening'),
                    MessageBand(INF, '{v:.0f}°C   too hot, risk of heat stress'),
                ),
                unknown='Temperature unknown'
            )),
            'rain': Param('precipitation_mm', Scorer(
                points=((0.1, 0.9), (1.3, 1.0), (2.5, 0.6), (7.6, 0.2), (8.0, 0.0)),
                messages=(
                    MessageBand(0.1, 'Dry: water plants if needed'),
                    MessageBand(1.3, '{v:.1f} mm/h   drizzle: natural watering for plants'),
                    MessageBand(2.5, '{v:.1f} mm/h   light rain: soil getting wet, avoid digging'),
                    MessageBand(7.6, '{v:.1f} mm/h   moderate rain: too wet to work outside'),
                    MessageBand(INF, '{v:.1f} mm/h   heavy rain: stay indoors'),
                ),
                unknown='Precipitation unknown'
            )),
        },
    },
    'clothing': {
        "id": 'clothing',
        "icon": '🧥',
        "label": 'Clothing',
        "parameters": {
            'temperature': Param('temperature_celsius', Scorer(
                points=((-5.0, 0.1), (0.0, 0.2), (5.0, 0.3), (10.0, 0.5), (15.0, 0.6), (20.0, 0.8), (23.0, 1.0), (26.0, 1.0), (32.0, 0.7)),
                messages=(
                    MessageBand(0.0, '{v:.0f}°C   heavy winter coat essential'),
                    MessageBand(5.0, '{v:.0f}°C   warm coat and layers needed'),
                    MessageBand(10.0, '{v:.0f}°C   jacket required'),
                    MessageBand(15.0, '{v:.0f}°C   light jacket recommended'),
                    MessageBand(20.0, '{v:.0f}°C   comfortable, light layers are enough'),
                    MessageBand(26.0, '{v:.0f}°C   warm, t-shirt weather'),
                    MessageBand(INF, '{v:.0f}°C   hot, light breathable clothing'),
                ),
                unknown='Temperature unknown'
            )),
            'wind': Param('wind_speed_m_per_s', Scorer(
                points=((3.4, 1.0), (5.5, 1.0), (8.0, 0.9), (10.8, 0.7), (13.9, 0.5), (14.0, 0.3)),
                messages=(
                    MessageBand(3.4, '{v:.0f} m/s    light breeze or calmer: no effect'),
                    MessageBand(5.5, '{v:.0f} m/s    gentle breeze: little effect'),
                    MessageBand(8.0, '{v:.0f} m/s    moderate breeze: slight chill'),
                    MessageBand(10.8, '{v:.0f} m/s    fresh breeze: a windbreaker is useful'),
                    MessageBand(13.9, '{v:.0f} m/s    strong breeze: feels noticeably colder, wear a windproof layer'),
                    MessageBand(INF, '{v:.0f} m/s    near gale or stronger: warm windproof clothing essential'),
                ),
                unknown='Wind unknown'
            )),
            'rain': Param('precipitation_mm', Scorer(
                points=((0.1, 1.0), (1.3, 0.7), (2.5, 0.4), (7.6, 0.2), (8.0, 0.2)),
                messages=(
                    MessageBand(0.1, 'Dry: no rain protection needed'),
                    MessageBand(1.3, '{v:.1f} mm/h   drizzle: an umbrella or light waterproof is useful'),
                    MessageBand(2.5, '{v:.1f} mm/h   light rain: a waterproof jacket is needed'),
                    MessageBand(7.6, '{v:.1f} mm/h   moderate rain: full waterproofs essential'),
                    MessageBand(INF, '{v:.1f} mm/h   heavy rain: full waterproofs essential'),
                ),
                unknown='Precipitation unknown'
            )),
        },
    },
    'driving': {
        "id": 'driving',
        "icon": '🚗',
        "label": 'Driving',
        "parameters": {
            'snow': Param('snow_precipitation_mm', Scorer(
                points=((0.0, 1.0), (0.05, 1.0), (0.12, 0.5), (0.5, 0.2), (1.0, 0.0)),
                messages=(
                    MessageBand(0.05, 'No snowfall'),
                    MessageBand(0.2, '{v:.1f} mm/h snow (water eq.)   light snow: snow on roads, winter tyres advised'),
                    MessageBand(0.8, '{v:.1f} mm/h snow (water eq.)   moderate snow: hazardous driving'),
                    MessageBand(INF, '{v:.1f} mm/h snow (water eq.)   heavy snow: avoid driving'),
                ),
                unknown='No snowfall'
            )),
            'wind': Param('wind_gust_m_per_s', _score_driving_wind),
            'rain': Param('precipitation_mm', Scorer(
                points=((0.1, 1.0), (1.3, 0.8), (2.5, 0.6), (7.6, 0.3), (8.0, 0.1)),
                messages=(
                    MessageBand(0.1, 'Dry: dry roads'),
                    MessageBand(1.3, '{v:.1f} mm/h   drizzle: damp roads'),
                    MessageBand(2.5, '{v:.1f} mm/h   light rain: wet roads, reduce speed, keep your distance'),
                    MessageBand(7.6, '{v:.1f} mm/h   moderate rain: reduced visibility, aquaplaning risk'),
                    MessageBand(INF, '{v:.1f} mm/h   heavy rain: very poor visibility, avoid driving if possible'),
                ),
                unknown='Precipitation unknown'
            )),
        },
    },
    'dogwalking': {
        "id": 'dogwalking',
        "icon": '🐕',
        "label": 'Dogwalking',
        "parameters": {
            'temperature': Param('temperature_celsius', Scorer(
                points=((-10.0, 0.1), (-5.0, 0.2), (2.0, 0.6), (5.0, 1.0), (22.0, 1.0), (28.0, 0.6), (32.0, 0.3), (36.0, 0.1)),
                messages=(
                    MessageBand(-5.0, '{v:.0f}°C   very cold, limit walk time for small breeds'),
                    MessageBand(2.0, '{v:.0f}°C   cold, boots may help sensitive paws'),
                    MessageBand(22.0, '{v:.0f}°C   comfortable for dogs'),
                    MessageBand(28.0, '{v:.0f}°C   warm, carry water for your dog'),
                    MessageBand(32.0, '{v:.0f}°C   hot, walk early morning or late evening'),
                    MessageBand(INF, '{v:.0f}°C   dangerous heat, hot pavement can burn paws'),
                ),
                unknown='Temperature unknown'
            )),
            'wind': Param('wind_speed_m_per_s', Scorer(
                points=((3.4, 1.0), (5.5, 1.0), (8.0, 1.0), (10.8, 0.8), (13.9, 0.5), (14.0, 0.2)),
                messages=(
                    MessageBand(3.4, '{v:.0f} m/s    light breeze or calmer: good walking conditions'),
                    MessageBand(5.5, '{v:.0f} m/s    gentle breeze: good walking conditions'),
                    MessageBand(8.0, '{v:.0f} m/s    moderate breeze: fine for most dogs'),
                    MessageBand(10.8, '{v:.0f} m/s    fresh breeze: breezy, fine for most dogs'),
                    MessageBand(13.9, '{v:.0f} m/s    strong breeze: small dogs may struggle'),
                    MessageBand(INF, '{v:.0f} m/s    near gale or stronger: keep dogs on a lead'),
                ),
                unknown='Wind unknown'
            )),
            'rain': Param('precipitation_mm', Scorer(
                points=((0.1, 1.0), (1.3, 0.8), (2.5, 0.5), (7.6, 0.3), (8.0, 0.2)),
                messages=(
                    MessageBand(0.1, 'Dry: great for a walk'),
                    MessageBand(1.3, "{v:.1f} mm/h   drizzle: most dogs don't mind"),
                    MessageBand(2.5, '{v:.1f} mm/h   light rain: keep the walk short'),
                    MessageBand(7.6, '{v:.1f} mm/h   moderate rain: short outing only'),
                    MessageBand(INF, '{v:.1f} mm/h   heavy rain: quick toilet break only'),
                ),
                unknown='Precipitation unknown'
            )),
        },
    },
}
