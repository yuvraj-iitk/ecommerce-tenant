import requests
import os
from dotenv import load_dotenv

load_dotenv()

KEYCLOAK_URL = "http://localhost:8080"
REALM = "ecommerce"

ADMIN_USERNAME = os.getenv("KEYCLOAK_ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("KEYCLOAK_ADMIN_PASSWORD")


# =========================================================
# GET KEYCLOAK ADMIN TOKEN
# =========================================================

def get_admin_token():
    url = f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token"

    data = {
        "client_id": "admin-cli",
        "username": ADMIN_USERNAME,
        "password": ADMIN_PASSWORD,
        "grant_type": "password"
    }

    response = requests.post(url, data=data)

    if response.status_code != 200:
        raise Exception(
            f"Could not get Keycloak admin token: {response.text}"
        )

    return response.json()["access_token"]


# =========================================================
# CREATE KEYCLOAK USER
# =========================================================

def create_keycloak_user(username, password, role_name=None):

    token = get_admin_token()

    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/users"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    user_data = {
        "username": username,
        "enabled": True,
        "email": f"{username}@example.com",
        "firstName": username,
        "lastName": "User",
        "emailVerified": True,
        "requiredActions": [],
        "credentials": [
            {
                "type": "password",
                "value": password,
                "temporary": False
            }
        ]
    }

    # Create user
    response = requests.post(
        url,
        headers=headers,
        json=user_data
    )

    if response.status_code not in [201, 204]:
        raise Exception(
            f"Keycloak user creation failed: {response.text}"
        )

    # =====================================================
    # GET CREATED USER ID
    # =====================================================

    search_url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/users"

    search_response = requests.get(
        search_url,
        headers=headers,
        params={
            "username": username,
            "exact": "true"
        }
    )

    if search_response.status_code != 200:
        raise Exception(
            f"Could not find created Keycloak user: "
            f"{search_response.text}"
        )

    users = search_response.json()

    if not users:
        raise Exception(
            "User was created but could not be found"
        )

    keycloak_user_id = users[0]["id"]

    # =====================================================
    # ASSIGN REALM ROLE
    # =====================================================

    if role_name:

        role_url = (
            f"{KEYCLOAK_URL}/admin/realms/"
            f"{REALM}/roles/{role_name}"
        )

        role_response = requests.get(
            role_url,
            headers=headers
        )

        if role_response.status_code != 200:
            raise Exception(
                f"Keycloak role '{role_name}' not found: "
                f"{role_response.text}"
            )

        role = role_response.json()

        mapping_url = (
            f"{KEYCLOAK_URL}/admin/realms/"
            f"{REALM}/users/{keycloak_user_id}/"
            f"role-mappings/realm"
        )

        mapping_response = requests.post(
            mapping_url,
            headers=headers,
            json=[
                {
                    "id": role["id"],
                    "name": role["name"]
                }
            ]
        )

        if mapping_response.status_code != 204:
            raise Exception(
                f"Could not assign role '{role_name}': "
                f"{mapping_response.text}"
            )

    return True


# =========================================================
# DELETE KEYCLOAK USER
# =========================================================

def delete_keycloak_user(username):

    token = get_admin_token()

    search_url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/users"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(
        search_url,
        headers=headers,
        params={
            "username": username,
            "exact": "true"
        }
    )

    if response.status_code != 200:
        raise Exception(
            f"Could not find Keycloak user: {response.text}"
        )

    users = response.json()

    if not users:
        raise Exception("Keycloak user not found")

    keycloak_user_id = users[0]["id"]

    delete_url = (
        f"{KEYCLOAK_URL}/admin/realms/{REALM}/users/"
        f"{keycloak_user_id}"
    )

    delete_response = requests.delete(
        delete_url,
        headers=headers
    )

    if delete_response.status_code != 204:
        raise Exception(
            f"Keycloak user deletion failed: "
            f"{delete_response.text}"
        )

    return True