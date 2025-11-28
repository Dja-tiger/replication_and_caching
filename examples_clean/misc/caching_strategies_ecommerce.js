// Статика - агрессивное кэширование
app.use('/static', express.static('public', {
  maxAge: '1y',  // 1 год
  immutable: true,  // Файл никогда не изменится
  etag: false  // Не нужен для immutable
}));

// API - валидационное кэширование
app.get('/api/products', (req, res) => {
  const products = getProducts();
  const etag = generateETag(products);

  res.set({
    'Cache-Control': 'private, max-age=0, must-revalidate',
    'ETag': etag
  });

  if (req.get('If-None-Match') === etag) {
    return res.status(304).end();
  }

  res.json(products);
});