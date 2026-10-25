import json
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
TRIPS = json.loads((ROOT / "data/trips.json").read_text(encoding="utf-8"))
# Open-Meteo 예보는 오늘부터 16일치까지만 받을 수 있음
FORECAST_DAYS = 16

HOURLY = ["temperature_2m", "apparent_temperature", "precipitation_probability", "precipitation",
          "weather_code", "wind_speed_10m", "relative_humidity_2m"]
DAILY = ["weather_code", "temperature_2m_max", "temperature_2m_min", "precipitation_probability_max",
         "precipitation_sum", "wind_speed_10m_max", "uv_index_max", "sunrise", "sunset"]


def update(slug):
    PLAN = json.loads((ROOT / "data" / slug / "plan.json").read_text(encoding="utf-8"))
    OUT = ROOT / "data" / slug / "weather.json"
    TRIP = PLAN["trip"]
    TZ = TRIP["timezone"]

    days = PLAN["days"]
    start, end = days[0]["date"], days[-1]["date"]
    now = datetime.now(ZoneInfo(TZ)).date()
    # 끝난 여행은 마지막 예보와 일정을 그대로 남기고, 예보 범위 밖의 여행은 범위 안에 들어올 때부터 받음
    if end < now.isoformat():
        print(slug, "ended")
        return
    last = min(end, (now + timedelta(days=FORECAST_DAYS - 1)).isoformat())
    if start > last:
        print(slug, "not in forecast range")
        return

    data = {}
    for key, loc in PLAN["locations"].items():
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={loc['lat']}&longitude={loc['lon']}"
            f"&daily={','.join(DAILY)}&hourly={','.join(HOURLY)}&wind_speed_unit=ms"
            f"&timezone={urllib.parse.quote(TZ, safe='')}&start_date={start}&end_date={last}"
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
    prev_rain, prev_plan = prev.get("rain", {}), prev.get("plan", {})
    today = now.isoformat()
    by_date = {d["date"]: d for d in days}

    def rainy(date, key):
        w = data.get(by_date[date]["plans"][key]["weather"], {}).get(date)
        return bool(w and w["pop"] is not None and w["pop"] >= PLAN["rainThreshold"])

    def has(date, key):
        return key in by_date[date]["plans"]

    # 고정된 일정이 나중에 plan.json에서 빠졌으면 그날 기본 일정으로 봄
    def locked_key(date):
        key = prev_plan.get(date, by_date[date]["default"])
        return key if has(date, key) else by_date[date]["default"]

    # 당일과 지난 날짜는 한 번 정해진 일정과 비 판정을 유지해야 여행 중 일정이 갑자기 바뀌지 않음
    locked = {d: locked_key(d) for d in by_date if d <= today}
    default = {d: by_date[d]["default"] for d in by_date}

    # 가중치가 있는 일정에 비가 오면 base 일정 날짜와 맞바꿈. 여러 곳이 비면 가중치가 큰 일정이 맑은 날을 가져감.
    # 맞바꿀 두 날짜 모두 서로의 일정을 plan.json에 갖고 있을 때만 후보가 됨
    SWAP = TRIP.get("swap") or {}
    WEIGHT = SWAP.get("weights", {})
    BASE = SWAP.get("base")
    candidates = [dict(default)]
    for d, k in default.items():
        if k not in WEIGHT:
            continue
        for b, bk in default.items():
            if bk == BASE and has(d, BASE) and has(b, k):
                c = dict(default)
                c[d], c[b] = BASE, k
                candidates.append(c)

    def cost(c):
        total = 0.0
        for d, k in c.items():
            if d in locked:
                continue
            total += WEIGHT.get(k, 0) * rainy(d, k) + (0.5 if k != default[d] else 0)
        return total

    valid = [c for c in candidates if all(c[d] == k for d, k in locked.items())] or [dict(default, **locked)]
    assign = min(valid, key=cost)

    rain = {}
    for date, key in assign.items():
        rain[date] = prev_rain[date] if date in locked and date in prev_rain else rainy(date, key)

    out = {
        "updatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "data": data,
        "plan": assign,
        "rain": rain,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(slug, "plan:", assign)
    print(slug, "rain:", rain)


for t in TRIPS:
    update(t["slug"])
