from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from auth import get_current_user, require_role
from keycloak_admin import create_keycloak_user, delete_keycloak_user

from database import engine, Base, SessionLocal
from models import Tenant, Role, User, Product, Order, OrderItem
from schemas import TenantCreate, RoleCreate, UserCreate, ProductCreate , OrderCreate,OrderResponse

Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def home():
    return {"message": "E-commerce API is working"}

#  Post Tenant
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

    # 3. Tenant user must have a tenant
    if role.name == "tenant" and u.tenant_id is None:
        raise HTTPException(
            status_code=400,
            detail="Tenant user must be linked to a tenant"
        )

    # 4. Check tenant
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
            u.password
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


# get Tenant
@app.get("/tenants")
def get_tenants(db: Session = Depends(get_db)):
    return db.query(Tenant).all()

# post roles
@app.post("/roles")
def create_role(r: RoleCreate, db: Session = Depends(get_db)):
    x = Role(name=r.name)
    db.add(x)
    db.commit()
    db.refresh(x)
    return x

# get roles
@app.get("/roles")
def get_roles(db: Session = Depends(get_db)):
    return db.query(Role).all()

# post users
@app.post("/users")
def create_user(
    u: UserCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin"))
):
    # Check username already exists
    existing_user = db.query(User).filter(
        User.username == u.username
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    # Check role exists
    role = db.query(Role).filter(
        Role.id == u.role_id
    ).first()

    if not role:
        raise HTTPException(
            status_code=404,
            detail="Role not found"
        )

    # If user is a tenant user, tenant must be provided
    if role.name == "tenant" and u.tenant_id is None:
        raise HTTPException(
            status_code=400,
            detail="Tenant user must be linked to a tenant"
        )

    # Check tenant exists
    if u.tenant_id is not None:
        tenant = db.query(Tenant).filter(
            Tenant.id == u.tenant_id
        ).first()

        if not tenant:
            raise HTTPException(
                status_code=404,
                detail="Tenant not found"
            )

    # Create user
    user = User(
        username=u.username,
        tenant_id=u.tenant_id,
        role_id=u.role_id
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user

# get users
@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()

# post products
@app.post("/products")
def create_product(
    p: ProductCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("tenant"))
):
    # Keycloak username se local database user find karo
    local_user = db.query(User).filter(
        User.username == current_user.get("preferred_username")
    ).first()

    if not local_user:
        raise HTTPException(
            status_code=404,
            detail="User not found in local database"
        )

    # Tenant user ke paas tenant hona zaroori hai
    if local_user.tenant_id is None:
        raise HTTPException(
            status_code=400,
            detail="User is not linked to any tenant"
        )

    # User sirf apne tenant ke liye product create kar sakta hai
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

# get my products
@app.get("/my-products")
def get_my_products(
    db: Session = Depends(get_db),
    current_user=Depends(require_role("tenant"))
):
    local_user = db.query(User).filter(
        User.username == current_user.get("preferred_username")
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

# update my product
@app.put("/products/{product_id}")
def update_product(
    product_id: int,
    p: ProductCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("tenant"))
):
    local_user = db.query(User).filter(
        User.username == current_user.get("preferred_username")
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

    # Tenant can update only its own product
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

# delete my product
@app.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("tenant"))
):
    local_user = db.query(User).filter(
        User.username == current_user.get("preferred_username")
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

    # Tenant can delete only its own product
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

# update product stock
@app.put("/products/{product_id}/stock")
def update_stock(
    product_id: int,
    quantity: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("tenant"))
):
    local_user = db.query(User).filter(
        User.username == current_user.get("preferred_username")
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

    # Tenant can update stock only for its own product
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

# get products
@app.get("/products")
def get_products(db: Session = Depends(get_db)):
    return db.query(Product).all()

# get tenant name products
@app.get("/{tenant_name}/products")
def get_tenant_products(
    tenant_name: str,
    search: str | None = None,
    category: str | None = None,
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    t = db.query(Tenant).filter(
        Tenant.name == tenant_name
    ).first()

    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found")

    q = db.query(Product).filter(Product.tenant_id == t.id)

    if search:
        q = q.filter(Product.name.ilike(f"%{search}%"))

    if category:
        q = q.filter(Product.category == category)

    products = q.offset((page - 1) * limit).limit(limit).all()

    return products


# post orders
@app.post("/orders")
def create_order(
    o: OrderCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # 1. Check user role
    roles = current_user.get("realm_access", {}).get("roles", [])

    if "user" not in roles and "tenant" not in roles:
        raise HTTPException(
            status_code=403,
            detail="Only users and tenant users can create orders"
        )

    # 2. Find local user
    user = db.query(User).filter(
        User.id == o.user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # 3. Make sure logged-in Keycloak user
    #    is ordering for himself
    local_username = current_user.get("preferred_username")

    if user.username != local_username:
        raise HTTPException(
            status_code=403,
            detail="You can only create orders for yourself"
        )

    # 4. Calculate order totals
    total_quantity = 0
    total_amount = 0

    items = []

    for i in o.items:

        # Find product
        p = db.query(Product).filter(
            Product.id == i.product_id
        ).first()

        if not p:
            raise HTTPException(
                status_code=404,
                detail=f"Product {i.product_id} not found"
            )

        # Quantity must be positive
        if i.quantity <= 0:
            raise HTTPException(
                status_code=400,
                detail="Quantity must be greater than 0"
            )

        # Check stock
        if i.quantity > p.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough stock for {p.name}"
            )

        # Calculate totals
        total_quantity += i.quantity
        total_amount += p.price * i.quantity

        items.append((p, i.quantity))

    # 5. Create order
    order = Order(
        user_id=user.id,
        total_quantity=total_quantity,
        total_amount=total_amount
    )

    db.add(order)

    # Get order ID
    db.flush()

    # 6. Create order items
    for p, q in items:

        # Reduce product stock
        p.quantity -= q

        item = OrderItem(
            order_id=order.id,
            product_id=p.id,
            quantity=q
        )

        db.add(item)

    # 7. Save everything
    db.commit()

    # 8. Refresh order
    db.refresh(order)

    return order

# get user history
@app.get("/users/{user_id}/orders", response_model=list[OrderResponse])
def get_order_history(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # Check Keycloak role
    roles = current_user.get("realm_access", {}).get("roles", [])

    if "user" not in roles and "tenant" not in roles:
        raise HTTPException(
            status_code=403,
            detail="Only users and tenant users can view orders"
        )

    # Find local user
    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Logged-in user can see only their own orders
    local_username = current_user.get("preferred_username")

    if user.username != local_username:
        raise HTTPException(
            status_code=403,
            detail="You can only view your own orders"
        )

    # Get user's orders
    orders = db.query(Order).filter(
        Order.user_id == user_id
    ).all()

    return orders

@app.get("/me")
def get_me(user=Depends(get_current_user)):
    return {
        "username": user.get("preferred_username"),
        "email": user.get("email"),
        "roles": user.get("realm_access", {}).get("roles", [])
    }

# admin test
@app.get("/admin-test")
def admin_test(user=Depends(require_role("admin"))):
    return {
        "message": "You are an admin",
        "username": user.get("preferred_username")
    }


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

    # Don't allow admin to delete an admin user
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
        delete_keycloak_user(user.username)
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