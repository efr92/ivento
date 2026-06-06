import httpx
from fastapi import HTTPException, Header, status
from app.core.config import settings


async def get_current_user(
    authorization: str = Header(..., alias="Authorization")
) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )

    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.get(
                f"{settings.AUTH_SERVICE_URL}/api/v1/auth/verify",
                headers={"Authorization": authorization}
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token"
                )
            return response.json()
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Auth service unavailable"
            )
