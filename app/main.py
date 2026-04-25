from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.api.router import api_router

app = FastAPI(title="User Management API")
app.include_router(api_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.exception_handler(Exception)
def handle_unexpected_error(request: Request, exc: Exception):
    # บังคับรูปแบบ response ให้เหมือนกันเสมอ เมื่อเกิด error ที่ไม่คาดคิด
    # เพื่อให้ฝั่ง frontend/ผู้ตรวจงาน parse ผลลัพธ์ได้ง่าย
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "failed",
            "message": "Unexpected server error",
        },
    )
