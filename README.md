# E-Commerce Backend System - Django REST Framework

### Step 1: User Management:
- User Registration & Authentication
- JWT Token-based Authentication
- User Profile Management
- Password Change Functionality
- Admin & Customer Role Management
- Complete Test Suite

## Step 2: Product Management (Coming Next)
- Product CRUD operations
- Category management with hierarchical structure
- Stock management
- Product search and filtering
- Admin-only product management

### Step 3: Order Management
- Create orders
- Order items management
- Order status tracking
- Calculate totals and subtotals

### Step 4: Payment System
- Stripe integration
- bKash integration
- Payment webhooks
- Strategy pattern implementation

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose 

### Installation (Local Setup)

#### 1. Clone & Setup Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```
#### 2. Database Setup
```bash
# Create PostgreSQL database
createdb ecommerce_db

# Or using psql:
psql -U postgres
CREATE DATABASE ecommerce_db;
\q
```
#### 3. Environment Configuration
```bash
# Copy .env.example to .env
cp .env.example .env

# Edit .env file with your credentials
# Important: Update SECRET_KEY, DB credentials, and API keys
```
#### 4. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

#### 5. Create Superuser
```bash
python manage.py createsuperuser
# Enter: email, first name, last name, password
```
#### 6. Run Development Server
```bash
python manage.py runserver
```
Server will start at: `http://localhost:8000`
---


## 🐳 Docker Setup

### Run with Docker Compose
```bash
# Build and start all services
docker-compose up --build

# Run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```
### Create Superuser in Docker
```bash
docker-compose exec backend python manage.py createsuperuser
```


---


## 📚 API Documentation

### Access API Documentation
Once the server is running:
- **Swagger UI**: http://localhost:8000/swagger/
- **ReDoc**: http://localhost:8000/redoc/
- **JSON Schema**: http://localhost:8000/swagger.json
---


## 🔐 API Endpoints (Step 1: User Management)

#### 1. Register User
```
Register: POST /api/users/register/
```
#### 2. Login User
```
POST /api/users/login/
```
#### 3. Refresh Token
```
POST /api/users/token/refresh/
```
#### 4. Logout User
```
POST /api/users/logout/
```
#### 5. Get Profile
```
GET /api/users/profile/
```
#### 6. Update Profile
```
PATCH /api/users/profile/
```
#### 7. Change Password
```
POST /api/users/change-password/
```

## 🔐 API Endpoints ( Product Management )

### **Category Endpoints:**
```
GET  /api/categories/              # List all
GET  /api/categories/tree/         # Full tree (DFS) 
GET  /api/categories/roots/        # Root categories
GET  /api/categories/{slug}/       # Category detail
GET  /api/categories/{slug}/descendants/  # DFS descendants 
GET  /api/categories/{slug}/products/     # All products in tree
POST /api/categories/              # Create (Admin)
```
### **Product Endpoints:**
```
GET  /api/products/                # List all
GET  /api/products/search/         # Search with filters 
GET  /api/products/{slug}/         # Product detail (cached)
GET  /api/products/{slug}/related/ # Related products (DFS) 
POST /api/products/{slug}/update_stock/  # Stock management
POST /api/products/  
```


 ## 🔐 API Endpoints ( Order Management )
### **Customer Endpoints:**
```
POST   /api/orders/                    # Create order 
GET    /api/orders/my_orders/          # My orders list
GET    /api/orders/{id}/               # Order detail
PATCH  /api/orders/{id}/               # Update (pending only)
POST   /api/orders/{id}/cancel/        # Cancel order
GET    /api/orders/{id}/history/       # Status history
PATCH  /api/orders/{id}/items/{item_id}/  # Update item qty
```
### **Admin Endpoints:**
```
GET    /api/orders/                    # All orders
POST   /api/orders/{id}/update_status/ # Update status 
GET    /api/orders/summary/            # Order statistics 
+ All customer endpoints
```

## 🔐 API Endpoints ( Payment Management )

| Method | Endpoint | Description |
|------|--------|------------|
| GET | /api/payments/ | List payments |
| POST | /api/payments/ | Create payment |
| GET | /api/payments/{id}/ | Payment details |
| PUT | /api/payments/{id}/ | Update payment |
| PATCH | /api/payments/{id}/ | Partial update |
| DELETE | /api/payments/{id}/ | Delete payment |
| POST | /api/payments/{id}/initiate/ | Initiate payment |
| POST | /api/payments/{id}/execute/ | Execute payment |
| POST | /api/payments/webhook/{provider}/ | Payment webhook |

---



### Authentication Endpoints

#### 1. Register User
```http
POST /api/users/register/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "01712345678"
}
```

**Response:**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "customer"
  },
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

#### 2. Login User
```http
POST /api/users/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

#### 3. Refresh Token
```http
POST /api/users/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### 4. Logout User
```http
POST /api/users/logout/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Profile Management Endpoints

#### 5. Get Profile
```http
GET /api/users/profile/
Authorization: Bearer {access_token}
```

#### 6. Update Profile
```http
PATCH /api/users/profile/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "first_name": "Updated",
  "last_name": "Name",
  "phone": "01812345678",
  "profile": {
    "address_line_1": "123 Main St",
    "city": "Dhaka",
    "country": "Bangladesh"
  }
}
```

#### 7. Change Password
```http
POST /api/users/change-password/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "old_password": "OldPass123!",
  "new_password": "NewPass123!",
  "new_password_confirm": "NewPass123!"
}
```




---

##  Running Tests

### Run All Tests
```bash
# Run all tests
python manage.py test

# Run with coverage
pytest --cov=apps

# Run specific app tests
python manage.py test apps.users
```

### Test Coverage
```bash
# Install coverage
pip install coverage

# Run tests with coverage
coverage run --source='apps' manage.py test
coverage report
coverage html  # Generate HTML report
```

---

## 📁 Project Structure

```
ecommerce_backend/
├── manage.py (Django creates)
├── requirements.txt 
├── .env.example 
├── .gitignore 
├── docker-compose.yml 
├── Dockerfile 
│
├── config/
│   ├── __init__.py (Django creates)
│   ├── settings.py
│   ├── urls.py 
│   ├── wsgi.py (keep)
│   └── asgi.py (keep)
│
├── apps/
│   ├── __init__.py 
│   └── users/
│       ├── __init__.py 
│       ├── apps.py 
│       ├── models.py 
│       ├── serializers.py 
│       ├── views.py 
│       ├── urls.py 
│       ├── admin.py 
│       ├── permissions.py 
│       ├── tests.py 
│       └── management/
│           ├── __init__.py 
│           └── commands/
│               ├── __init__.py 
│               └── seed_users.py 
│
├── utils/
│   ├── __init__.py 
│   └── exceptions.py 
│
└── logs/ (create empty folder)
```

---

## Development Commands

```bash
# Create new app
python manage.py startapp app_name

# Make migrations
python manage.py makemigrations

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver

# Open Django shell
python manage.py shell

# Run tests
python manage.py test
```

---
---

## Common Issues & Solutions

### Issue: Database connection error
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check connection
psql -U postgres -h localhost
```

### Issue: Redis connection error
```bash
# Check Redis is running
redis-cli ping
# Should return: PONG
```

### Issue: Port already in use
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

---

## 📧 Contact & Support

For questions or issues, please contact mh1445156@gmail.com.

---
