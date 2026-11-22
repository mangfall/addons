"""Build tools/demo-home.json: a made-up sample home for marketing screenshots of the cards.

Every name and value is invented; nothing comes from a real installation.
Usage: python3 tools/demo_home.py
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

NOW = datetime(2026, 11, 22, 13, 30, tzinfo=timezone.utc)
ISO = NOW.isoformat()
states, entities, devices = {}, {}, {}
areas = {a.lower(): {"name": a} for a in ["Wohnzimmer", "Küche", "Schlafzimmer", "Bad", "Büro", "Flur", "Garten", "Garage"]}
areas = {k.replace("ü", "u"): v for k, v in areas.items()}


def add(eid, state, area=None, device=None, **attrs):
    states[eid] = {"entity_id": eid, "state": str(state), "attributes": attrs, "last_changed": ISO, "last_updated": ISO}
    dev = device or eid.split(".", 1)[1]
    devices.setdefault(dev, {"area_id": area})
    entities[eid] = {"device_id": dev, "area_id": area}


P = dict(device_class="power", unit_of_measurement="W", state_class="measurement")
# Energy: sunny November noon, battery charging, feeding the rest into the grid
add("sensor.pv_leistung", 4120, None, "wechselrichter", friendly_name="PV Leistung", **P)
add("sensor.netz_leistung", -1340, None, "stromzaehler", friendly_name="Stromzähler Netzleistung", **P)
add("sensor.batteriespeicher_leistung", -1450, None, "speicher", friendly_name="Batteriespeicher Leistung", **P)
add("sensor.hausverbrauch", 1330, None, "stromzaehler", friendly_name="Hausverbrauch", **P)
add("sensor.batteriespeicher_ladestand", 78, None, "speicher", friendly_name="Batteriespeicher Ladestand",
    device_class="battery", unit_of_measurement="%")
# Cistern (LEVEL)
add("sensor.zisterne_fullstand", 3240, "garten", "mangfall_level", friendly_name="Zisterne Füllstand",
    device_class="volume_storage", unit_of_measurement="L", state_class="measurement")
add("sensor.zisterne_fullgrad", 65, "garten", "mangfall_level", friendly_name="Zisterne Füllgrad", unit_of_measurement="%")
# Rooms
for room, t, h in [("wohnzimmer", 21.4, 47), ("kuche", 22.1, 51), ("schlafzimmer", 18.6, 55), ("bad", 23.0, 62), ("buro", 20.7, 42)]:
    name = areas[room]["name"]
    add(f"sensor.{room}_temperatur", t, room, f"{room}_klima", friendly_name=f"{name} Temperatur",
        device_class="temperature", unit_of_measurement="°C", state_class="measurement")
    add(f"sensor.{room}_luftfeuchtigkeit", h, room, f"{room}_klima", friendly_name=f"{name} Luftfeuchtigkeit",
        device_class="humidity", unit_of_measurement="%", state_class="measurement")
add("sensor.wohnzimmer_co2", 640, "wohnzimmer", "wohnzimmer_klima", friendly_name="Wohnzimmer CO₂",
    device_class="carbon_dioxide", unit_of_measurement="ppm")
add("sensor.buro_co2", 1180, "buro", "buro_klima", friendly_name="Büro CO₂", device_class="carbon_dioxide", unit_of_measurement="ppm")
# Heating
for room, cur, target, action in [("wohnzimmer", 21.4, 21.5, "heating"), ("bad", 23.0, 23.0, "idle"), ("schlafzimmer", 18.6, 18.0, "idle"), ("buro", 20.7, 21.0, "heating")]:
    add(f"climate.{room}", "heat", room, f"{room}_thermostat", friendly_name=f"{areas[room]['name']}",
        current_temperature=cur, temperature=target, hvac_action=action, hvac_modes=["off", "heat"], min_temp=5, max_temp=30)
# Dynamic price (ct shape over the day, in EUR/kWh)
today = [0.24, 0.23, 0.22, 0.22, 0.23, 0.25, 0.29, 0.33, 0.31, 0.27, 0.22, 0.18, 0.16, 0.15, 0.17, 0.21, 0.27, 0.34, 0.37, 0.35, 0.31, 0.28, 0.26, 0.25]
add("sensor.tibber_strompreis", 0.15, None, "tibber", friendly_name="Tibber Strompreis", unit_of_measurement="EUR/kWh", today=today)
# Car
add("sensor.id_3_ladestand", 64, "garage", "id3", friendly_name="ID.3 Ladestand", device_class="battery", unit_of_measurement="%")
add("sensor.id_3_reichweite", 248, "garage", "id3", friendly_name="ID.3 Reichweite", device_class="distance", unit_of_measurement="km")
add("binary_sensor.id_3_ladekabel", "on", "garage", "id3", friendly_name="ID.3 Ladekabel", device_class="plug")
# Mower, vacuum
add("lawn_mower.sileno", "docked", "garten", "maehroboter", friendly_name="Mähroboter")
add("sensor.sileno_akku", 100, "garten", "maehroboter", friendly_name="Mähroboter Akku", device_class="battery", unit_of_measurement="%")
add("vacuum.saugi", "docked", "flur", "saugroboter", friendly_name="Saugi", battery_level=92)
# Waste
d = lambda n: (NOW + timedelta(days=n)).strftime("%Y-%m-%d")  # noqa: E731
add("sensor.abfallkalender", "morgen", None, "abfall", friendly_name="Abfallkalender",
    **{"Gelber Sack": d(1), "Restmüll": d(4), "Papier": d(9), "Biotonne": d(6)})
# Weather
add("weather.musterstadt", "sunny", None, "wetter", friendly_name="Musterstadt", temperature=9.0, humidity=71, wind_speed=12.0,
    pressure=1021, cloud_coverage=10, temperature_unit="°C", wind_speed_unit="km/h", supported_features=3)
# Lights
for eid, st, area, name in [("light.wohnzimmer_decke", "on", "wohnzimmer", "Decke"), ("light.wohnzimmer_stehlampe", "on", "wohnzimmer", "Stehlampe"),
                            ("light.kuche", "on", "kuche", "Küche"), ("light.flur", "off", "flur", "Flur"), ("light.schlafzimmer", "off", "schlafzimmer", "Schlafzimmer"),
                            ("light.terrasse", "off", "garten", "Terrasse")]:
    add(eid, st, area, eid.split(".")[1], friendly_name=name, brightness=180 if st == "on" else None, supported_color_modes=["brightness"])
# Covers, openings, security
for room, pos in [("wohnzimmer", 100), ("kuche", 100), ("schlafzimmer", 0), ("buro", 60)]:
    add(f"cover.{room}_rollladen", "open" if pos else "closed", room, f"{room}_rollladen", friendly_name=f"{areas[room]['name']} Rollladen",
        current_position=pos, device_class="shutter", supported_features=15)
add("binary_sensor.terrassentur", "off", "wohnzimmer", "terrassentur", friendly_name="Terrassentür", device_class="door")
add("binary_sensor.bad_fenster", "on", "bad", "bad_fenster", friendly_name="Badfenster", device_class="window")
add("binary_sensor.kuche_fenster", "off", "kuche", "kuche_fenster", friendly_name="Küchenfenster", device_class="window")
add("lock.haustur", "locked", "flur", "haustur", friendly_name="Haustür")
add("alarm_control_panel.alarmanlage", "disarmed", "flur", "alarm", friendly_name="Alarmanlage")
add("binary_sensor.rauchmelder_flur", "off", "flur", "rauchmelder", friendly_name="Rauchmelder Flur", device_class="smoke")
# Batteries of small devices
for eid, v, name in [("sensor.bad_fenster_batterie", 18, "Badfenster"), ("sensor.rauchmelder_flur_batterie", 64, "Rauchmelder Flur"),
                     ("sensor.thermostat_bad_batterie", 81, "Thermostat Bad"), ("sensor.terrassentur_batterie", 92, "Terrassentür")]:
    add(eid, v, None, eid.split(".")[1], friendly_name=f"{name} Batterie", device_class="battery", unit_of_measurement="%")
# Media, people
add("media_player.wohnzimmer", "playing", "wohnzimmer", "lautsprecher", friendly_name="Wohnzimmer", media_title="Sonntagmorgen",
    media_artist="Jazz Trio", volume_level=0.32, supported_features=152463)
add("person.anna", "home", None, "anna", friendly_name="Anna")
add("person.ben", "not_home", None, "ben", friendly_name="Ben")
add("zone.home", "1", None, "home", friendly_name="Zuhause")

out = Path(__file__).with_name("demo-home.json")
out.write_text(json.dumps({"_hinweis": "Erfundener Beispielhaushalt für Werbebilder. Keine echten Daten.",
                           "states": states, "entities": entities, "devices": devices, "areas": areas}, ensure_ascii=False, indent=1))
print(out, len(states), "entities")
