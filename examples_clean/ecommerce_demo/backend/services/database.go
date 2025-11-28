package services

import (
	"fmt"
	"log"

	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"

	"ecommerce-backend/models"
)

type DatabaseService struct {
	DB *gorm.DB
}

func NewDatabaseService(host, user, password, dbname string, port int) (*DatabaseService, error) {
	dsn := fmt.Sprintf("host=%s user=%s password=%s dbname=%s port=%d sslmode=disable TimeZone=UTC",
		host, user, password, dbname, port)

	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{
		Logger: logger.Default.LogMode(logger.Info),
	})
	if err != nil {
		return nil, fmt.Errorf("failed to connect to database: %v", err)
	}

	return &DatabaseService{DB: db}, nil
}

func (ds *DatabaseService) AutoMigrate() error {
	return ds.DB.AutoMigrate(&models.Product{}, &models.User{}, &models.Comment{}, &models.Cart{})
}

func (ds *DatabaseService) SeedData() error {
	// Check if data already exists
	var count int64
	ds.DB.Model(&models.Product{}).Count(&count)
	if count > 0 {
		log.Println("Data already exists, skipping seed")
		return nil
	}

	// Create users
	users := []models.User{
		{Name: "Alice Johnson", Email: "alice@example.com"},
		{Name: "Bob Smith", Email: "bob@example.com"},
		{Name: "Charlie Brown", Email: "charlie@example.com"},
		{Name: "Diana Prince", Email: "diana@example.com"},
		{Name: "Eve Wilson", Email: "eve@example.com"},
	}

	for _, user := range users {
		if err := ds.DB.Create(&user).Error; err != nil {
			return err
		}
	}

	// Create products - АКТУАЛЬНЫЕ МОДЕЛИ 2025
	products := []models.Product{
		// Флагманские смартфоны 2025
		{Name: "iPhone 17 Pro Max", Description: "Революционный флагман с A19 Pro, улучшенный Dynamic Island 2.0", Price: 169900, OldPrice: &[]float64{179900}[0], Brand: "Apple", Category: "Smartphones", IsBestseller: true, Stock: 45},
		{Name: "iPhone 17 Pro", Description: "Компактный флагман с ProMotion 144Hz и титановым корпусом 2-го поколения", Price: 149900, Brand: "Apple", Category: "Smartphones", IsBestseller: true, Stock: 60},
		{Name: "iPhone 17", Description: "Базовая модель с A19 Bionic и перископической камерой", Price: 109900, Brand: "Apple", Category: "Smartphones", IsBestseller: false, Stock: 80},
		{Name: "Samsung Galaxy S25 Ultra", Description: "Флагман с S Pen, 250MP камерой и Snapdragon 8 Gen 4", Price: 154900, OldPrice: &[]float64{164900}[0], Brand: "Samsung", Category: "Smartphones", IsBestseller: true, IsFlashSale: true, Stock: 35},
		{Name: "Samsung Galaxy S25+", Description: "Премиум смартфон с усовершенствованным Galaxy AI 2.0", Price: 119900, Brand: "Samsung", Category: "Smartphones", IsBestseller: false, Stock: 40},
		{Name: "Samsung Galaxy S25", Description: "Компактный флагман с Dynamic AMOLED 3X и 144Hz", Price: 94900, Brand: "Samsung", Category: "Smartphones", IsBestseller: false, Stock: 50},

		// Среднебюджетные смартфоны 2025
		{Name: "Samsung Galaxy A56", Description: "Среднебюджетный хит с 144Hz AMOLED экраном", Price: 44900, Brand: "Samsung", Category: "Smartphones", IsBestseller: true, Stock: 100},
		{Name: "Xiaomi 15 Pro", Description: "Флагман с Leica камерами 2.0 и Snapdragon 8 Gen 4", Price: 99900, Brand: "Xiaomi", Category: "Smartphones", IsBestseller: false, Stock: 30},
		{Name: "Google Pixel 9 Pro", Description: "Революционная AI камера и Android 15", Price: 114900, OldPrice: &[]float64{119900}[0], Brand: "Google", Category: "Smartphones", IsBestseller: false, IsFlashSale: true, Stock: 25},
		{Name: "OnePlus 13", Description: "Флагман-убийца с Hasselblad камерами 3-го поколения", Price: 89900, Brand: "OnePlus", Category: "Smartphones", IsBestseller: false, Stock: 35},

		// Ноутбуки 2025
		{Name: "MacBook Pro 16 M4 Max", Description: "Революционный ноутбук с M4 Max и 3nm процессом", Price: 429900, Brand: "Apple", Category: "Laptops", IsBestseller: true, Stock: 15},
		{Name: "MacBook Air 15 M4", Description: "Ультралегкий с M4 и батареей на 24 часа", Price: 179900, Brand: "Apple", Category: "Laptops", IsBestseller: true, Stock: 30},
		{Name: "MacBook Air 13 M3", Description: "Компактный ноутбук с M3 для учебы и работы", Price: 139900, OldPrice: &[]float64{149900}[0], Brand: "Apple", Category: "Laptops", IsBestseller: false, IsFlashSale: true, Stock: 40},

		// Планшеты 2025
		{Name: "iPad Pro 13 M5", Description: "Профессиональный планшет с OLED 2.0 и M5", Price: 169900, Brand: "Apple", Category: "Tablets", IsBestseller: true, Stock: 20},
		{Name: "iPad Air M3", Description: "Универсальный планшет с M3 процессором", Price: 84900, Brand: "Apple", Category: "Tablets", IsBestseller: false, Stock: 35},
		{Name: "Samsung Galaxy Tab S10 Ultra", Description: "Гигантский Android планшет с S Pen Pro", Price: 139900, Brand: "Samsung", Category: "Tablets", IsBestseller: false, Stock: 15},

		// Аудио 2025
		{Name: "AirPods Pro 3", Description: "Революционные наушники с H3 чипом и Lossless Audio", Price: 34900, OldPrice: &[]float64{39900}[0], Brand: "Apple", Category: "Audio", IsBestseller: true, IsFlashSale: true, Stock: 150},
		{Name: "Sony WH-1000XM6", Description: "Эталон шумоподавления с AI адаптацией", Price: 44900, Brand: "Sony", Category: "Audio", IsBestseller: false, Stock: 45},
		{Name: "Samsung Galaxy Buds4 Pro", Description: "TWS с Galaxy AI 2.0 и адаптивным ANC", Price: 29900, Brand: "Samsung", Category: "Audio", IsBestseller: false, Stock: 60},

		// Умные часы 2025
		{Name: "Apple Watch Ultra 3", Description: "Титановые часы для экстрима с microLED экраном", Price: 109900, Brand: "Apple", Category: "Wearables", IsBestseller: true, Stock: 25},
		{Name: "Apple Watch Series 10", Description: "Юбилейная модель с чипом S10 и глюкометром", Price: 59900, Brand: "Apple", Category: "Wearables", IsBestseller: false, Stock: 50},
		{Name: "Samsung Galaxy Watch 7 Ultra", Description: "Премиум часы с титановым корпусом", Price: 49900, OldPrice: &[]float64{54900}[0], Brand: "Samsung", Category: "Wearables", IsBestseller: false, IsFlashSale: true, Stock: 30},
	}

	for _, product := range products {
		if err := ds.DB.Create(&product).Error; err != nil {
			return err
		}
	}

	// Create comments
	comments := []models.Comment{
		{ProductID: 1, UserID: 1, Author: "Alice Johnson", Text: "Отличный телефон, очень доволен покупкой!", Rating: 5},
		{ProductID: 1, UserID: 2, Author: "Bob Smith", Text: "Камера просто супер, рекомендую!", Rating: 5},
		{ProductID: 2, UserID: 3, Author: "Charlie Brown", Text: "Хороший Android, но дорого", Rating: 4},
		{ProductID: 3, UserID: 4, Author: "Diana Prince", Text: "Мощный ноутбук для работы", Rating: 5},
		{ProductID: 4, UserID: 5, Author: "Eve Wilson", Text: "Звук отличный, но быстро разряжается", Rating: 4},
		{ProductID: 5, UserID: 1, Author: "Alice Johnson", Text: "Лучшие наушники для путешествий", Rating: 5},
		{ProductID: 6, UserID: 2, Author: "Bob Smith", Text: "Удобный планшет для чтения", Rating: 4},
		{ProductID: 7, UserID: 3, Author: "Charlie Brown", Text: "Хорошая альтернатива iPad", Rating: 4},
	}

	for _, comment := range comments {
		if err := ds.DB.Create(&comment).Error; err != nil {
			return err
		}
	}

	log.Println("Database seeded successfully")
	return nil
}

