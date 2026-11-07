const forecastDays = 16;
const hourMs = 60 * 60 * 1000;
const forecastUrl = 'https://api.open-meteo.com/v1/forecast';
const hourlyFields = ['temperature_2m', 'apparent_temperature', 'precipitation_probability',
  'precipitation', 'weather_code', 'wind_speed_10m', 'relative_humidity_2m'];
const dailyFields = {
  code: 'weather_code', max: 'temperature_2m_max', min: 'temperature_2m_min',
  pop: 'precipitation_probability_max', rain: 'precipitation_sum', wind: 'wind_speed_10m_max',
  uv: 'uv_index_max', sunrise: 'sunrise', sunset: 'sunset',
};

function dateAfter(date, days) {
  return new Date(Date.parse(date) + days * 24 * hourMs).toISOString().slice(0, 10);
}

async function readForecast(locations, timezone, start, end) {
  const entries = Object.entries(locations);
  const url = new URL(forecastUrl);
  url.search = new URLSearchParams({
    latitude: entries.map(([, location]) => location.lat).join(','),
    longitude: entries.map(([, location]) => location.lon).join(','),
    timezone, start_date: start, end_date: end, wind_speed_unit: 'ms',
    daily: Object.values(dailyFields).join(','), hourly: hourlyFields.join(','),
  });
  const response = await fetch(url, { signal: AbortSignal.timeout(10000) });
  if (!response.ok) {
    const error = new Error(`Open-Meteo HTTP ${response.status}`);
    error.status = response.status;
    throw error;
  }
  const forecast = await response.json();
  const rows = Array.isArray(forecast) ? forecast : [forecast];
  if (rows.length !== entries.length) throw new Error('Open-Meteo returned an incomplete location list');
  return Object.fromEntries(entries.map(([key], index) => [key, formatForecast(rows[index])]));
}

function formatForecast({ daily, hourly }) {
  const valid = (rows, fields) => Array.isArray(rows?.time) && rows.time.length > 0 &&
    fields.every((field) => Array.isArray(rows[field]) && rows[field].length === rows.time.length);
  if (!valid(daily, Object.values(dailyFields)) || !valid(hourly, hourlyFields)) {
    throw new Error('Open-Meteo returned an incomplete forecast');
  }

  const hoursByDay = new Map();
  for (const [index, time] of hourly.time.entries()) {
    const day = time.slice(0, 10);
    if (!hoursByDay.has(day)) hoursByDay.set(day, []);
    hoursByDay.get(day).push([Number(time.slice(11, 13)), ...hourlyFields.map((field) => hourly[field][index])]);
  }
  return Object.fromEntries(daily.time.map((day, index) => {
    const values = Object.fromEntries(Object.entries(dailyFields).map(([key, field]) => {
      const value = daily[field][index];
      return [key, field === 'sunrise' || field === 'sunset' ? value?.slice(11, 16) ?? null : value];
    }));
    return [day, { ...values, hours: hoursByDay.get(day) ?? [] }];
  }));
}

function assignWeatherPlan(plan, data, previous, today) {
  const days = new Map(plan.days.map((day) => [day.date, day]));
  const defaults = Object.fromEntries(plan.days.map((day) => [day.date, day.default]));
  const locked = {};
  const { base, weights = {} } = plan.trip.swap ?? {};
  const hasPlan = (date, key) => Object.hasOwn(days.get(date).plans, key);
  const rainy = (date, key) => {
    const location = days.get(date).plans[key].weather;
    const pop = data[location]?.[date]?.pop;
    return pop != null && pop >= plan.rainThreshold;
  };

  // 당일과 지난 날짜의 일정과 비 판정은 기존에 확정한 값을 유지합니다.
  for (const [date, key] of Object.entries(defaults)) {
    if (date <= today) {
      const previousKey = previous.plan?.[date];
      locked[date] = hasPlan(date, previousKey) ? previousKey : key;
    }
  }

  const candidates = [defaults];
  for (const [date, key] of Object.entries(defaults)) {
    if (!Object.hasOwn(weights, key)) continue;
    for (const [baseDate, baseKey] of Object.entries(defaults)) {
      if (baseKey === base && hasPlan(date, base) && hasPlan(baseDate, key)) {
        candidates.push({ ...defaults, [date]: base, [baseDate]: key });
      }
    }
  }
  const cost = (assignment) => Object.entries(assignment).reduce((total, [date, key]) =>
    Object.hasOwn(locked, date) ? total : total +
      (weights[key] ?? 0) * Number(rainy(date, key)) + (key === defaults[date] ? 0 : 0.5), 0);
  let selected = null;
  let lowest = Infinity;
  for (const candidate of candidates) {
    if (!Object.entries(locked).every(([date, key]) => candidate[date] === key)) continue;
    const score = cost(candidate);
    if (score < lowest) {
      selected = candidate;
      lowest = score;
    }
  }
  const assignment = selected ?? { ...defaults, ...locked };
  const rain = Object.fromEntries(Object.entries(assignment).map(([date, key]) => [
    date, Object.hasOwn(locked, date) && Object.hasOwn(previous.rain ?? {}, date)
      ? previous.rain[date] : rainy(date, key),
  ]));
  return { plan: assignment, rain };
}

