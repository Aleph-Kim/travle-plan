// 오프라인에서도 쓸 수 있도록 마지막으로 받은 화면과 데이터를 보관하고, 항상 보관본으로 응답함.
// 새 버전은 STAGED 에 따로 받아 두었다가 화면을 새로 열 때(내비게이션) 한꺼번에 ACTIVE 로 옮겨 반영함.
const ACTIVE = 'trip-active';
const STAGED = 'trip-staged';
const WEATHER = 'https://raw.githubusercontent.com/Aleph-Kim/travle-plan/main/data/weather.json';
const BASE = new URL('./', self.location).href;
const FILES = ['index.html', 'config.js', 'data/plan.json', 'manifest.webmanifest',
  'icon.svg', 'icon-180.png', 'icon-192.png', 'icon-512.png', 'icon-maskable-512.png'].map((f) => BASE + f);
const TRACKED = FILES.concat([WEATHER]);
// 이 파일이 바뀌면 새로고침을 물어봄. 날씨는 일정이 바뀔 때(plan, rain)만 물어봄
const ASK = [BASE + 'index.html', BASE + 'config.js', BASE + 'data/plan.json'];

const keyOf = (url) => {
  const u = new URL(url);
  u.search = '';
  if (u.href === BASE) return BASE + 'index.html';
  return u.href;
};

const text = (res) => (res ? res.clone().text() : Promise.resolve(null));

// 네트워크에서 받은 파일이 보관본과 다르면 STAGED 에 넣음
async function stage() {
  const active = await caches.open(ACTIVE);
  const staged = await caches.open(STAGED);
  let ask = false;
  for (const url of TRACKED) {
    let res;
    try {
      res = await fetch(url, { cache: 'no-cache' });
    } catch (e) {
      return { offline: true };
    }
    if (!res.ok) continue;
    const body = await res.clone().text();
    const cur = await active.match(url);
    if (!cur) { await active.put(url, res); continue; }
    const pending = await staged.match(url);
    const base = pending ? await text(pending) : await text(cur);
    if (body === base) continue;
    const activeBody = await text(cur);
    if (body === activeBody) { await staged.delete(url); continue; }
    await staged.put(url, res);
  }
  // 물어볼지 판단은 사용자가 보고 있는 ACTIVE 와 STAGED 를 비교
  for (const url of ASK) if (await staged.match(url)) ask = true;
  const sw = await staged.match(WEATHER);
  if (sw) {
    try {
      const a = JSON.parse(await text(await active.match(WEATHER)));
      const b = JSON.parse(await text(sw));
      if (JSON.stringify([a.plan, a.rain]) !== JSON.stringify([b.plan, b.rain])) ask = true;
    } catch (e) { ask = true; }
  }
  const sig = [];
  for (const req of await staged.keys()) sig.push(req.url + ':' + (await text(await staged.match(req))).length);
  return { ask, sig: sig.sort().join('|') };
}

// 받아 둔 새 버전을 ACTIVE 로 옮김
async function promote() {
  const staged = await caches.open(STAGED);
  const reqs = await staged.keys();
  if (!reqs.length) return;
  const active = await caches.open(ACTIVE);
  for (const req of reqs) await active.put(req, await staged.match(req));
  await caches.delete(STAGED);
}

self.addEventListener('install', (event) => {
  event.waitUntil(stage().then(() => self.skipWaiting(), () => self.skipWaiting()));
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== ACTIVE && k !== STAGED).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('message', (event) => {
  const port = event.ports[0];
  if (!port) return;
  if (event.data === 'check') event.waitUntil(stage().then((r) => port.postMessage(r), () => port.postMessage({ offline: true })));
});

async function fromActive(request, key) {
  const active = await caches.open(ACTIVE);
  const hit = await active.match(key);
  if (hit) return hit;
  const res = await fetch(request);
  if (res.ok) await active.put(key, res.clone());
  return res;
}

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;
  if (req.mode === 'navigate' && req.url.startsWith(BASE)) {
    event.respondWith(promote().then(() => fromActive(req, BASE + 'index.html')));
    return;
  }
  const key = keyOf(req.url);
  if (TRACKED.indexOf(key) === -1) return;
  event.respondWith(fromActive(req, key));
});
