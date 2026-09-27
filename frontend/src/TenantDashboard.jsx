import { useEffect, useState } from "react";
import keycloak from "./keycloak";

import {
  getMyTenant,
  getMyProducts,
  createProduct,
  updateProduct,
  deleteProduct,
  updateStock,
} from "./api";

function TenantDashboard() {
  const [tenant, setTenant] = useState(null);
  const [products, setProducts] = useState([]);

  const [form, setForm] = useState({
    name: "",
    category: "",
    price: "",
    quantity: "",
  });

  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);

      const [tenantData, productData] = await Promise.all([
        getMyTenant(),
        getMyProducts(),
      ]);

      setTenant(tenantData);
      setProducts(productData);
    } catch (error) {
      console.error(error);
      alert(error.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleChange = (e) => {
    setForm({
      ...form,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async () => {
    if (!form.name.trim()) {
      alert("Please enter product name");
      return;
    }

    if (!form.category.trim()) {
      alert("Please enter category");
      return;
    }

    if (!form.price || Number(form.price) < 0) {
      alert("Please enter valid price");
      return;
    }

    if (!form.quantity || Number(form.quantity) < 0) {
      alert("Please enter valid quantity");
      return;
    }

    try {
      const productData = {
        name: form.name,
        category: form.category,
        price: Number(form.price),
        quantity: Number(form.quantity),
        tenant_id: tenant.tenant_id,
      };

      if (editingId) {
        await updateProduct(editingId, productData);
        alert("Product updated successfully");
      } else {
        await createProduct(productData);
        alert("Product created successfully");
      }

      setForm({
        name: "",
        category: "",
        price: "",
        quantity: "",
      });

      setEditingId(null);

      await loadData();
    } catch (error) {
      alert(error.message);
    }
  };

  const handleEdit = (product) => {
    setEditingId(product.id);

    setForm({
      name: product.name,
      category: product.category,
      price: String(product.price),
      quantity: String(product.quantity),
    });
  };

  const handleDelete = async (productId) => {
    const confirmDelete = window.confirm(
      "Are you sure you want to delete this product?"
    );

    if (!confirmDelete) return;

    try {
      await deleteProduct(productId);

      alert("Product deleted successfully");

      await loadData();
    } catch (error) {
      alert(error.message);
    }
  };

  const handleStockUpdate = async (product) => {
    const newQuantity = window.prompt(
      "Enter new stock quantity:",
      product.quantity
    );

    if (newQuantity === null) return;

    if (Number(newQuantity) < 0 || newQuantity === "") {
      alert("Invalid quantity");
      return;
    }

    try {
      await updateStock(product.id, Number(newQuantity));

      alert("Stock updated successfully");

      await loadData();
    } catch (error) {
      alert(error.message);
    }
  };

  const cancelEdit = () => {
    setEditingId(null);

    setForm({
      name: "",
      category: "",
      price: "",
      quantity: "",
    });
  };

  const logout = () => {
    keycloak.logout();
  };

  return (
    <div style={{ padding: "30px" }}>
      <h1>🏢 Tenant Dashboard</h1>

      <h2>
        Welcome, {keycloak.tokenParsed?.preferred_username}
      </h2>

      {tenant && (
        <div>
          <p>
            <strong>Tenant:</strong> {tenant.tenant_name}
          </p>

          <p>
            <strong>Tenant ID:</strong> {tenant.tenant_id}
          </p>
        </div>
      )}

      <button onClick={logout}>Logout</button>

      <hr />

      <h2>
        {editingId ? "✏️ Edit Product" : "➕ Add Product"}
      </h2>

      <div>
        <input
          type="text"
          name="name"
          placeholder="Product name"
          value={form.name}
          onChange={handleChange}
        />
      </div>

      <br />

      <div>
        <input
          type="text"
          name="category"
          placeholder="Category"
          value={form.category}
          onChange={handleChange}
        />
      </div>

      <br />

      <div>
        <input
          type="number"
          name="price"
          placeholder="Price"
          value={form.price}
          onChange={handleChange}
        />
      </div>

      <br />

      <div>
        <input
          type="number"
          name="quantity"
          placeholder="Quantity"
          value={form.quantity}
          onChange={handleChange}
        />
      </div>

      <br />

      <button onClick={handleSubmit}>
        {editingId ? "Update Product" : "Create Product"}
      </button>

      {editingId && (
        <button onClick={cancelEdit} style={{ marginLeft: "10px" }}>
          Cancel
        </button>
      )}

      <hr />

      <h2>📦 My Products</h2>

      {loading && <p>Loading...</p>}

      {!loading && products.length === 0 && (
        <p>No products found.</p>
      )}

      {!loading &&
        products.map((product) => (
          <div key={product.id}>
            <h3>{product.name}</h3>

            <p>Category: {product.category}</p>

            <p>Price: ₹{product.price}</p>

            <p>Available Stock: {product.quantity}</p>

            <button onClick={() => handleEdit(product)}>
              Edit
            </button>

            <button
              onClick={() => handleDelete(product.id)}
              style={{ marginLeft: "10px" }}
            >
              Delete
            </button>

            <button
              onClick={() => handleStockUpdate(product)}
              style={{ marginLeft: "10px" }}
            >
              Update Stock
            </button>

            <hr />
          </div>
        ))}
    </div>
  );
}

export default TenantDashboard;