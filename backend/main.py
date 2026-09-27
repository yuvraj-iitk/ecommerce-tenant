from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from auth import get_current_user, require_role
from keycloak_admin import create_keycloak_user, delete_keycloak_user

from database import engine, Base, SessionLocal
from models import Tenant, Role, User, Product, Order, OrderItem

from schemas import (
    TenantCreate,
    RoleCreate,
    UserCreate,
    SignupCreate,
    ProductCreate,
    OrderCreate,
    OrderResponse,
    MyOrderCreate
)


# =========================
# DATABASE
# =========================

Base.metadata.create_all(bind=engine)


# =========================
# FASTAPI APP
# =========================

app = FastAPI()


# =========================
# CORS
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# DATABASE SESSION
# =========================

def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# =========================
# HOME
# =========================

@app.get("/")
def home():
    return {
        "message": "E-commerce API is working"
    }


# =========================================================
# TENANTS
# =========================================================

# ADMIN ONLY
# Create a new tenant / brand

@app.post("/tenants")
def create_tenant(
    tenant: TenantCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin"))
):
    # Check duplicate tenant
    existing_tenant = db.query(Tenant).filter(
        Tenant.name == tenant.name
    ).first()

    if existing_tenant:
        raise HTTPException(
            status_code=400,
            detail="Tenant already exists"
        )

    new_tenant = Tenant(
        name=tenant.name
    )

    db.add(new_tenant)
    db.commit()
    db.refresh(new_tenant)

    return new_tenant


# Get all tenants

@app.get("/tenants")
def get_tenants(
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin"))
):
    return db.query(Tenant).all()


# ADMIN ONLY
# Delete tenant / brand
# Deletes tenant users, their orders, order items,
# products and finally the tenant.

@app.delete("/tenants/{tenant_id}")
def delete_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin"))
):
    # 1. Find tenant
    tenant = db.query(Tenant).filter(
        Tenant.id == tenant_id
    ).first()

    if not tenant:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found"
        )

    # 2. Find all users belonging to this tenant
    users = db.query(User).filter(
        User.tenant_id == tenant_id
    ).all()

    # 3. Delete tenant users from Keycloak and local database
    for user in users:

        # Don't delete admin users accidentally
        role = db.query(Role).filter(
            Role.id == user.role_id
        ).first()

        if role and role.name == "admin":
            continue

        try:
            delete_keycloak_user(user.username)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Could not delete Keycloak user {user.username}: {str(e)}"
            )

        # Find user's orders
        orders = db.query(Order).filter(
            Order.user_id == user.id
        ).all()

        # Delete order items first
        for order in orders:
            db.query(OrderItem).filter(
                OrderItem.order_id == order.id
            ).delete(
                synchronize_session=False
            )

        # Delete orders
        db.query(Order).filter(
            Order.user_id == user.id
        ).delete(
            synchronize_session=False
        )

        # Delete local user
        db.delete(user)

    # 4. Delete all products of this tenant
    db.query(Product).filter(
        Product.tenant_id == tenant_id
    ).delete(
        synchronize_session=False
    )

    # 5. Delete tenant
    db.delete(tenant)

    db.commit()

    return {
        "message": "Tenant deleted successfully",
        "tenant_id": tenant_id
    }

# =========================================================
# ROLES
# =========================================================

# ADMIN ONLY

@app.post("/roles")
def create_role(
    r: RoleCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin"))
):
    existing_role = db.query(Role).filter(
        Role.name == r.name
    ).first()

    if existing_role:
        raise HTTPException(
            status_code=400,
            detail="Role already exists"
        )

    x = Role(
        name=r.name
    )

    db.add(x)
    db.commit()
    db.refresh(x)

    return x


# ADMIN ONLY

@app.get("/roles")
def get_roles(
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin"))
):
    return db.query(Role).all()


# =========================================================
# PUBLIC SIGNUP
# =========================================================