func (ds *DatabaseService) GetBestsellers() ([]models.Product, error) {
	var products []models.Product
	err := ds.DB.Where("is_bestseller = ?", true).Find(&products).Error
	return products, err
}

func (ds *DatabaseService) GetRecommendations(userID uint, limit int) ([]models.Product, error) {
	var products []models.Product

	// Simple recommendation: get random products not marked as bestsellers
	err := ds.DB.Where("is_bestseller = ?", false).Order("RANDOM()").Limit(limit).Find(&products).Error
	return products, err
}

func (ds *DatabaseService) GetFlashSales() ([]models.Product, error) {
	var products []models.Product
	err := ds.DB.Where("is_flash_sale = ?", true).Find(&products).Error
	return products, err
}

func (ds *DatabaseService) GetTopComments(limit int) ([]models.Comment, error) {
	var comments []models.Comment
	err := ds.DB.Preload("Product").Preload("User").Order("rating DESC, created_at DESC").Limit(limit).Find(&comments).Error
	return comments, err
}

func (ds *DatabaseService) GetProduct(id uint) (*models.Product, error) {
	var product models.Product
	err := ds.DB.First(&product, id).Error
	if err != nil {
		return nil, err
	}
	return &product, nil
}

func (ds *DatabaseService) GetUser(id uint) (*models.User, error) {
	var user models.User
	err := ds.DB.First(&user, id).Error
	if err != nil {
		return nil, err
	}
	return &user, nil
}

