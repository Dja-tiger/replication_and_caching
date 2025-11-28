// Глобальные переменные
let ws = null;
let cart = [];
let currentUser = { id: 1, name: 'User' };
let pollingIntervals = {};

// Инициализация приложения
document.addEventListener('DOMContentLoaded', function() {
    try {
        console.log('DOMContentLoaded fired');

        console.log('Calling initWebSocket...');
        initWebSocket();

        console.log('Calling loadInitialData...');
        loadInitialData();

        console.log('Calling setupPolling...');
        setupPolling();

        console.log('Calling setupEventListeners...');
        setupEventListeners();

        // Загружаем данные пользователя
        console.log('Calling loadUserProfile...');
        loadUserProfile();

        // Определяем текущую страницу
        const path = window.location.pathname;
        if (path.includes('/product/')) {
            initProductPage();
        } else if (path.includes('/profile')) {
            initProfilePage();
        } else {
            initHomePage();
        }
    } catch (error) {
        console.error('Error in DOMContentLoaded:', error);
    }
});

// WebSocket подключение
function initWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    try {
        ws = new WebSocket(wsUrl);

        ws.onopen = function() {
            updateWSStatus('connected', 'Подключено');
            showNotification('WebSocket подключен', 'success');
        };

        ws.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            } catch (e) {
                console.error('Ошибка парсинга WebSocket сообщения:', e);
            }
        };

        ws.onclose = function() {
            updateWSStatus('disconnected', 'Отключено');
            showNotification('WebSocket отключен', 'error');

            // Переподключение через 5 секунд
            setTimeout(initWebSocket, 5000);
        };

        ws.onerror = function(error) {
            console.error('WebSocket ошибка:', error);
            updateWSStatus('disconnected', 'Ошибка');
        };

    } catch (e) {
        console.error('Не удалось создать WebSocket:', e);
        updateWSStatus('disconnected', 'Ошибка подключения');
    }
}

// Обработка сообщений WebSocket
function handleWebSocketMessage(data) {
    console.log('WebSocket сообщение:', data);

    switch (data.type) {
        case 'cache_invalidated':
            if (data.cache) {
                showNotification(`Кэш "${data.cache}" инвалидирован`, 'info');
                refreshData(data.cache);
            }
            break;

        case 'flash_sales_updated':
            showNotification('Flash Sales обновлены!', 'warning');
            loadFlashSales();
            break;

        case 'profile_updated':
            showNotification('Профиль пользователя обновлен', 'info');
            if (data.user_id === currentUser.id) {
                loadUserProfile();
            }
            break;

        case 'all_caches_invalidated':
            showNotification('Все кэши инвалидированы!', 'warning');
            loadAllData();
            break;

        case 'cart_updated':
            showNotification('Корзина обновлена', 'info');
            loadCart();
            break;
    }
}

// Статус WebSocket
function updateWSStatus(status, text) {
    const indicator = document.getElementById('ws-status');
    if (indicator) {
        indicator.textContent = text;
        indicator.className = `status-indicator ${status}`;
    }
}

// Настройка поллинга для TTL кэшей
function setupPolling() {
    // Поллинг бестселлеров каждые 30 секунд (TTL 1 час)
    pollingIntervals.bestsellers = setInterval(() => {
        loadBestsellers();
    }, 30000);

    // Поллинг рекомендаций каждые 45 секунд (TTL 1 час)
    pollingIntervals.recommendations = setInterval(() => {
        loadRecommendations();
    }, 45000);

    // Поллинг комментариев каждую минуту
    pollingIntervals.comments = setInterval(() => {
        loadTopComments();
    }, 60000);
}