@app.post("/signup")
def signup(
    data: SignupCreate,
    db: Session = Depends(get_db)
):
    # Check username already exists locally
    existing_user = db.query(User).filter(
        User.username == data.username
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    # Get normal user role
    user_role = db.query(Role).filter(
        Role.name == "user"
    ).first()

    if not user_role:
        raise HTTPException(
            status_code=500,
            detail="User role not found"
        )

    # Create user in Keycloak
    try:
        create_keycloak_user(
            data.username,
            data.password,
            "user"
        )

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    # Create user in local database
    new_user = User(
        username=data.username,
        tenant_id=None,
        role_id=user_role.id
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "Signup successful",
        "username": new_user.username
    }

# =========================================================
# USERS
# =========================================================

# ADMIN ONLY
# Admin creates tenant users / normal users

@app.post("/users")
def create_user(
    u: UserCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin"))
):
    # 1. Check username already exists locally

    existing_user = db.query(User).filter(
        User.username == u.username
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    # 2. Check role

    role = db.query(Role).filter(
        Role.id == u.role_id
    ).first()

    if not role:
        raise HTTPException(
            status_code=404,
            detail="Role not found"
        )

    # 3. Tenant user must have tenant

    if role.name == "tenant" and u.tenant_id is None:
        raise HTTPException(
            status_code=400,
            detail="Tenant user must be linked to a tenant"
        )

    # 4. Check tenant exists

    if u.tenant_id is not None:

        tenant = db.query(Tenant).filter(
            Tenant.id == u.tenant_id
        ).first()

        if not tenant:
            raise HTTPException(
                status_code=404,
                detail="Tenant not found"
            )

    # 5. Create user in Keycloak

    try:

        create_keycloak_user(
            u.username,
            u.password,
            role.name
        )

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    # 6. Create user in local database

    user = User(
        username=u.username,
        tenant_id=u.tenant_id,
        role_id=u.role_id
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


# ADMIN ONLY

@app.get("/users")
def get_users(
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin"))
):
    return db.query(User).all()


# ADMIN ONLY
# Delete user

@app.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin"))
):
    # Find local user

    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Don't allow admin to delete admin user

    role = db.query(Role).filter(
        Role.id == user.role_id
    ).first()

    if role and role.name == "admin":
        raise HTTPException(
            status_code=400,
            detail="Admin user cannot be deleted"
        )

    # Delete from Keycloak

    try:

        delete_keycloak_user(
            user.username
        )

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    # Delete from local database

    db.delete(user)
    db.commit()

    return {
        "message": "User deleted successfully",
        "username": user.username
    }


# =========================================================
# PRODUCTS
# =========================================================

# TENANT ONLY
# Create product for own tenant

@app.post("/products")
def create_product(
    p: ProductCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("tenant"))
):
    # Find local user using Keycloak username

    local_user = db.query(User).filter(
        User.username == current_user.get(
            "preferred_username"
        )
    ).first()

    if not local_user:
        raise HTTPException(
            status_code=404,
            detail="User not found in local database"
        )

    # Tenant user must have tenant

    if local_user.tenant_id is None:
        raise HTTPException(
            status_code=400,
            detail="User is not linked to any tenant"
        )

    # User can only create product for own tenant

    if p.tenant_id != local_user.tenant_id:
        raise HTTPException(
            status_code=403,
            detail="You can only manage your own tenant products"
        )

    x = Product(
        name=p.name,
        category=p.category,
        price=p.price,
        quantity=p.quantity,
        tenant_id=local_user.tenant_id
    )

    db.add(x)
    db.commit()
    db.refresh(x)

    return x


# TENANT ONLY
# Get own products

@app.get("/my-products")
def get_my_products(
    db: Session = Depends(get_db),
    current_user=Depends(require_role("tenant"))
):
    local_user = db.query(User).filter(
        User.username == current_user.get(
            "preferred_username"
        )
    ).first()

    if not local_user:
        raise HTTPException(
            status_code=404,
            detail="User not found in local database"
        )

    if local_user.tenant_id is None:
        raise HTTPException(
            status_code=400,
            detail="User is not linked to any tenant"
        )

    products = db.query(Product).filter(
        Product.tenant_id == local_user.tenant_id
    ).all()

    return products


# TENANT ONLY
# Update own product

@app.put("/products/{product_id}")
def update_product(
    product_id: int,
    p: ProductCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("tenant"))
):
    local_user = db.query(User).filter(
        User.username == current_user.get(
            "preferred_username"
        )
    ).first()

    if not local_user:
        raise HTTPException(
            status_code=404,
            detail="User not found in local database"
        )

    if local_user.tenant_id is None:
        raise HTTPException(
            status_code=400,
            detail="User is not linked to any tenant"
        )

    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    # Tenant can update only own product

    if product.tenant_id != local_user.tenant_id:
        raise HTTPException(
            status_code=403,
            detail="You can only update your own tenant products"
        )

    product.name = p.name
    product.category = p.category
    product.price = p.price
    product.quantity = p.quantity

    db.commit()
    db.refresh(product)

    return product


