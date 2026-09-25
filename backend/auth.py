from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
import requests

KEYCLOAK_URL = "http://localhost:8080"
REALM = "ecommerce"

ISSUER = f"{KEYCLOAK_URL}/realms/{REALM}"
JWKS_URL = f"{ISSUER}/protocol/openid-connect/certs"

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    try:
        # Keycloak ki public keys
        jwks = requests.get(JWKS_URL).json()

        # Token ka header
        header = jwt.get_unverified_header(token)

        # Token kis key se sign hua hai
        kid = header["kid"]

        key = next(
            k for k in jwks["keys"]
            if k["kid"] == kid
        )

        # Token verify
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            issuer=ISSUER,
            options={"verify_aud": False}
        )

        return payload

    except Exception as e:
        print("JWT ERROR:", e)
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

def require_role(required_role: str):
    def role_checker(
        user=Depends(get_current_user)
    ):
        roles = user.get("realm_access", {}).get("roles", [])

        if required_role not in roles:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission"
            )

        return user

    return role_checker    