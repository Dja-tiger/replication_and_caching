package models

import (
	"time"
)

type Product struct {
	ID          uint   `json:"id" gorm:"primaryKey"`
	Name        string `json:"name"`
	Description string `json:"description"`
	Price       float64 `json:"price"`
	OldPrice    *float64 `json:"old_price,omitempty"`
	Brand       string `json:"brand"`
	Category    string `json:"category"`
	IsBestseller bool  `json:"is_bestseller"`
	IsFlashSale  bool  `json:"is_flash_sale"`
	Stock       int   `json:"stock"`
	CreatedAt   time.Time `json:"created_at"`
	UpdatedAt   time.Time `json:"updated_at"`
}

type User struct {
	ID        uint      `json:"id" gorm:"primaryKey"`
	Name      string    `json:"name"`
	Email     string    `json:"email" gorm:"unique"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}

type Comment struct {
	ID        uint      `json:"id" gorm:"primaryKey"`
	ProductID uint      `json:"product_id"`
	UserID    uint      `json:"user_id"`
	Author    string    `json:"author"`
	Text      string    `json:"text"`
	Rating    int       `json:"rating"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`

	Product Product `json:"product" gorm:"foreignKey:ProductID"`
	User    User    `json:"user" gorm:"foreignKey:UserID"`
}

type Cart struct {
	ID        uint      `json:"id" gorm:"primaryKey"`
	UserID    uint      `json:"user_id"`
	ProductID uint      `json:"product_id"`
	Quantity  int       `json:"quantity"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`

	Product Product `json:"product" gorm:"foreignKey:ProductID"`
	User    User    `json:"user" gorm:"foreignKey:UserID"`
}

type CartItem struct {
	ProductID uint    `json:"product_id"`
	Name      string  `json:"name"`
	Price     float64 `json:"price"`
	Quantity  int     `json:"quantity"`
	Total     float64 `json:"total"`
}

type CartResponse struct {
	Items []CartItem `json:"items"`
	Total float64    `json:"total"`
	Count int        `json:"count"`
}

type WSMessage struct {
	Type string      `json:"type"`
	Data interface{} `json:"data"`
}

type CacheInvalidationRequest struct {
	CacheType string `json:"cache_type"`
}

type UpdateProfileRequest struct {
	Name string `json:"name"`
}

type AddToCartRequest struct {
	ProductID uint `json:"product_id"`
	Quantity  int  `json:"quantity"`
}

type UpdateCartRequest struct {
	ProductID uint `json:"product_id"`
	Quantity  int  `json:"quantity"`
}

type RemoveFromCartRequest struct {
	ProductID uint `json:"product_id"`
}