# TENANT ONLY
# Delete own product

@app.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("tenant"))
):
    local_user = db.query(User).filter(
        User.username == current_user.get(
            "preferred_username"
        )
    ).first()

    if not local_user:
        raise HTTPException(
            status_code=404,
            detail="User not found in local database"
        )

    if local_user.tenant_id is None:
        raise HTTPException(
            status_code=400,
            detail="User is not linked to any tenant"
        )

    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    # Tenant can delete only own product

    if product.tenant_id != local_user.tenant_id:
        raise HTTPException(
            status_code=403,
            detail="You can only delete your own tenant products"
        )

    db.delete(product)
    db.commit()

    return {
        "message": "Product deleted successfully",
        "product_id": product_id
    }


# TENANT ONLY
# Update stock

@app.put("/products/{product_id}/stock")
def update_stock(
    product_id: int,
    quantity: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("tenant"))
):
    local_user = db.query(User).filter(
        User.username == current_user.get(
            "preferred_username"
        )
    ).first()

    if not local_user:
        raise HTTPException(
            status_code=404,
            detail="User not found in local database"
        )

    if local_user.tenant_id is None:
        raise HTTPException(
            status_code=400,
            detail="User is not linked to any tenant"
        )

    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    # Tenant can update stock only for own product

    if product.tenant_id != local_user.tenant_id:
        raise HTTPException(
            status_code=403,
            detail="You can only manage stock of your own tenant products"
        )

    if quantity < 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity cannot be negative"
        )

    product.quantity = quantity

    db.commit()
    db.refresh(product)

    return {
        "message": "Stock updated successfully",
        "product_id": product.id,
        "quantity": product.quantity
    }


# =========================================================
# ALL PRODUCTS
# =========================================================

@app.get("/products")
def get_products(
    search: str | None = None,
    category: str | None = None,
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    if page < 1:
        raise HTTPException(
            status_code=400,
            detail="Page must be greater than 0"
        )

    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 100"
        )

    q = db.query(Product)

    # Search by product name

    if search:
        q = q.filter(
            Product.name.ilike(
                f"%{search}%"
            )
        )

    # Filter by category

    if category:
        q = q.filter(
            Product.category == category
        )

    products = q.offset(
        (page - 1) * limit
    ).limit(limit).all()

    return products


# =========================================================
# TENANT LEVEL PRODUCTS
# =========================================================

@app.get("/{tenant_name}/products")
def get_tenant_products(
    tenant_name: str,
    search: str | None = None,
    category: str | None = None,
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    if page < 1:
        raise HTTPException(
            status_code=400,
            detail="Page must be greater than 0"
        )

    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 100"
        )

    tenant = db.query(Tenant).filter(
        Tenant.name == tenant_name
    ).first()

    if not tenant:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found"
        )

    q = db.query(Product).filter(
        Product.tenant_id == tenant.id
    )

    if search:
        q = q.filter(
            Product.name.ilike(
                f"%{search}%"
            )
        )

    if category:
        q = q.filter(
            Product.category == category
        )

    products = q.offset(
        (page - 1) * limit
    ).limit(limit).all()

    return products


# =========================================================
# ORDERS
# =========================================================

# Create order using user_id
# Logged-in user can only order for himself

@app.post("/orders")
def create_order(
    o: OrderCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # Check user role

    roles = current_user.get(
        "realm_access",
        {}
    ).get(
        "roles",
        []
    )

    if "user" not in roles and "tenant" not in roles:
        raise HTTPException(
            status_code=403,
            detail="Only users and tenant users can create orders"
        )

    # Find local user

    user = db.query(User).filter(
        User.id == o.user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Logged-in Keycloak user

    local_username = current_user.get(
        "preferred_username"
    )

    if user.username != local_username:
        raise HTTPException(
            status_code=403,
            detail="You can only create orders for yourself"
        )

    total_quantity = 0
    total_amount = 0

    items = []

    for i in o.items:

        product = db.query(Product).filter(
            Product.id == i.product_id
        ).first()

        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product {i.product_id} not found"
            )

        if i.quantity <= 0:
            raise HTTPException(
                status_code=400,
                detail="Quantity must be greater than 0"
            )

        if i.quantity >= product.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough stock for {product.name}"
            )

        total_quantity += i.quantity
        total_amount += product.price * i.quantity

        items.append(
            (product, i.quantity)
        )

    order = Order(
        user_id=user.id,
        total_quantity=total_quantity,
        total_amount=total_amount
    )

    db.add(order)

    db.flush()

    for product, quantity in items:

        product.quantity -= quantity

        item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=quantity
        )

        db.add(item)

    db.commit()

    db.refresh(order)

    return order


