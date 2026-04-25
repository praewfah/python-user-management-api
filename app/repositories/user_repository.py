from datetime import datetime
from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, load_only

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_active_users(self, query: str, start: int, limit: int) -> list[User]:
        base_stmt = (
            select(User)
            .options(load_only(User.id, User.name, User.age, User.email, User.avatar_url))
            .where(User.deleted_at.is_(None))
        )

        normalized_query = query.strip().lower()
        stmt = base_stmt
        if normalized_query and len(normalized_query) >= 3:
            # ค้นหาแบบ contains เพื่อให้ผลลัพธ์ครบ
            escaped_query = (
                normalized_query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            )
            contains_keyword = f"%{escaped_query}%"
            name_col = func.lower(User.name)
            email_col = func.lower(User.email)
            contains_filter = or_(
                name_col.like(contains_keyword, escape="\\"),
                email_col.like(contains_keyword, escape="\\"),
            )
            stmt = base_stmt.where(contains_filter).order_by(User.id.asc())
        else:
            # กำหนดลำดับก่อน pagination เพื่อให้ผลลัพธ์คงที่ทุกครั้ง
            stmt = stmt.order_by(User.id.asc())

        stmt = stmt.offset(start).limit(limit)
        return self.db.scalars(stmt).all()

    def count_active_users(self, query: str) -> int:
        stmt = select(func.count(User.id)).where(User.deleted_at.is_(None))
        normalized_query = query.strip().lower()
        if normalized_query and len(normalized_query) >= 3:
            escaped_query = (
                normalized_query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            )
            contains_keyword = f"%{escaped_query}%"
            name_col = func.lower(User.name)
            email_col = func.lower(User.email)
            stmt = stmt.where(
                or_(
                    name_col.like(contains_keyword, escape="\\"),
                    email_col.like(contains_keyword, escape="\\"),
                )
            )
        total = self.db.scalar(stmt)
        return int(total or 0)

    def get_active_by_id(self, user_id: int) -> Optional[User]:
        user = self.db.get(User, user_id)
        if not user or user.deleted_at is not None:
            return None
        return user

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.get(User, user_id)

    def create_user(self, *, name: str, age: int, email: str, avatar_url: str) -> User:
        user = User(name=name, age=age, email=email, avatar_url=avatar_url)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_user(self, user: User, *, name: str, age: int, email: str, avatar_url: str) -> User:
        user.name = name
        user.age = age
        user.email = email
        user.avatar_url = avatar_url
        self.db.commit()
        self.db.refresh(user)
        return user

    def soft_delete_user(self, user: User) -> None:
        user.deleted_at = datetime.utcnow()
        self.db.commit()