async function updateWeatherTrip(db, trip, now) {
  const today = new Date(now).toLocaleDateString('sv-SE', { timeZone: trip.timezone });
  const plan = JSON.parse(trip.plan_body);
  const start = plan.days[0].date;
  const end = plan.days.at(-1).date;
  const until = [end, dateAfter(today, forecastDays - 1)].sort()[0];
  if (end < today || start > until) return { slug: trip.slug, status: 'outside_forecast_window' };

  const hourStart = Math.floor(now / hourMs) * hourMs;
  const claim = await db.prepare(`
    UPDATE trips SET weather_checked_at = ? WHERE slug = ? AND weather_checked_at < ?
  `).bind(now, trip.slug, hourStart).run();
  if (!claim.meta.changes) return { slug: trip.slug, status: 'already_checked' };

  try {
    const data = await readForecast(plan.locations, trip.timezone, start, until);
    const previous = trip.weather_body ? JSON.parse(trip.weather_body) : {};
    const updatedAt = new Date(now).toISOString();
    const weather = { updatedAt, data, ...assignWeatherPlan(plan, data, previous, today) };
    const saved = await db.prepare(`
      INSERT INTO trip_documents (slug, kind, body)
      SELECT slug, 'weather', ? FROM trips WHERE slug = ? AND weather_checked_at = ?
      ON CONFLICT(slug, kind) DO UPDATE SET body = excluded.body
      WHERE COALESCE(julianday(json_extract(trip_documents.body, '$.updatedAt')), 0)
        < julianday(json_extract(excluded.body, '$.updatedAt'))
      RETURNING json_extract(body, '$.updatedAt') AS updated_at
    `).bind(JSON.stringify(weather), trip.slug, now).first('updated_at');
    return saved ? { slug: trip.slug, status: 'updated', updatedAt: saved }
      : { slug: trip.slug, status: 'superseded' };
  } catch (error) {
    // 제공사의 요청 제한은 다음 시간에 다시 확인합니다.
    if (error.status === 429) return { slug: trip.slug, status: 'rate_limited' };
    // 같은 시간의 재시도는 허용하고 이미 저장된 예보는 유지합니다.
    await db.prepare('UPDATE trips SET weather_checked_at = ? WHERE slug = ? AND weather_checked_at = ?')
      .bind(hourStart - 1, trip.slug, now).run();
    throw error;
  }
}

async function refreshTravelWeather(db) {
  const { results: trips } = await db.prepare(`
    SELECT t.slug, t.timezone, p.body AS plan_body, w.body AS weather_body
    FROM trips t
    JOIN trip_documents p ON p.slug = t.slug AND p.kind = 'plan'
    LEFT JOIN trip_documents w ON w.slug = t.slug AND w.kind = 'weather'
    ORDER BY t.starts_on, t.slug
  `).all();
  const now = Date.now();
  const results = [];
  for (const trip of trips) {
    try {
      results.push(await updateWeatherTrip(db, trip, now));
    } catch (error) {
      console.error('Weather update failed', trip.slug, error.message);
      results.push({ slug: trip.slug, status: 'failed' });
    }
  }
  return results;
}
