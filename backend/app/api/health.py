from fastapi import APIRouter, status

from app.db.session import check_db_connection

router = APIRouter(tags=["Health"])


@router.get("/health", status_code=status.HTTP_200_OK)
def health() -> dict[str, str]:
    """
    Check the health of the application.

    Returns:
        A dictionary containing the status of the application.
    """
    return {"status": "ok"}


@router.get("/health/db", status_code=status.HTTP_200_OK)
def health_db() -> dict[str, str]:
    """
    Check the health of the database connection.

    Returns:
        A dictionary containing the status of the database connection.
    """
    if check_db_connection():
        return {"status": "ok"}
    else:
        return {"status": "error"}