# =========================================================
# MY ORDER
# =========================================================

@app.post("/orders/me")
def create_my_order(
    o: MyOrderCreate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    username = user.get(
        "preferred_username"
    )

    if not username:
        raise HTTPException(
            status_code=401,
            detail="Username not found in token"
        )

    db_user = db.query(User).filter(
        User.username == username
    ).first()

    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="User not found in database"
        )

    total_quantity = 0
    total_amount = 0

    items = []

    for i in o.items:

        product = db.query(Product).filter(
            Product.id == i.product_id
        ).first()

        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product {i.product_id} not found"
            )

        if i.quantity <= 0:
            raise HTTPException(
                status_code=400,
                detail="Quantity must be greater than 0"
            )

        if i.quantity >= product.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough stock for {product.name}"
            )

        total_quantity += i.quantity
        total_amount += product.price * i.quantity

        items.append(
            (product, i.quantity)
        )

    order = Order(
        user_id=db_user.id,
        total_quantity=total_quantity,
        total_amount=total_amount
    )

    db.add(order)

    db.flush()

    for product, quantity in items:

        product.quantity -= quantity

        item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=quantity
        )

        db.add(item)

    db.commit()

    db.refresh(order)

    return {
        "message": "Order created successfully",
        "order_id": order.id,
        "total_quantity": order.total_quantity,
        "total_amount": order.total_amount
    }


# =========================================================
# MY ORDER HISTORY
# =========================================================

@app.get("/orders/me", response_model=list[OrderResponse])
def get_my_orders(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    username = user.get(
        "preferred_username"
    )

    if not username:
        raise HTTPException(
            status_code=401,
            detail="Username not found in token"
        )

    db_user = db.query(User).filter(
        User.username == username
    ).first()

    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="User not found in database"
        )

    orders = db.query(Order).filter(
        Order.user_id == db_user.id
    ).all()

    return orders


# =========================================================
# USER ORDER HISTORY
# =========================================================

@app.get(
    "/users/{user_id}/orders",
    response_model=list[OrderResponse]
)
def get_order_history(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    roles = current_user.get(
        "realm_access",
        {}
    ).get(
        "roles",
        []
    )

    if "user" not in roles and "tenant" not in roles:
        raise HTTPException(
            status_code=403,
            detail="Only users and tenant users can view orders"
        )

    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    local_username = current_user.get(
        "preferred_username"
    )

    if user.username != local_username:
        raise HTTPException(
            status_code=403,
            detail="You can only view your own orders"
        )

    orders = db.query(Order).filter(
        Order.user_id == user_id
    ).all()

    return orders


# =========================================================
# CURRENT USER
# =========================================================

@app.get("/me")
def get_me(
    user=Depends(get_current_user)
):
    return {
        "username": user.get(
            "preferred_username"
        ),
        "email": user.get(
            "email"
        ),
        "roles": user.get(
            "realm_access",
            {}
        ).get(
            "roles",
            []
        )
    }

@app.get("/my-tenant")
def get_my_tenant(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    username = user.get("preferred_username")

    if not username:
        raise HTTPException(
            status_code=401,
            detail="Username not found in token"
        )

    local_user = db.query(User).filter(
        User.username == username
    ).first()

    if not local_user:
        raise HTTPException(
            status_code=404,
            detail="User not found in database"
        )

    if local_user.tenant_id is None:
        raise HTTPException(
            status_code=400,
            detail="User is not linked to any tenant"
        )

    tenant = db.query(Tenant).filter(
        Tenant.id == local_user.tenant_id
    ).first()

    if not tenant:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found"
        )

    return {
        "tenant_id": tenant.id,
        "tenant_name": tenant.name
    }

# =========================================================
# ADMIN TEST
# =========================================================

@app.get("/admin-test")
def admin_test(
    user=Depends(require_role("admin"))
):
    return {
        "message": "You are an admin",
        "username": user.get(
            "preferred_username"
        )
    }