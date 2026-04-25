from fastapi import HTTPException
from typing import Optional
from clients import get_client_details


def validate_api_key(x_api_key: Optional[str]):
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key"
        )

    client = get_client_details(x_api_key)

    if not client:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key"
        )

    return client