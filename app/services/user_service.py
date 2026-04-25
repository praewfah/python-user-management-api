from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserListResponse, UserResponse, UserUpdate


class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def list_users(self, query: str, start: int, limit: int):
        users = self.repository.list_active_users(query=query, start=start, limit=limit)
        total = self.repository.count_active_users(query=query)
        page = (start // limit) + 1
        total_pages = (total + limit - 1) // limit if total > 0 else 0
        return UserListResponse(
            items=[UserResponse.model_validate(user) for user in users],
            total=total,
            page=page,
            total_pages=total_pages,
        )

    def get_user_or_404(self, user_id: int):
        user = self.repository.get_active_by_id(user_id=user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user

    def create_user(self, payload: UserCreate):
        try:
            return self.repository.create_user(
                name=payload.name,
                age=payload.age,
                email=payload.email,
                avatar_url=payload.avatarUrl,
            )
        except IntegrityError:
            # rollback ทันทีเมื่อ unique constraint fail เพื่อให้ session กลับมาใช้งานต่อได้
            self.repository.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists in the system",
            ) from None

    def update_user(self, user_id: int, payload: UserUpdate):
        user = self.get_user_or_404(user_id=user_id)
        try:
            return self.repository.update_user(
                user,
                name=payload.name,
                age=payload.age,
                email=payload.email,
                avatar_url=payload.avatarUrl,
            )
        except IntegrityError:
            # กรณีแก้ไขแล้วชน email เดิมของ user คนอื่น
            self.repository.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists in the system",
            ) from None

    def delete_user(self, user_id: int):
        user = self.repository.get_by_id(user_id=user_id)
        if not user:
            return {"status": "failed", "message": "User not found"}
        if user.deleted_at is not None:
            return {"status": "failed", "message": "User already deleted"}
        self.repository.soft_delete_user(user)
        return {"status": "success"}
