// 오프라인 캐시를 없애면서, 이미 설치된 기기에서 이전 캐시를 지우고 스스로 해제하기 위한 파일 (요청은 가로채지 않음)
self.addEventListener('install', () => self.skipWaiting());

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.map((k) => caches.delete(k))))
      .then(() => self.registration.unregister())
  );
});
