# E-Commerce Multi-Tenant Application

A multi-tenant e-commerce application built using FastAPI, React, SQLite, SQLAlchemy and Keycloak authentication.

## Features

### Authentication & Authorization
- User signup and login using Keycloak
- Role-based access control
- Three roles:
  - Admin
  - Tenant
  - User
- Unique usernames

### Admin
- Create and delete tenants/brands
- Create and delete users
- Manage tenant users
- Manage application roles

### Tenant
- Manage products belonging to their own brand
- Create products
- Update products
- Delete products
- Update product stock
- View their own products

### Customer
- View products
- Search products by name
- Filter products by category
- Pagination
- Add products to cart
- Place orders
- View order history

### Orders
- Order contains products and quantities
- Total quantity calculated automatically
- Total amount calculated automatically
- Product stock is reduced after successful order
- Orders cannot be created when requested quantity is greater than or equal to available stock

### Multi-Tenancy
Products and tenant users are associated with their respective brands/tenants.

Tenant-specific product endpoints are supported using tenant names.

## Technology Stack

### Backend
- Python
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic
- JWT authentication

### Frontend
- React
- Vite
- JavaScript
- CSS

### Authentication
- Keycloak
- OpenID Connect

### Testing
- Pytest
- FastAPI TestClient

## Project Structure

```text
ecommerce_tenant/
│
├── backend/
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── database.py
│   ├── auth.py
│   ├── keycloak_admin.py
│   ├── ecommerce.db
│   └── tests/
│       └── test_api.py
│
├── frontend/
│   └── React application
│
├── keycloak/
│   └── docker-compose.yml
│
├── .gitignore
└── README.md
