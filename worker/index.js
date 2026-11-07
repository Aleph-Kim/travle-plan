const jsonHeaders = { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-cache' };
const dataRoot = '/travle-plan/data/';

async function travelData(db, path) {
  if (path === dataRoot + 'trips.json') {
    const { results } = await db.prepare(
      'SELECT slug, name_json, starts_on, ends_on FROM trips ORDER BY starts_on, slug',
    ).all();
    return Response.json(results.map((trip) => ({
      slug: trip.slug, name: JSON.parse(trip.name_json), start: trip.starts_on, end: trip.ends_on,
    })), { headers: jsonHeaders });
  }

  const match = path.slice(dataRoot.length).match(/^([\da-z-]+)\/(plan|i18n|weather)\.json$/);
  if (!match) return new Response('Not found', { status: 404 });

  const [, slug, kind] = match;
  const body = await db.prepare('SELECT body FROM trip_documents WHERE slug = ? AND kind = ?')
    .bind(slug, kind).first('body');
  return body === null || body === undefined
    ? new Response('Not found', { status: 404 })
    : new Response(body, { headers: jsonHeaders });
}

function webAsset(url) {
  const path = url.pathname;
  const dashboard = ['/', '/index.html', '/travle-plan/', '/travle-plan/index.html'].includes(path);
  const assetPath = dashboard ? '/index.html' : path.endsWith('/') ? path + 'index.html' : path;
  if (Object.hasOwn(assets, assetPath)) {
    const [type, value] = assets[assetPath];
    const body = type === 'image/png' ? Uint8Array.from(atob(value), (character) => character.charCodeAt(0)) : value;
    return new Response(body, { headers: { 'Content-Type': type, 'Cache-Control': 'no-cache' } });
  }
  if (path === '/travle-plan' || Object.hasOwn(assets, path + '/index.html')) {
    url.pathname += '/';
    return Response.redirect(url, 308);
  }
  return new Response('Not found', { status: 404 });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === '/mcp' && request.method === 'POST') return weatherMcp(request, env);
    if (request.method !== 'GET' && request.method !== 'HEAD') {
      return new Response('Method not allowed', { status: 405, headers: { Allow: 'GET, HEAD' } });
    }
    let response;
    try {
      response = url.pathname.startsWith(dataRoot)
        ? await travelData(env.DB, url.pathname)
        : webAsset(url);
    } catch (error) {
      console.error('Travel data unavailable', error.message);
      response = new Response('Travel data unavailable', { status: 503 });
    }
    return request.method === 'HEAD' ? new Response(null, response) : response;
  },
};

const weatherTool = {
  name: 'refresh_weather',
  description: 'Refresh eligible trip forecasts from Open-Meteo, store them in D1, and report the per-trip result. Owner only.',
  inputSchema: { type: 'object', properties: {}, additionalProperties: false },
};

async function weatherMcp(request, env) {
  let message;
  try {
    message = await request.json();
  } catch {
    return Response.json({ jsonrpc: '2.0', id: null, error: { code: -32700, message: 'Invalid JSON' } });
  }

  const reply = (result) => Response.json({ jsonrpc: '2.0', id: message?.id ?? null, result });
  const error = (code, detail) => Response.json({
    jsonrpc: '2.0', id: message?.id ?? null, error: { code, message: detail },
  });
  if (message?.jsonrpc !== '2.0' || typeof message.method !== 'string') return error(-32600, 'Invalid request');
  if (message.method === 'server/discover') {
    return reply({ supportedVersions: ['2026-07-28'], capabilities: { tools: {} } });
  }
  if (message.method === 'tools/list') return reply({ tools: [weatherTool] });
  if (message.method !== 'tools/call') return error(-32601, 'Method not found');
  if (message.params?.name !== weatherTool.name) return error(-32602, 'Unknown tool');

  // Sites가 제공하는 확인된 계정만 예보를 갱신할 수 있습니다.
  const caller = request.headers.get('oai-authenticated-user-email')?.toLowerCase();
  if (!request.headers.has('oai-authenticated-user-id') || !env.WEATHER_OWNER_EMAIL ||
      caller !== env.WEATHER_OWNER_EMAIL.toLowerCase()) {
    return reply({ isError: true, content: [{ type: 'text', text: 'Weather updates require the Site owner.' }] });
  }
  try {
    const results = await refreshTravelWeather(env.DB);
    return reply({
      isError: results.some(({ status }) => status === 'failed' || status === 'rate_limited'),
      content: [{ type: 'text', text: JSON.stringify(results) }],
    });
  } catch (error) {
    console.error('Weather task failed', error.message);
    return reply({ isError: true, content: [{ type: 'text', text: 'The weather update could not be completed.' }] });
  }
}
