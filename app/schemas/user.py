from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator

EMAIL_REGEX = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"


class UserBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    age: StrictInt = Field(ge=0)
    email: str = Field(pattern=EMAIL_REGEX, max_length=255)
    avatarUrl: str = Field(min_length=1, max_length=2048)

    @field_validator("name", "avatarUrl")
    @classmethod
    def strip_and_validate(cls, value: str) -> str:
        # ตัดช่องว่างหัวท้ายก่อน validate เพื่อกันข้อมูลที่ดูเหมือนมีค่าแต่เป็นช่องว่างล้วน
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be empty")
        return stripped

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        # normalize email ให้เป็นรูปแบบเดียวกันก่อนเข้า DB (ลดปัญหาซ้ำต่างตัวพิมพ์)
        return value.strip().lower()


class UserCreate(UserBase):
    pass


class UserUpdate(UserBase):
    pass


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    age: int
    email: str
    avatarUrl: str = Field(alias="avatar_url")


class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    total_pages: int = Field(ge=0)
