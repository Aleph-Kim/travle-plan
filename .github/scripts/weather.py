import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
PLAN = json.loads((ROOT / "data/plan.json").read_text(encoding="utf-8"))
OUT = ROOT / "data/weather.json"

days = PLAN["days"]
start, end = days[0]["date"], days[-1]["date"]

HOURLY = ["temperature_2m", "apparent_temperature", "precipitation_probability", "precipitation",
          "weather_code", "wind_speed_10m", "relative_humidity_2m"]
DAILY = ["weather_code", "temperature_2m_max", "temperature_2m_min", "precipitation_probability_max",
         "precipitation_sum", "wind_speed_10m_max", "uv_index_max", "sunrise", "sunset"]

data = {}
for key, loc in PLAN["locations"].items():
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={loc['lat']}&longitude={loc['lon']}"
        f"&daily={','.join(DAILY)}&hourly={','.join(HOURLY)}&wind_speed_unit=ms"
        f"&timezone=Asia%2FTokyo&start_date={start}&end_date={end}"
    )
    with urllib.request.urlopen(url, timeout=30) as res:
        body = json.load(res)
    d, h = body["daily"], body["hourly"]

    # 시간별은 날짜별로 묶어 [시, 기온, 체감, 강수확률, 강수량, 날씨코드, 풍속, 습도] 배열로 줄여 파일 크기를 줄임
    hours = {}
    for i, t in enumerate(h["time"]):
        hours.setdefault(t[:10], []).append([int(t[11:13])] + [h[f][i] for f in HOURLY])

    data[key] = {
        t: {
            "code": d["weather_code"][i],
            "max": d["temperature_2m_max"][i],
            "min": d["temperature_2m_min"][i],
            "pop": d["precipitation_probability_max"][i],
            "rain": d["precipitation_sum"][i],
            "wind": d["wind_speed_10m_max"][i],
            "uv": d["uv_index_max"][i],
            "sunrise": d["sunrise"][i][11:16] if d["sunrise"][i] else None,
            "sunset": d["sunset"][i][11:16] if d["sunset"][i] else None,
            "hours": hours.get(t, []),
        }
        for i, t in enumerate(d["time"])
    }

prev = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
prev_rain = prev.get("rain", {})
today = datetime.now(ZoneInfo("Asia/Tokyo")).date().isoformat()

# 당일과 지난 날짜는 한 번 정해진 판정을 유지해야 여행 중 일정이 갑자기 바뀌지 않음
rain = {}
for day in days:
    date = day["date"]
    if date <= today and date in prev_rain:
        rain[date] = prev_rain[date]
        continue
    w = data.get(day["weather"], {}).get(date)
    rain[date] = bool(w and w["pop"] is not None and w["pop"] >= PLAN["rainThreshold"])

out = {
    "updatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "data": data,
    "rain": rain,
}
OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("rain:", rain)
