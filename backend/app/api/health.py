from fastapi import APIRouter

from app import __version__

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok", "version": __version__}


@router.get("/version")
def version():
    return {"version": __version__, "name": "csv-rescue"}
