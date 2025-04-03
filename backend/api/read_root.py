from fastapi import APIRouter


router = APIRouter()


@router.get("/")
async def read_root():
    """Basic endpoint to check if the server is running."""
    return {"message": "Payment backend is running!"}
