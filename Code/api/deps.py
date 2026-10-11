from typing import Callable, Optional

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from greendash.security.authz import verify_token


class Principal(BaseModel):
    role: str
    sub: Optional[str] = None


# auto_error=False so a missing header is answered by us, always as 401.
_bearer = HTTPBearer(auto_error=False)
_CHALLENGE = {"WWW-Authenticate": "Bearer"}


def get_principal(creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer)) -> Principal:
    """Authenticate the request from its bearer token. Never trusts anything else."""
    if creds is None or creds.scheme.lower() != "bearer" or not creds.credentials:
        raise HTTPException(status_code=401, detail="Not authenticated", headers=_CHALLENGE)
    try:
        claims = verify_token(creds.credentials)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired", headers=_CHALLENGE)
    except jwt.InvalidSignatureError:
        raise HTTPException(status_code=401, detail="Invalid token signature", headers=_CHALLENGE)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token", headers=_CHALLENGE)
    return Principal(role=claims["role"], sub=claims.get("sub") or None)


def require_role(*roles: str) -> Callable:
    """Dependency: authenticated and one of `roles` (any authenticated role if empty)."""
    def _require_role(principal: Principal = Depends(get_principal)) -> Principal:
        if roles and principal.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return principal
    return _require_role


DEMO_PERSONAS = frozenset(f"CUST-{i:04d}" for i in range(1, 9))


def require_subject(principal: Principal, customer_id: str) -> None:
    """A CUSTOMER may only act on their own customer_id; staff roles are not bound."""
    if principal.role == "CUSTOMER" and (not principal.sub or principal.sub != customer_id):
        raise HTTPException(status_code=403, detail="Cannot access another customer's data")
    # Evaluators (judges) see the eight demo personas only, never the wider customer base.
    if principal.role == "EVALUATOR" and customer_id not in DEMO_PERSONAS:
        raise HTTPException(status_code=403, detail="Evaluators can open demo personas only")


def customer_key_for(customer_id: str) -> str:
    # return the key to be used to fetch from DB
    return customer_id


def db_key_for(customer_id: str) -> str:
    """Pseudonymous key for anything written to the database (audit, scenario runs, feedback, opt-outs).

    A keyed HMAC, so stored rows never carry the customer ID. Uses PSEUDONYM_KEY when set,
    otherwise the signing secret, so it is stable for one deployment.
    """
    import os
    from config.settings import settings
    from security.privacy import pseudonymise
    return "k_" + pseudonymise(customer_id, key=(os.environ.get("PSEUDONYM_KEY") or settings.jwt_secret).encode())

