# ETag: версионирование ресурсов

# Генерация на сервере
def generate_etag(content):
    return f'"{hashlib.md5(content).hexdigest()}"'

# Проверка
@app.route('/api/product/<id>')
def get_product(id):
    product = db.get_product(id)
    etag = generate_etag(json.dumps(product))

    if request.headers.get('If-None-Match') == etag:
        return '', 304  # Not Modified

    return jsonify(product), 200, {'ETag': etag}