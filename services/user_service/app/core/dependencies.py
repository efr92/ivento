import httpx
from fastapi import HTTPException, Header, status
from app.core.config import settings
from shared.messages import SHARED_MESSAGES


async def get_current_user(
    authorization: str = Header(..., alias="Authorization")
) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=SHARED_MESSAGES["invalid_auth_header"]
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
                    detail=SHARED_MESSAGES["invalid_or_expired_token"]
                )
            return response.json()
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=SHARED_MESSAGES["auth_service_unavailable"]
            )
