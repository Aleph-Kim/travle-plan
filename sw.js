// 일정이나 화면 파일이 바뀌면 이 값을 올려야 기존 캐시가 교체됨
const CACHE = 'trip-v17';
const WEATHER = 'https://raw.githubusercontent.com/Aleph-Kim/travle-plan/main/data/weather.json';
const ASSETS = ['./', './index.html', './config.js', './data/plan.json', './manifest.webmanifest'];

self.addEventListener('install', (event) => {
  // 브라우저 HTTP 캐시에 남은 이전 파일이 새 캐시에 들어가지 않도록 서버에서 다시 받음
  event.waitUntil(caches.open(CACHE)
    .then((c) => c.addAll(ASSETS.map((u) => new Request(u, { cache: 'reload' }))))
    .then(() => self.skipWaiting()));
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  const url = new URL(req.url);
  if (req.method !== 'GET') return;

  // 공유 날씨는 항상 최신을 먼저 받고, 오프라인일 때만 마지막 사본을 보여줌
  if (url.href.startsWith(WEATHER)) {
    event.respondWith(
      fetch(req).then((res) => {
        if (res.ok) { const copy = res.clone(); caches.open(CACHE).then((c) => c.put(WEATHER, copy)); }
        return res;
      }).catch(() => caches.match(WEATHER))
    );
    return;
  }
  if (url.origin !== self.location.origin) return;
  // 홈 화면 아이콘은 OS가 직접 받아가므로 서비스 워커가 가로채지 않음 (잘 되는 onochu 구성과 동일하게)
  if (/\/icon[^/]*\.(png|svg)$/.test(url.pathname)) return;

  // 저속망 대비 캐시를 먼저 보여주고 뒤에서 갱신
  event.respondWith(
    caches.open(CACHE).then((cache) =>
      cache.match(req, { ignoreSearch: true }).then((cached) => {
        const network = fetch(req).then((res) => {
          if (res.ok) cache.put(req, res.clone());
          return res;
        }).catch(() => cached);
        return cached || network;
      })
    )
  );
});
