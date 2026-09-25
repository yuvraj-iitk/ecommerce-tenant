from pydantic import BaseModel

class TenantCreate(BaseModel):
    name: str

class RoleCreate(BaseModel):
    name: str    

class UserCreate(BaseModel):
    username: str
    password: str
    tenant_id: int | None = None
    role_id: int    

class ProductCreate(BaseModel):
    name: str
    category: str
    price: int
    quantity: int
    tenant_id: int

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int


class OrderCreate(BaseModel):
    user_id: int
    items: list[OrderItemCreate]


class OrderItemResponse(BaseModel):
    product_id: int
    quantity: int

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: int
    user_id: int
    total_quantity: int
    total_amount: int
    items: list[OrderItemResponse]

    class Config:
        from_attributes = True