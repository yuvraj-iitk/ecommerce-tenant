import { useEffect, useState } from "react";
import keycloak from "./keycloak";

import {
  getTenants,
  createTenant,
  deleteTenant,
  getUsers,
  getRoles,
  createUser,
  deleteUser,
} from "./api";

function AdminDashboard() {
  const [tenants, setTenants] = useState([]);
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);

  const [tenantName, setTenantName] = useState("");

  const [userForm, setUserForm] = useState({
    username: "",
    password: "",
    tenant_id: "",
    role_id: "",
  });

  const [loading, setLoading] = useState(false);

  // Load all admin data
  const loadData = async () => {
    try {
      setLoading(true);

      const [tenantData, userData, roleData] = await Promise.all([
        getTenants(),
        getUsers(),
        getRoles(),
      ]);

      setTenants(tenantData);
      setUsers(userData);
      setRoles(roleData);

      // Default role = tenant
      const tenantRole = roleData.find((role) => role.name === "tenant");

      if (tenantRole) {
        setUserForm((prev) => ({
          ...prev,
          role_id: String(tenantRole.id),
        }));
      }
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

  // Create Tenant
  const handleCreateTenant = async () => {
    if (!tenantName.trim()) {
      alert("Please enter tenant name");
      return;
    }

    try {
      await createTenant(tenantName);

      alert("Tenant created successfully");

      setTenantName("");

      await loadData();
    } catch (error) {
      alert(error.message);
    }
  };

  // Delete Tenant
  const handleDeleteTenant = async (tenantId) => {
    const confirmDelete = window.confirm(
      "Are you sure you want to delete this tenant?"
    );

    if (!confirmDelete) {
      return;
    }

    try {
      await deleteTenant(tenantId);

      alert("Tenant deleted successfully");

      await loadData();
    } catch (error) {
      alert(error.message);
    }
  };

  // Create User
  const handleCreateUser = async () => {
    if (!userForm.username.trim()) {
      alert("Please enter username");
      return;
    }

    if (!userForm.password) {
      alert("Please enter password");
      return;
    }

    if (!userForm.role_id) {
      alert("Please select role");
      return;
    }

    const selectedRole = roles.find(
      (role) => String(role.id) === String(userForm.role_id)
    );

    // Tenant role must have a tenant
    if (selectedRole?.name === "tenant" && !userForm.tenant_id) {
      alert("Please select a tenant for tenant user");
      return;
    }

    try {
      const userData = {
        username: userForm.username,
        password: userForm.password,
        role_id: Number(userForm.role_id),
        tenant_id: userForm.tenant_id
          ? Number(userForm.tenant_id)
          : null,
      };

      await createUser(userData);

      alert("User created successfully");

      setUserForm({
        username: "",
        password: "",
        tenant_id: "",
        role_id: String(
          roles.find((role) => role.name === "tenant")?.id || ""
        ),
      });

      await loadData();
    } catch (error) {
      alert(error.message);
    }
  };

  // Delete User
  const handleDeleteUser = async (userId) => {
    const confirmDelete = window.confirm(
      "Are you sure you want to delete this user?"
    );

    if (!confirmDelete) {
      return;
    }

    try {
      await deleteUser(userId);

      alert("User deleted successfully");

      await loadData();
    } catch (error) {
      alert(error.message);
    }
  };

  const logout = () => {
    keycloak.logout();
  };

  // Find tenant name from tenant ID
  const getTenantName = (tenantId) => {
    const tenant = tenants.find(
      (tenant) => tenant.id === tenantId
    );

    return tenant ? tenant.name : "No Tenant";
  };

  // Find role name from role ID
  const getRoleName = (roleId) => {
    const role = roles.find(
      (role) => role.id === roleId
    );

    return role ? role.name : "Unknown";
  };

  return (
    <div style={{ padding: "30px" }}>
      <h1>Admin Dashboard</h1>

      <h2>
        Welcome, {keycloak.tokenParsed?.preferred_username}
      </h2>

      <p>
        Role: Admin
      </p>

      <button onClick={logout}>
        Logout
      </button>

      <hr />

      {/* ================= TENANTS ================= */}

      <h2>🏢 Tenant Management</h2>

      <div>
        <input
          type="text"
          placeholder="Enter tenant name"
          value={tenantName}
          onChange={(e) => setTenantName(e.target.value)}
        />

        <button onClick={handleCreateTenant}>
          Create Tenant
        </button>
      </div>

      <br />

      {tenants.length === 0 ? (
        <p>No tenants found.</p>
      ) : (
        tenants.map((tenant) => (
          <div key={tenant.id}>
            <h3>{tenant.name}</h3>

            <p>
              Tenant ID: {tenant.id}
            </p>

            <button
              onClick={() => handleDeleteTenant(tenant.id)}
            >
              Delete Tenant
            </button>

            <hr />
          </div>
        ))
      )}

      {/* ================= CREATE USER ================= */}

      <h2>👤 Create Tenant User</h2>

      <div>
        <input
          type="text"
          placeholder="Username"
          value={userForm.username}
          onChange={(e) =>
            setUserForm({
              ...userForm,
              username: e.target.value,
            })
          }
        />
      </div>

      <br />

      <div>
        <input
          type="password"
          placeholder="Password"
          value={userForm.password}
          onChange={(e) =>
            setUserForm({
              ...userForm,
              password: e.target.value,
            })
          }
        />
      </div>

      <br />

      <div>
        <label>Role: </label>

        <select
          value={userForm.role_id}
          onChange={(e) =>
            setUserForm({
              ...userForm,
              role_id: e.target.value,
            })
          }
        >
          <option value="">
            Select Role
          </option>

          {roles.map((role) => (
            <option
              key={role.id}
              value={role.id}
            >
              {role.name}
            </option>
          ))}
        </select>
      </div>

      <br />

      <div>
        <label>Tenant: </label>

        <select
          value={userForm.tenant_id}
          onChange={(e) =>
            setUserForm({
              ...userForm,
              tenant_id: e.target.value,
            })
          }
        >
          <option value="">
            Select Tenant
          </option>

          {tenants.map((tenant) => (
            <option
              key={tenant.id}
              value={tenant.id}
            >
              {tenant.name}
            </option>
          ))}
        </select>
      </div>

      <br />

      <button onClick={handleCreateUser}>
        Create User
      </button>

      {/* ================= USERS ================= */}

      <hr />

      <h2>👥 Users</h2>

      {users.length === 0 ? (
        <p>No users found.</p>
      ) : (
        users.map((user) => (
          <div key={user.id}>
            <h3>{user.username}</h3>

            <p>
              User ID: {user.id}
            </p>

            <p>
              Role: {getRoleName(user.role_id)}
            </p>

            <p>
              Tenant: {getTenantName(user.tenant_id)}
            </p>

            {getRoleName(user.role_id) !== "admin" && (
              <button
                onClick={() => handleDeleteUser(user.id)}
              >
                Delete User
              </button>
            )}

            <hr />
          </div>
        ))
      )}

      {loading && <p>Loading...</p>}
    </div>
  );
}

export default AdminDashboard;