func (ds *DatabaseService) UpdateUser(id uint, name string) error {
	return ds.DB.Model(&models.User{}).Where("id = ?", id).Update("name", name).Error
}

func (ds *DatabaseService) GetCartItems(userID uint) ([]models.CartItem, error) {
	var cartItems []models.Cart
	err := ds.DB.Preload("Product").Where("user_id = ?", userID).Find(&cartItems).Error
	if err != nil {
		return nil, err
	}

	var items []models.CartItem
	for _, cart := range cartItems {
		item := models.CartItem{
			ProductID: cart.ProductID,
			Name:      cart.Product.Name,
			Price:     cart.Product.Price,
			Quantity:  cart.Quantity,
			Total:     cart.Product.Price * float64(cart.Quantity),
		}
		items = append(items, item)
	}

	return items, nil
}

func (ds *DatabaseService) AddToCart(userID, productID uint, quantity int) error {
	var cart models.Cart
	err := ds.DB.Where("user_id = ? AND product_id = ?", userID, productID).First(&cart).Error

	if err == gorm.ErrRecordNotFound {
		// Create new cart item
		cart = models.Cart{
			UserID:    userID,
			ProductID: productID,
			Quantity:  quantity,
		}
		return ds.DB.Create(&cart).Error
	} else if err != nil {
		return err
	} else {
		// Update existing cart item
		cart.Quantity += quantity
		return ds.DB.Save(&cart).Error
	}
}

func (ds *DatabaseService) UpdateCartItem(userID, productID uint, quantity int) error {
	if quantity <= 0 {
		return ds.RemoveFromCart(userID, productID)
	}

	return ds.DB.Model(&models.Cart{}).
		Where("user_id = ? AND product_id = ?", userID, productID).
		Update("quantity", quantity).Error
}

func (ds *DatabaseService) RemoveFromCart(userID, productID uint) error {
	return ds.DB.Where("user_id = ? AND product_id = ?", userID, productID).Delete(&models.Cart{}).Error
}

func (ds *DatabaseService) GetCartTotal(userID uint) (float64, int, error) {
	items, err := ds.GetCartItems(userID)
	if err != nil {
		return 0, 0, err
	}

	var total float64
	var count int
	for _, item := range items {
		total += item.Total
		count += item.Quantity
	}

	return total, count, nil
}