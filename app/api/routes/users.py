from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserListResponse, UserResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/api/user", tags=["users"])


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    # ใช้ Dependency Injection เพื่อแยกชั้น route ออกจาก business/data logic
    return UserService(UserRepository(db))


@router.get("", response_model=UserListResponse)
def get_users(
    q: str = Query(default=""),
    start: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    service: UserService = Depends(get_user_service),
):
    return service.list_users(query=q, start=start, limit=limit)


@router.get("/{user_id}", response_model=UserResponse)
def get_user_detail(user_id: int, service: UserService = Depends(get_user_service)):
    return service.get_user_or_404(user_id=user_id)


@router.post("", response_model=UserResponse, status_code=201)
def create_user(payload: UserCreate, service: UserService = Depends(get_user_service)):
    return service.create_user(payload=payload)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, payload: UserUpdate, service: UserService = Depends(get_user_service)):
    return service.update_user(user_id=user_id, payload=payload)


@router.delete("/{user_id}")
def delete_user(user_id: int, service: UserService = Depends(get_user_service)):
    return service.delete_user(user_id=user_id)


@router.post("/restore", response_model=UserResponse)
def restore_user(
    email: str = Query(..., min_length=3, max_length=255),
    service: UserService = Depends(get_user_service),
):
    return service.restore_user_by_email(email=email)
