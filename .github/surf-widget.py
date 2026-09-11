#!/usr/bin/env python3
"""Daily surf widget for the GitHub profile README.

Fetches the wave forecast for Steamer Lane, Santa Cruz from the free
Open-Meteo marine API (no key needed) plus wind from the standard
forecast API, then renders a small dark SVG strip at repo root: surf.svg.

Runs in GitHub Actions once a day; safe to run locally too.
"""
import json
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

LAT, LON = 36.9511, -122.0253  # Steamer Lane, Santa Cruz
TZ = ZoneInfo("America/Los_Angeles")
SPOT = "STEAMER LANE \u00b7 SANTA CRUZ"


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "surf-widget/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def main():
    marine = get_json(
        "https://marine-api.open-meteo.com/v1/marine"
        f"?latitude={LAT}&longitude={LON}"
        "&hourly=wave_height,wave_period"
        "&daily=wave_height_max"
        "&timezone=America%2FLos_Angeles&forecast_days=2"
    )
    wx = get_json(
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={LAT}&longitude={LON}"
        "&hourly=wind_speed_10m,wind_direction_10m"
        "&wind_speed_unit=kn"
        "&timezone=America%2FLos_Angeles&forecast_days=2"
    )

    today = datetime.now(TZ).date().isoformat()
    mh, wh, wxh = marine["hourly"], marine["hourly"], wx["hourly"]

    # Daytime window 06:00-18:00 local for "today"
    heights, periods, winds, wdirs = [], [], [], []
    for i, t in enumerate(mh["time"]):
        if t.startswith(today) and 6 <= int(t[11:13]) <= 18:
            if mh["wave_height"][i] is not None:
                heights.append(mh["wave_height"][i])
            if mh["wave_period"][i] is not None:
                periods.append(mh["wave_period"][i])
    for i, t in enumerate(wxh["time"]):
        if t.startswith(today) and 6 <= int(t[11:13]) <= 18:
            if wxh["wind_speed_10m"][i] is not None:
                winds.append(wxh["wind_speed_10m"][i])
                wdirs.append(wxh["wind_direction_10m"][i])

    if not heights:  # fall back to full-day values
        heights = [v for v in mh["wave_height"] if v is not None][:24]
    if not periods:
        periods = [v for v in mh["wave_period"] if v is not None][:24]

    lo_ft = round(min(heights) * 3.28084)
    hi_ft = round(max(heights) * 3.28084)
    wave_txt = f"{lo_ft}\u2013{hi_ft} ft" if lo_ft != hi_ft else f"{lo_ft} ft"
    period = round(sum(periods) / len(periods))
    wind_kn = round(sum(winds) / len(winds)) if winds else 0
    wdir = (sum(wdirs) / len(wdirs)) if wdirs else 0

    # Steamer Lane faces roughly south: offshore = wind from N/NE/NW
    offshore = wdir >= 290 or wdir <= 130
    onshore = 150 <= wdir <= 210
    wind_txt = f"{wind_kn} kt " + ("offshore" if offshore else "onshore" if onshore else "cross-shore")

    # 0-5 star rating
    avg_ft = (lo_ft + hi_ft) / 2
    if avg_ft < 2:
        s = 1
    elif avg_ft < 3:
        s = 2
    elif avg_ft <= 6:
        s = 4
    elif avg_ft <= 10:
        s = 5
    else:
        s = 3
    if period >= 10:
        s += 1
    elif period < 8:
        s -= 1
    if wind_kn < 6:
        s += 1
    elif wind_kn > 12:
        s -= 1
    if offshore and wind_kn <= 12:
        s += 1
    s = max(1, min(5, s))
    stars = "\u2605" * s + "\u2606" * (5 - s)

    updated = datetime.now(TZ).strftime("%b %-d")

    svg = f"""<svg width="680" height="96" viewBox="0 0 680 96" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Steamer Lane surf forecast">
  <rect x="0.5" y="0.5" width="679" height="95" rx="12" fill="#0d1526" stroke="#1e293b"/>
  <text x="24" y="32" font-family="system-ui, -apple-system, 'Segoe UI', sans-serif" font-size="12" letter-spacing="2.5" fill="#7d8aa5">\U0001f3c4\u2009{SPOT} \u2014 TODAY\u2019S SURF</text>
  <text x="656" y="32" text-anchor="end" font-family="system-ui, -apple-system, 'Segoe UI', sans-serif" font-size="11" fill="#5b6b86">Updated {updated}</text>
  <text x="24" y="70" font-family="system-ui, -apple-system, 'Segoe UI', sans-serif" font-size="27" font-weight="700" fill="#ffffff">{wave_txt}<tspan font-size="18" font-weight="400" fill="#7d8aa5"> @ {period}s</tspan></text>
  <text x="300" y="68" font-family="system-ui, -apple-system, 'Segoe UI', sans-serif" font-size="17" fill="#b8c4d8">Wind {wind_txt}</text>
  <text x="656" y="70" text-anchor="end" font-family="system-ui, -apple-system, 'Segoe UI', sans-serif" font-size="22" letter-spacing="3" fill="#fbbf24">{stars}</text>
</svg>
"""
    with open("surf.svg", "w") as f:
        f.write(svg)
    print(f"wrote surf.svg: {wave_txt} @ {period}s, wind {wind_txt}, {stars}")


if __name__ == "__main__":
    main()
