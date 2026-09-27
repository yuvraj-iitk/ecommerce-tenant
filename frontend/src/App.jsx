import { useEffect, useState } from "react";
import AdminDashboard from "./AdminDashboard";
import keycloak from "./keycloak";

import {
  getProducts,
  createOrder,
  getMyOrders,
  getMyTenant,
  getMyProducts,
  createProduct,
  updateProduct,
  deleteProduct,
  updateStock,
} from "./api";

function App() {
  // ==================================================
  // AUTH / ROLE
  // ==================================================

  const roles =
    keycloak.tokenParsed?.realm_access?.roles || [];

  const isAdmin = roles.includes("admin");
  const isTenant = roles.includes("tenant");
  const isLoggedIn = keycloak.authenticated;

  // ==================================================
  // CUSTOMER STATES
  // ==================================================

  const [products, setProducts] = useState([]);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [cart, setCart] = useState([]);
  const [orders, setOrders] = useState([]);
  const [signupUsername, setSignupUsername] = useState("");
  const [signupPassword, setSignupPassword] = useState("");
  const [signupMessage, setSignupMessage] = useState("");
  const [showSignup, setShowSignup] = useState(false);
  const [page, setPage] = useState(1);
  const [limit] = useState(5);

  // ==================================================
  // TENANT STATES
  // ==================================================

  const [tenantInfo, setTenantInfo] = useState(null);
  const [tenantProducts, setTenantProducts] = useState([]);
  const [tenantLoading, setTenantLoading] = useState(false);
  const [tenantError, setTenantError] = useState("");
  const [editingId, setEditingId] = useState(null);

  const [productForm, setProductForm] = useState({
    name: "",
    category: "",
    price: "",
    quantity: "",
  });

  // ==================================================
  // LOAD CUSTOMER PRODUCTS
  // ==================================================

  const loadProducts = async () => {
    try {
      setLoading(true);
      setError("");

      const data = await getProducts(
        search,
        category,
        page,
        limit
      );

      setProducts(data);
    } catch (err) {
      console.error(err);

      setError(
        err.message ||
          "Products load nahi ho pa rahe hain."
      );
    } finally {
      setLoading(false);
    }
  };

  // ==================================================
  // LOAD ORDERS
  // ==================================================

  const loadOrders = async () => {
    try {
      const data = await getMyOrders();
      setOrders(data);
    } catch (error) {
      console.error(error);
    }
  };

  // ==================================================
  // LOAD TENANT DATA
  // ==================================================

  const loadTenantData = async () => {
    try {
      setTenantLoading(true);
      setTenantError("");

      const tenant = await getMyTenant();

      setTenantInfo(tenant);

      const products = await getMyProducts();

      setTenantProducts(products);
    } catch (error) {
      console.error(error);

      setTenantError(
        error.message ||
          "Tenant data load nahi ho pa raha."
      );
    } finally {
      setTenantLoading(false);
    }
  };

  // ==================================================
  // USE EFFECTS
  // ==================================================

  useEffect(() => {
    if (!isAdmin) {
      loadProducts();
    }
  }, [search, category,page, isAdmin]);

  useEffect(() => {
    if (!isAdmin) {
      loadOrders();
    }
  }, [isAdmin]);

  useEffect(() => {
    if (isTenant && !isAdmin) {
      loadTenantData();
    }
  }, [isTenant, isAdmin]);

  // ==================================================
// SIGNUP
// ==================================================

const handleSignup = async (e) => {
  e.preventDefault();

  setSignupMessage("");

  if (!signupUsername || !signupPassword) {
    setSignupMessage("Username and password required.");
    return;
  }

  try {
    const response = await fetch(
      "http://127.0.0.1:8000/signup",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username: signupUsername,
          password: signupPassword,
        }),
      }
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data.detail || "Signup failed"
      );
    }

    setSignupMessage(
      "Signup successful! Now click Login."
    );

    setSignupUsername("");
    setSignupPassword("");
  } catch (error) {
    setSignupMessage(error.message);
  }
};

  // ==================================================
  // LOGOUT
  // ==================================================

  const logout = () => {
    keycloak.logout();
  };

  // ==================================================
  // CART
  // ==================================================

  const addToCart = (product) => {
    const existingProduct = cart.find(
      (item) => item.id === product.id
    );

    if (existingProduct) {
      if (
        existingProduct.cartQuantity >=
        product.quantity
      ) {
        alert("Stock available nahi hai.");
        return;
      }

      setCart(
        cart.map((item) =>
          item.id === product.id
            ? {
                ...item,
                cartQuantity:
                  item.cartQuantity + 1,
              }
            : item
        )
      );
    } else {
      setCart([
        ...cart,
        {
          ...product,
          cartQuantity: 1,
        },
      ]);
    }
  };

  const removeFromCart = (productId) => {
    setCart(
      cart.filter(
        (item) => item.id !== productId
      )
    );
  };

  const increaseQuantity = (productId) => {
    setCart(
      cart.map((item) => {
        if (item.id !== productId) {
          return item;
        }

        if (
          item.cartQuantity >=
          item.quantity
        ) {
          alert("Stock available nahi hai.");
          return item;
        }

        return {
          ...item,
          cartQuantity:
            item.cartQuantity + 1,
        };
      })
    );
  };

  const decreaseQuantity = (productId) => {
    setCart(
      cart
        .map((item) =>
          item.id === productId
            ? {
                ...item,
                cartQuantity:
                  item.cartQuantity - 1,
              }
            : item
        )
        .filter(
          (item) => item.cartQuantity > 0
        )
    );
  };

  const totalAmount = cart.reduce(
    (total, item) =>
      total +
      item.price *
        item.cartQuantity,
    0
  );

  // ==================================================
  // PLACE ORDER
  // ==================================================

  const placeOrder = async () => {
    if (cart.length === 0) {
      alert("Cart is empty");
      return;
    }

    try {
      const result =
        await createOrder(cart);

      alert(
        `Order placed successfully!\nOrder ID: ${result.order_id}\nTotal: ₹${result.total_amount}`
      );

      setCart([]);

      loadProducts();
      loadOrders();

      if (isTenant) {
        loadTenantData();
      }
    } catch (error) {
      alert(error.message);
    }
  };

  // ==================================================
  // TENANT FORM
  // ==================================================

  const handleFormChange = (e) => {
    setProductForm({
      ...productForm,
      [e.target.name]:
        e.target.value,
    });
  };

  // ==================================================
  // CREATE / UPDATE PRODUCT
  // ==================================================

  const handleProductSubmit =
    async (e) => {
      e.preventDefault();

      if (!tenantInfo) {
        alert(
          "Tenant information not found."
        );
        return;
      }

      if (
        !productForm.name ||
        !productForm.category ||
        productForm.price === "" ||
        productForm.quantity === ""
      ) {
        alert(
          "Please fill all fields."
        );
        return;
      }

      if (
        Number(productForm.price) < 0 ||
        Number(productForm.quantity) < 0
      ) {
        alert(
          "Price and quantity cannot be negative."
        );
        return;
      }

      try {
        const productData = {
          name: productForm.name,
          category:
            productForm.category,
          price:
            Number(productForm.price),
          quantity:
            Number(productForm.quantity),
          tenant_id:
            tenantInfo.tenant_id,
        };

        if (editingId) {
          await updateProduct(
            editingId,
            productData
          );

          alert(
            "Product updated successfully."
          );
        } else {
          await createProduct(
            productData
          );

          alert(
            "Product created successfully."
          );
        }

        setProductForm({
          name: "",
          category: "",
          price: "",
          quantity: "",
        });

        setEditingId(null);

        await loadTenantData();
        await loadProducts();
      } catch (error) {
        alert(error.message);
      }
    };

  // ==================================================
  // EDIT PRODUCT
  // ==================================================

  const startEdit = (product) => {
    setEditingId(product.id);

    setProductForm({
      name: product.name,
      category: product.category,
      price: String(product.price),
      quantity: String(product.quantity),
    });

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  // ==================================================
  // CANCEL EDIT
  // ==================================================

  const cancelEdit = () => {
    setEditingId(null);

    setProductForm({
      name: "",
      category: "",
      price: "",
      quantity: "",
    });
  };

  // ==================================================
  // DELETE PRODUCT
  // ==================================================

  const handleDeleteProduct =
    async (productId) => {
      const confirmDelete =
        window.confirm(
          "Are you sure you want to delete this product?"
        );

      if (!confirmDelete) {
        return;
      }

      try {
        await deleteProduct(
          productId
        );

        alert(
          "Product deleted successfully."
        );

        await loadTenantData();
        await loadProducts();
      } catch (error) {
        alert(error.message);
      }
    };

  // ==================================================
  // UPDATE STOCK
  // ==================================================

  const handleStockUpdate =
    async (product) => {
      const newQuantity =
        window.prompt(
          `Enter new stock quantity for ${product.name}:`,
          product.quantity
        );

      if (newQuantity === null) {
        return;
      }

      const quantity =
        Number(newQuantity);

      if (
        isNaN(quantity) ||
        quantity < 0 ||
        !Number.isInteger(quantity)
      ) {
        alert(
          "Please enter a valid whole number."
        );
        return;
      }

      try {
        await updateStock(
          product.id,
          quantity
        );

        alert(
          "Stock updated successfully."
        );

        await loadTenantData();
        await loadProducts();
      } catch (error) {
        alert(error.message);
      }
    };

  // ==================================================
// LOGIN / SIGNUP SCREEN
// ==================================================

if (!isLoggedIn) {
  return (
    <div
      style={{
        maxWidth: "500px",
        margin: "100px auto",
        padding: "30px",
        textAlign: "center",
        fontFamily: "Arial",
      }}
    >
      <h1
  style={{
    fontSize: "40px",
    margin: "0 0 30px 0",
    lineHeight: "1.2",
  }}
>
  E-Commerce Application
</h1>

      {!showSignup ? (
        <>
          <h2>Welcome</h2>

          <p>
            Please login to continue shopping.
          </p>

          <button
            onClick={() => keycloak.login()}
          >
            Login with Keycloak
          </button>

          <br />
          <br />

          <p>
            Don't have an account?
          </p>

          <button
            onClick={() => setShowSignup(true)}
          >
            Signup
          </button>
        </>
      ) : (
        <>
          <h2>Create Account</h2>

          <form onSubmit={handleSignup}>
            <div>
              <input
                type="text"
                placeholder="Username"
                value={signupUsername}
                onChange={(e) =>
                  setSignupUsername(e.target.value)
                }
              />
            </div>

            <br />

            <div>
              <input
                type="password"
                placeholder="Password"
                value={signupPassword}
                onChange={(e) =>
                  setSignupPassword(e.target.value)
                }
              />
            </div>

            <br />

            <button type="submit">
              Create Account
            </button>
          </form>

          {signupMessage && (
            <p>{signupMessage}</p>
          )}

          <br />

          <button
            onClick={() => {
              setShowSignup(false);
              setSignupMessage("");
            }}
          >
            Back to Login
          </button>
        </>
      )}
    </div>
  );
}  

  // ==================================================
  // ADMIN
  // ==================================================

  if (isAdmin) {
    return <AdminDashboard />;
  }

  // ==================================================
  // UI
  // ==================================================

  return (
    <div
      style={{
        maxWidth: "1100px",
        margin: "auto",
        padding: "20px",
        fontFamily: "Arial",
      }}
    >
      {/* HEADER */}

        <h1
          style={{
            fontSize: "42px",
            marginBottom: "30px",
          }}
        >
          🛍️ E-Commerce Application
        </h1>        

      <h2>
        Welcome,{" "}
        {
          keycloak.tokenParsed
            ?.preferred_username
        }
      </h2>

      <p>
        Role:{" "}
        {
          keycloak.tokenParsed
            ?.realm_access
            ?.roles
            ?.join(", ")
        }
      </p>

      <button onClick={logout}>
        Logout
      </button>

      <hr />

      {/* ================================================= */}
      {/* TENANT DASHBOARD */}
      {/* ================================================= */}

      {isTenant && (
        <div>
          <h1>
            🏪 Tenant Dashboard
          </h1>

          {tenantInfo && (
            <div>
              <h2>
                Tenant:{" "}
                {
                  tenantInfo.tenant_name
                }
              </h2>

              <p>
                Tenant ID:{" "}
                {
                  tenantInfo.tenant_id
                }
              </p>
            </div>
          )}

          {tenantError && (
            <p>
              {tenantError}
            </p>
          )}

          <hr />

          {/* PRODUCT FORM */}

          <h2>
            {editingId
              ? "✏️ Edit Product"
              : "➕ Add New Product"}
          </h2>

          <form
            onSubmit={
              handleProductSubmit
            }
          >
            <div>
              <input
                type="text"
                name="name"
                placeholder="Product Name"
                value={
                  productForm.name
                }
                onChange={
                  handleFormChange
                }
              />
            </div>

            <br />

            <div>
              <input
                type="text"
                name="category"
                placeholder="Category"
                value={
                  productForm.category
                }
                onChange={
                  handleFormChange
                }
              />
            </div>

            <br />

            <div>
              <input
                type="number"
                name="price"
                placeholder="Price"
                value={
                  productForm.price
                }
                onChange={
                  handleFormChange
                }
              />
            </div>

            <br />

            <div>
              <input
                type="number"
                name="quantity"
                placeholder="Quantity"
                value={
                  productForm.quantity
                }
                onChange={
                  handleFormChange
                }
              />
            </div>

            <br />

            <button type="submit">
              {editingId
                ? "Update Product"
                : "Create Product"}
            </button>

            {editingId && (
              <button
                type="button"
                onClick={
                  cancelEdit
                }
                style={{
                  marginLeft: "10px",
                }}
              >
                Cancel
              </button>
            )}
          </form>

          <hr />

          {/* TENANT PRODUCTS */}

          <h2>
            📦 My Products
          </h2>

          {tenantLoading && (
            <p>
              Loading your products...
            </p>
          )}

          {!tenantLoading &&
            tenantProducts.length === 0 && (
              <p>
                You have no products yet.
              </p>
            )}

          {tenantProducts.map(
            (product) => (
              <div
                key={product.id}
                style={{
                  border:
                    "1px solid #ccc",
                  padding: "15px",
                  marginBottom: "10px",
                }}
              >
                <h3>
                  {product.name}
                </h3>

                <p>
                  Category:{" "}
                  {product.category}
                </p>

                <p>
                  Price: ₹
                  {product.price}
                </p>

                <p>
                  Stock:{" "}
                  {product.quantity}
                </p>

                <button
                  onClick={() =>
                    startEdit(product)
                  }
                >
                  Edit
                </button>

                <button
                  onClick={() =>
                    handleDeleteProduct(
                      product.id
                    )
                  }
                  style={{
                    marginLeft: "10px",
                  }}
                >
                  Delete
                </button>

                <button
                  onClick={() =>
                    handleStockUpdate(
                      product
                    )
                  }
                  style={{
                    marginLeft: "10px",
                  }}
                >
                  Update Stock
                </button>
              </div>
            )
          )}

          <hr />
        </div>
      )}

      {/* ================================================= */}
      {/* CUSTOMER SHOPPING */}
      {/* ================================================= */}

      <h1>
        🛍️ Shop Products
      </h1>

      <h2>
        Products
      </h2>

      {/* SEARCH */}

      <input
        type="text"
        placeholder="Search product..."
        value={search}
        onChange={(e) =>
          setSearch(e.target.value)
        }
      />

      {/* CATEGORY */}

      <select
        value={category}
        onChange={(e) =>
          setCategory(e.target.value)
        }
        style={{
          marginLeft: "10px",
        }}
      >
        <option value="">
          All Categories
        </option>

        <option value="Shoes">
          Shoes
        </option>

        <option value="Clothing">
          Clothing
        </option>

        <option value="Electronics">
          Electronics
        </option>

        <option value="Accessories">
          Accessories
        </option>
      </select>

      <br />
      <br />

      {/* PRODUCTS */}

      {loading && (
        <p>
          Loading products...
        </p>
      )}

      {error && (
        <p>
          {error}
        </p>
      )}

      {!loading &&
        !error &&
        products.length === 0 && (
          <p>
            No products found.
          </p>
        )}

      {!loading &&
        products.map(
          (product) => (
            <div
              key={product.id}
              style={{
                border:
                  "1px solid #ccc",
                padding: "15px",
                marginBottom: "10px",
              }}
            >
              <h3>
                {product.name}
              </h3>

              <p>
                Category:{" "}
                {product.category}
              </p>

              <p>
                Price: ₹
                {product.price}
              </p>

              <p>
                Available:{" "}
                {product.quantity}
              </p>

              {product.quantity > 0 ? (
                <button
                  onClick={() =>
                    addToCart(product)
                  }
                >
                  Add to Cart
                </button>
              ) : (
                <button disabled>
                  Out of Stock
                </button>
              )}
            </div>
          )
        )}
      {/* PAGINATION */}

      <div
        style={{
          marginTop: "20px",
          textAlign: "center",
        }}
      >
        <button
          onClick={() =>
            setPage((prev) => Math.max(prev - 1, 1))
          }
          disabled={page === 1}
        >
          Previous
        </button>
      
        <span
          style={{
            margin: "0 15px",
          }}
        >
          Page {page}
        </span>
      
        <button
          onClick={() =>
            setPage((prev) => prev + 1)
          }
          disabled={products.length < limit}
        >
          Next
        </button>
      </div>        
        

      
        

      {/* CART */}

      <hr />

      <h2>
        🛒 Cart
      </h2>

      {cart.length === 0 && (
        <p>
          Your cart is empty.
        </p>
      )}

      {cart.map(
        (item) => (
          <div
            key={item.id}
            style={{
              border:
                "1px solid #ccc",
              padding: "15px",
              marginBottom: "10px",
            }}
          >
            <h3>
              {item.name}
            </h3>

            <p>
              Price: ₹
              {item.price}
            </p>

            <button
              onClick={() =>
                decreaseQuantity(
                  item.id
                )
              }
            >
              -
            </button>

            <span
              style={{
                margin: "0 10px",
              }}
            >
              {item.cartQuantity}
            </span>

            <button
              onClick={() =>
                increaseQuantity(
                  item.id
                )
              }
            >
              +
            </button>

            <p>
              Subtotal: ₹
              {
                item.price *
                item.cartQuantity
              }
            </p>

            <button
              onClick={() =>
                removeFromCart(
                  item.id
                )
              }
            >
              Remove
            </button>
          </div>
        )
      )}

      {cart.length > 0 && (
        <div>
          <h2>
            Total: ₹
            {totalAmount}
          </h2>

          <button
            onClick={placeOrder}
          >
            Place Order
          </button>
        </div>
      )}

      {/* ORDER HISTORY */}

      <hr />

      <h2>
        📦 My Order History
      </h2>

      {orders.length === 0 && (
        <p>
          No orders found.
        </p>
      )}

      {orders.map(
  (order) => (
    <div
      key={order.id}
      style={{
        border: "1px solid #ccc",
        padding: "15px",
        marginBottom: "10px",
      }}
    >
      <h3>
        Order #{order.id}
      </h3>

      <p>
        Total Quantity:{" "}
        {order.total_quantity}
      </p>

      <p>
        Total Amount: ₹
        {order.total_amount}
      </p>

      <h4>Items:</h4>

      {order.items && order.items.length > 0 ? (
        order.items.map(
          (item, index) => (
            <div
              key={index}
              style={{
                marginLeft: "20px",
                marginBottom: "8px",
              }}
            >
            <p>
              {products.find(
                (product) => product.id === item.product_id
              )?.name || `Product ID: ${item.product_id}`}
              × {item.quantity}
            </p>            
            </div>
          )
        )
      ) : (
        <p>No items found.</p>
      )}
    </div>
  )
)}
    </div>
  );
}

export default App;