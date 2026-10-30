from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Health check")
def health_check():
    """Health check endpoint indicating service availability."""
    return {"status": "ok", "app": "NextShift"}
