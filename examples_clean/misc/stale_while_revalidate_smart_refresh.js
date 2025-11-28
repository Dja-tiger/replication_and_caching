self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request).then(cached => {
      const fetched = fetch(event.request)
        .then(response => {
          caches.open('v1').then(cache =>
            cache.put(event.request, response.clone()));
          return response;
        });
      return cached || fetched;
    })
  );
});