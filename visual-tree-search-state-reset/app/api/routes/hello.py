from fastapi import APIRouter
from app.api.controllers.hello_controller import HelloController

router = APIRouter(
    prefix="",
    tags=["hello"]
)
hello_controller = HelloController()

@router.get("", include_in_schema=True)
async def get_hello():
    return hello_controller.get_hello()