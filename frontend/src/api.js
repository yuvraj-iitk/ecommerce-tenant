import keycloak from "./keycloak";

const API_URL = "http://127.0.0.1:8000";

// =========================
// CUSTOMER APIs
// =========================

// GET ALL PRODUCTS
export async function getProducts(
  search = "",
  category = "",
  page = 1,
  limit = 10
) {
  const params = new URLSearchParams();

  if (search) params.append("search", search);
  if (category) params.append("category", category);

  params.append("page", page);
  params.append("limit", limit);

  const response = await fetch(
    `${API_URL}/products?${params.toString()}`,
    {
      headers: {
        Authorization: `Bearer ${keycloak.token}`,
      },
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail || "Failed to fetch products"
    );
  }

  return data;
}

// CREATE ORDER
export async function createOrder(cart) {
  const orderData = {
    items: cart.map((item) => ({
      product_id: item.id,
      quantity: item.cartQuantity,
    })),
  };

  const response = await fetch(`${API_URL}/orders/me`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${keycloak.token}`,
    },
    body: JSON.stringify(orderData),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail || "Order creation failed"
    );
  }

  return data;
}

// MY ORDERS
export async function getMyOrders() {
  const response = await fetch(`${API_URL}/orders/me`, {
    headers: {
      Authorization: `Bearer ${keycloak.token}`,
    },
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail || "Failed to fetch orders"
    );
  }

  return data;
}


// =========================
// TENANT APIs
// =========================

// GET CURRENT TENANT
export async function getMyTenant() {
  const response = await fetch(`${API_URL}/my-tenant`, {
    headers: {
      Authorization: `Bearer ${keycloak.token}`,
    },
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail || "Failed to fetch tenant"
    );
  }

  return data;
}

// GET OWN PRODUCTS
export async function getMyProducts() {
  const response = await fetch(`${API_URL}/my-products`, {
    headers: {
      Authorization: `Bearer ${keycloak.token}`,
    },
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail || "Failed to fetch your products"
    );
  }

  return data;
}

// CREATE PRODUCT
export async function createProduct(product) {
  const response = await fetch(`${API_URL}/products`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${keycloak.token}`,
    },
    body: JSON.stringify(product),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail || "Failed to create product"
    );
  }

  return data;
}

// UPDATE PRODUCT
export async function updateProduct(productId, product) {
  const response = await fetch(
    `${API_URL}/products/${productId}`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${keycloak.token}`,
      },
      body: JSON.stringify(product),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail || "Failed to update product"
    );
  }

  return data;
}

// DELETE PRODUCT
export async function deleteProduct(productId) {
  const response = await fetch(
    `${API_URL}/products/${productId}`,
    {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${keycloak.token}`,
      },
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail || "Failed to delete product"
    );
  }

  return data;
}

// UPDATE STOCK
export async function updateStock(productId, quantity) {
  const response = await fetch(
    `${API_URL}/products/${productId}/stock?quantity=${quantity}`,
    {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${keycloak.token}`,
      },
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail || "Failed to update stock"
    );
  }

  return data;
}


// =========================
// ADMIN APIs
// =========================

// GET ALL TENANTS
export async function getTenants() {
  const response = await fetch(`${API_URL}/tenants`, {
    headers: {
      Authorization: `Bearer ${keycloak.token}`,
    },
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail || "Failed to fetch tenants"
    );
  }

  return data;
}

// CREATE TENANT
export async function createTenant(name) {
  const response = await fetch(`${API_URL}/tenants`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${keycloak.token}`,
    },
    body: JSON.stringify({
      name: name,
    }),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail || "Failed to create tenant"
    );
  }

  return data;
}

// DELETE TENANT
export async function deleteTenant(tenantId) {
  const response = await fetch(
    `${API_URL}/tenants/${tenantId}`,
    {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${keycloak.token}`,
      },
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail || "Failed to delete tenant"
    );
  }

  return data;
}

// GET USERS
export async function getUsers() {
  const response = await fetch(`${API_URL}/users`, {
    headers: {
      Authorization: `Bearer ${keycloak.token}`,
    },
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail || "Failed to fetch users"
    );
  }

  return data;
}

// GET ROLES
export async function getRoles() {
  const response = await fetch(`${API_URL}/roles`, {
    headers: {
      Authorization: `Bearer ${keycloak.token}`,
    },
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail || "Failed to fetch roles"
    );
  }

  return data;
}

// CREATE USER
export async function createUser(user) {
  const response = await fetch(`${API_URL}/users`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${keycloak.token}`,
    },
    body: JSON.stringify(user),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail || "Failed to create user"
    );
  }

  return data;
}

// DELETE USER
export async function deleteUser(userId) {
  const response = await fetch(
    `${API_URL}/users/${userId}`,
    {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${keycloak.token}`,
      },
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail || "Failed to delete user"
    );
  }

  return data;
}