// API вызовы
async function apiCall(endpoint, options = {}) {
    console.log(`apiCall to ${endpoint}`);
    try {
        const response = await fetch(`/api${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        console.log(`apiCall to ${endpoint} succeeded`, data);
        return data;
    } catch (error) {
        console.error(`API ошибка (${endpoint}):`, error);
        showNotification(`Ошибка: ${error.message}`, 'error');
        throw error;
    }
}

// Загрузка начальных данных
async function loadInitialData() {
    console.log('loadInitialData called');
    try {
        await Promise.all([
            loadBestsellers(),
            loadRecommendations(),
            loadFlashSales(),
            loadTopComments(),
            loadCart()
        ]);
        console.log('loadInitialData completed');
    } catch (error) {
        console.error('Ошибка загрузки начальных данных:', error);
    }
}

// Загрузка всех данных (после инвалидации)
async function loadAllData() {
    loadInitialData();
}

// Загрузка бестселлеров
async function loadBestsellers() {
    console.log('loadBestsellers called');
    const container = document.getElementById('bestsellers');
    if (container) {
        container.innerHTML = '<div class="loading"></div>';
        console.log('bestsellers container found');
    } else {
        console.log('bestsellers container NOT found');
    }

    try {
        const data = await apiCall('/bestsellers');
        renderProducts(data || [], 'bestsellers');
        updateCacheStatus('bestsellers', true);
    } catch (error) {
        console.error('Ошибка загрузки бестселлеров:', error);
        updateCacheStatus('bestsellers', false);
        if (container) {
            container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📦</div><div class="empty-state-message">Не удалось загрузить товары</div></div>';
        }
    }
}

// Загрузка рекомендаций
async function loadRecommendations() {
    const container = document.getElementById('recommendations');
    if (container) {
        container.innerHTML = '<div class="loading"></div>';
    }

    try {
        const data = await apiCall('/recommendations');
        renderProducts(data || [], 'recommendations');
        updateCacheStatus('recommendations', true);
    } catch (error) {
        console.error('Ошибка загрузки рекомендаций:', error);
        updateCacheStatus('recommendations', false);
        if (container) {
            container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">💡</div><div class="empty-state-message">Не удалось загрузить рекомендации</div></div>';
        }
    }
}

// Загрузка flash sales
async function loadFlashSales() {
    const container = document.getElementById('flash-sales');
    if (container) {
        container.innerHTML = '<div class="loading"></div>';
    }

    try {
        const data = await apiCall('/flash-sales');
        renderFlashSales(data || []);
        updateCacheStatus('flash-sales', true);
    } catch (error) {
        console.error('Ошибка загрузки flash sales:', error);
        updateCacheStatus('flash-sales', false);
        if (container) {
            container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">⚡</div><div class="empty-state-message">Нет активных акций</div></div>';
        }
    }
}

// Загрузка топ комментариев
async function loadTopComments() {
    try {
        const data = await apiCall('/comments/top');
        renderComments(data || []);
        updateCacheStatus('comments', true);
    } catch (error) {
        console.error('Ошибка загрузки комментариев:', error);
        updateCacheStatus('comments', false);
    }
}

// Загрузка корзины
async function loadCart() {
    try {
        const data = await apiCall('/cart');
        cart = data.items || [];
        updateCartUI();
    } catch (error) {
        console.error('Ошибка загрузки корзины:', error);
    }
}

// Загрузка профиля пользователя
async function loadUserProfile() {
    try {
        const data = await apiCall('/user/profile');
        currentUser = data.user || currentUser;
        updateUserUI();
    } catch (error) {
        console.error('Ошибка загрузки профиля:', error);
    }
}

// Отрисовка товаров
function renderProducts(products, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    if (products.length === 0) {
        container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📦</div><div class="empty-state-message">Нет доступных товаров</div><div class="empty-state-submessage">Попробуйте обновить страницу</div></div>';
        return;
    }

    container.innerHTML = products.map(product => `
        <div class="product-card" onclick="goToProduct(${product.id})">
            <div class="product-image">
                ${product.is_flash_sale ? '<div class="flash-sale-badge">SALE!</div>' : ''}
            </div>
            <div class="product-name">${product.name}</div>
            <div class="product-price">
                ${product.old_price ?
                    `<span class="current-price">${product.price.toLocaleString('ru-RU')}₽</span>
                     <span class="old-price">${product.old_price.toLocaleString('ru-RU')}₽</span>` :
                    `${product.price.toLocaleString('ru-RU')}₽`
                }
            </div>
            <div class="product-actions">
                <button class="add-to-cart-btn" onclick="addToCart(${product.id}, event)">
                    В корзину
                </button>
                <span class="stock-info">${product.stock} шт.</span>
            </div>
        </div>
    `).join('');
}

// Отрисовка flash sales
function renderFlashSales(sales) {
    const container = document.getElementById('flash-sales');
    if (!container) return;

    if (sales.length === 0) {
        container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">⚡</div><div class="empty-state-message">Нет активных акций</div><div class="empty-state-submessage">Следите за обновлениями!</div></div>';
        return;
    }

    container.innerHTML = sales.map(sale => `
        <div class="product-card flash-sale-card" onclick="goToProduct(${sale.id})">
            <div class="flash-sale-badge">FLASH SALE!</div>
            <div class="product-image"></div>
            <div class="product-name">${sale.name || 'Flash Sale Item'}</div>
            <div class="product-price">
                <span class="current-price">${sale.price.toLocaleString('ru-RU')}₽</span>
                <span class="old-price">${sale.old_price ? sale.old_price.toLocaleString('ru-RU') : (sale.price * 1.2).toLocaleString('ru-RU')}₽</span>
            </div>
            <div class="sale-timer">
                Осталось: ${formatTimeLeft(Date.now() + 2 * 60 * 60 * 1000)}
            </div>
            <button class="add-to-cart-btn" onclick="addToCart(${sale.id}, event)">
                Купить сейчас!
            </button>
        </div>
    `).join('');
}

// Отрисовка комментариев
function renderComments(comments) {
    const container = document.getElementById('top-comments');
    if (!container) return;

    container.innerHTML = comments.map(comment => `
        <div class="comment-item">
            <div class="comment-author">${comment.author || 'Anonymous'}</div>
            <div class="comment-rating">${'★'.repeat(comment.rating || 0)}${'☆'.repeat(5-(comment.rating || 0))}</div>
            <div class="comment-text">${comment.text || ''}</div>
        </div>
    `).join('');
}

// Обновление UI пользователя
function updateUserUI() {
    const userNameElement = document.getElementById('user-name');
    const userNameInput = document.getElementById('user-name-input');

    if (userNameElement) {
        userNameElement.textContent = currentUser.name;
    }
    if (userNameInput) {
        userNameInput.value = currentUser.name;
    }
}

// Обновление UI корзины
function updateCartUI() {
    const cartCount = document.getElementById('cart-count');
    const cartItems = document.getElementById('cart-items');
    const cartTotal = document.getElementById('cart-total');

    if (cartCount) {
        cartCount.textContent = cart.reduce((sum, item) => sum + item.quantity, 0);
    }

    if (cartItems) {
        if (cart.length === 0) {
            cartItems.innerHTML = '<div class="empty-cart">Корзина пуста</div>';
        } else {
            cartItems.innerHTML = cart.map(item => `
                <div class="cart-item">
                    <div class="cart-item-info">
                        <div class="cart-item-name">${item.name || 'Товар'}</div>
                        <div class="cart-item-price">${(item.price || 0).toLocaleString('ru-RU')}₽</div>
                    </div>
                    <div class="cart-item-controls">
                        <button class="quantity-btn" onclick="updateCartQuantity(${item.product_id}, ${item.quantity - 1})">-</button>
                        <span class="quantity">${item.quantity || 0}</span>
                        <button class="quantity-btn" onclick="updateCartQuantity(${item.product_id}, ${item.quantity + 1})">+</button>
                        <button class="remove-btn" onclick="removeFromCart(${item.product_id})">Удалить</button>
                    </div>
                </div>
            `).join('');
        }
    }

    if (cartTotal) {
        const total = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
        cartTotal.textContent = total.toLocaleString('ru-RU');
    }
}

// Добавление в корзину
async function addToCart(productId, event) {
    if (event) {
        event.stopPropagation();
    }

    try {
        await apiCall(`/cart/add/${productId}`, { method: 'POST' });
        showNotification('Товар добавлен в корзину', 'success');
        loadCart();
    } catch (error) {
        console.error('Ошибка добавления в корзину:', error);
    }
}

// Обновление количества в корзине
async function updateCartQuantity(productId, newQuantity) {
    if (newQuantity <= 0) {
        removeFromCart(productId);
        return;
    }

    try {
        await apiCall(`/cart/update/${productId}`, {
            method: 'PUT',
            body: JSON.stringify({ quantity: newQuantity })
        });
        loadCart();
    } catch (error) {
        console.error('Ошибка обновления корзины:', error);
    }
}

// Удаление из корзины
async function removeFromCart(productId) {
    try {
        await apiCall(`/cart/remove/${productId}`, { method: 'DELETE' });
        showNotification('Товар удален из корзины', 'info');
        loadCart();
    } catch (error) {
        console.error('Ошибка удаления из корзины:', error);
    }
}

// Обновление профиля
async function updateProfile() {
    const nameInput = document.getElementById('user-name-input');
    if (!nameInput) return;

    const newName = nameInput.value.trim();
    if (!newName) {
        showNotification('Введите имя пользователя', 'error');
        return;
    }

    try {
        await apiCall('/user/profile', {
            method: 'PUT',
            body: JSON.stringify({ name: newName })
        });
        showNotification('Профиль обновлен', 'success');
        loadUserProfile();
    } catch (error) {
        console.error('Ошибка обновления профиля:', error);
    }
}

// Инвалидация кэша
async function invalidateCache(cacheType) {
    console.log('invalidateCache called with:', cacheType);
    try {
        const result = await apiCall(`/cache/invalidate/${cacheType}`, { method: 'POST' });
        console.log('Cache invalidation result:', result);
        // Показываем локальное уведомление для отладки
        showNotification(`Кэш "${cacheType}" инвалидирован`, 'success');

        // Перезагружаем соответствующие данные
        switch(cacheType) {
            case 'bestsellers':
                loadBestsellers();
                break;
            case 'recommendations':
                loadRecommendations();
                break;
            case 'flash-sales':
                loadFlashSales();
                break;
            case 'all':
                loadAllData();
                break;
        }
    } catch (error) {
        console.error('Ошибка инвалидации кэша:', error);
        showNotification(`Ошибка инвалидации кэша: ${error.message}`, 'error');
    }
}

// Получение статуса кэша
async function getCacheStatus() {
    try {
        const data = await apiCall('/cache/status');
        showCacheStatus(data);
    } catch (error) {
        console.error('Ошибка получения статуса кэша:', error);
    }
}

// Отображение статуса кэша
function showCacheStatus(status) {
    const statusPanel = document.getElementById('cache-status');
    if (!statusPanel) return;

    const bestsellersStatus = status.bestsellers && status.bestsellers.exists ? '✅' : '❌';
    const flashSalesStatus = status.flash_sales && status.flash_sales.exists ? '✅' : '❌';
    const commentsStatus = status.top_comments && status.top_comments.exists ? '✅' : '❌';
    const recommendationsCount = status.recommendations ? status.recommendations.count : 0;

    statusPanel.innerHTML = `
        <div>Bestsellers: ${bestsellersStatus}</div>
        <div>Flash Sales: ${flashSalesStatus}</div>
        <div>Comments: ${commentsStatus}</div>
        <div>Recommendations: ${recommendationsCount} пользователей</div>
    `;
}

// Обновление статуса кэша
function updateCacheStatus(cacheType, isActive) {
    const indicators = document.querySelectorAll(`.${cacheType}-indicator`);
    indicators.forEach(indicator => {
        indicator.style.opacity = isActive ? '1' : '0.5';
    });
}

// Обновление данных по типу кэша
function refreshData(cacheType) {
    switch (cacheType) {
        case 'bestsellers':
            loadBestsellers();
            break;
        case 'recommendations':
            loadRecommendations();
            break;
        case 'flash-sales':
            loadFlashSales();
            break;
        case 'profile':
            loadUserProfile();
            break;
    }
}

// Переход на страницу товара
function goToProduct(productId) {
    window.location.href = `/product/${productId}`;
}

// Переключение корзины
function toggleCart() {
    const modal = document.getElementById('cart-modal');
    if (modal) {
        modal.classList.toggle('active');
    }
}

// Переключение профиля
function toggleProfile() {
    const panel = document.getElementById('user-panel');
    if (panel) {
        // Если стиль не установлен, считаем что панель видна (по умолчанию)
        const isHidden = panel.style.display === 'none';
        panel.style.display = isHidden ? 'block' : 'none';
    }
}

// Показ уведомлений
function showNotification(message, type = 'info') {
    const container = document.getElementById('notifications');
    if (!container) return;

    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;

    container.appendChild(notification);

    // Автоматическое удаление через 5 секунд
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 5000);
}

// Форматирование оставшегося времени
function formatTimeLeft(endTime) {
    const now = new Date();
    const end = new Date(endTime);
    const diff = end - now;

    if (diff <= 0) return 'Завершено';

    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

    return `${hours}ч ${minutes}м`;
}

// Настройка обработчиков событий
function setupEventListeners() {
    // Закрытие модальных окон по клику вне их
    document.addEventListener('click', function(event) {
        const cartModal = document.getElementById('cart-modal');
        if (cartModal && cartModal.classList.contains('active')) {
            if (event.target === cartModal) {
                toggleCart();
            }
        }
    });

    // Обработка поиска
    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(event) {
            if (event.key === 'Enter') {
                performSearch(this.value);
            }
        });
    }

    const searchBtn = document.querySelector('.search-btn');
    if (searchBtn) {
        searchBtn.addEventListener('click', function() {
            const searchInput = document.querySelector('.search-input');
            if (searchInput) {
                performSearch(searchInput.value);
            }
        });
    }
}

// Выполнение поиска
async function performSearch(query) {
    if (!query.trim()) return;

    try {
        const data = await apiCall(`/search?q=${encodeURIComponent(query)}`);
        // Отображение результатов поиска
        showSearchResults(data.results || []);
    } catch (error) {
        console.error('Ошибка поиска:', error);
    }
}

// Отображение результатов поиска
function showSearchResults(results) {
    // Реализация отображения результатов поиска
    console.log('Результаты поиска:', results);
}

// Инициализация домашней страницы
function initHomePage() {
    console.log('Инициализация домашней страницы');
}

// Инициализация страницы товара
function initProductPage() {
    const productId = window.location.pathname.split('/').pop();
    loadProductDetails(productId);
}

// Инициализация страницы профиля
function initProfilePage() {
    console.log('Инициализация страницы профиля');
}

// Загрузка деталей товара
async function loadProductDetails(productId) {
    try {
        const data = await apiCall(`/product/${productId}`);
        renderProductDetails(data);
    } catch (error) {
        console.error('Ошибка загрузки товара:', error);
    }
}

// Отрисовка деталей товара
function renderProductDetails(product) {
    console.log('Детали товара:', product);

    // Сохраняем продукт для других функций
    window.currentProduct = product;

    // Обновляем заголовок страницы
    document.title = `${product.name} - ТЕХНОМИР`;

    // Обновляем breadcrumb
    const categoryEl = document.getElementById('product-category');
    const breadcrumbEl = document.getElementById('product-breadcrumb');
    if (categoryEl) categoryEl.textContent = product.category || 'Категория';
    if (breadcrumbEl) breadcrumbEl.textContent = product.name || 'Товар';

    // Обновляем информацию о товаре
    const nameEl = document.getElementById('product-name');
    if (nameEl) nameEl.textContent = product.name || 'Название не указано';

    const brandEl = document.getElementById('product-brand');
    if (brandEl) brandEl.textContent = product.brand || '';

    const descEl = document.getElementById('product-description');
    const fullDescEl = document.getElementById('full-description');
    if (descEl) descEl.textContent = product.description || '';
    if (fullDescEl) fullDescEl.textContent = product.description || 'Описание отсутствует';

    // Обновляем цену
    const priceEl = document.getElementById('product-price');
    if (priceEl) {
        if (product.old_price) {
            priceEl.innerHTML = `
                <span class="current-price">${product.price.toLocaleString('ru-RU')} ₽</span>
                <span class="old-price">${product.old_price.toLocaleString('ru-RU')} ₽</span>
                <span class="discount">-${Math.round((1 - product.price/product.old_price) * 100)}%</span>
            `;
        } else {
            priceEl.innerHTML = `<span class="current-price">${product.price.toLocaleString('ru-RU')} ₽</span>`;
        }
    }

    // Обновляем наличие
    const stockEl = document.getElementById('product-stock');
    if (stockEl) {
        if (product.stock > 0) {
            stockEl.innerHTML = `<span class="in-stock">✓ В наличии (${product.stock} шт.)</span>`;
        } else {
            stockEl.innerHTML = `<span class="out-of-stock">✗ Нет в наличии</span>`;
        }
    }

    // Обновляем характеристики
    const specsTable = document.getElementById('specs-table');
    if (specsTable) {
        specsTable.innerHTML = `
            <tr><td>Бренд</td><td>${product.brand || 'Не указан'}</td></tr>
            <tr><td>Категория</td><td>${product.category || 'Не указана'}</td></tr>
            <tr><td>Артикул</td><td>ID-${product.id}</td></tr>
            ${product.is_bestseller ? '<tr><td>Статус</td><td>🔥 Бестселлер</td></tr>' : ''}
            ${product.is_flash_sale ? '<tr><td>Акция</td><td>⚡ Flash Sale</td></tr>' : ''}
        `;
    }
}

// Очистка при закрытии страницы
window.addEventListener('beforeunload', function() {
    // Закрываем WebSocket
    if (ws) {
        ws.close();
    }

    // Очищаем интервалы поллинга
    Object.values(pollingIntervals).forEach(interval => {
        clearInterval(interval);
    });
});