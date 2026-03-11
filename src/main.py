from fastapi import FastAPI, Depends
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.responses import JSONResponse

from src.database.models import UserModel
from src.routes import (
    accounts_router,
    profiles_router,
    movie_router,
    cart_router,
    orders_router,
    payments_router,
    movie_interaction_router,
)

from src.security.http import get_current_active_user

app = FastAPI(title="Online Cinema Fast API", description="Online cinema Platform")

api_version_prefix = "/api/v1"

app.include_router(
    accounts_router, prefix=f"{api_version_prefix}/accounts", tags=["accounts"]
)
app.include_router(
    profiles_router, prefix=f"{api_version_prefix}/profiles", tags=["profiles"]
)
app.include_router(movie_router, prefix=api_version_prefix, tags=["movies"])
app.include_router(cart_router, prefix=f"{api_version_prefix}/cart", tags=["cart"])
app.include_router(
    orders_router, prefix=f"{api_version_prefix}/orders", tags=["orders"]
)
app.include_router(
    payments_router, prefix=f"{api_version_prefix}/payments", tags=["payments"]
)
app.include_router(
    movie_interaction_router, prefix=api_version_prefix, tags=["movie-interactions"]
)


@app.get(f"{api_version_prefix}/openapi.json", include_in_schema=False)
async def protected_openapi(_: UserModel = Depends(get_current_active_user)):
    return JSONResponse(app.openapi())


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html(_: UserModel = Depends(get_current_active_user)):
    return get_swagger_ui_html(
        openapi_url=f"{api_version_prefix}/openapi.json",
        title=f"{app.title} - Swagger UI",
    )


@app.get("/redoc", include_in_schema=False)
async def redoc_html(_: UserModel = Depends(get_current_active_user)):
    return get_redoc_html(
        openapi_url=f"{api_version_prefix}/openapi.json",
        title=f"{app.title} - ReDoc",
    )
