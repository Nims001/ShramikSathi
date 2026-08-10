"""Authentication: register, login, logout, and the current user profile."""

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..deps import create_session, current_user
from ..models import Session, User
from ..schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserOut, UserUpdate
from ..security import hash_password, verify_password
from ..services.calculations import age_from_dob

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> AuthResponse:
    username = payload.username.strip()
    existing = await db.execute(select(User).where(User.username == username))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Username already taken")

    user = User(
        username=username,
        password_hash=hash_password(payload.password),
        role=payload.role,
        gender=payload.gender,
        date_of_birth=payload.date_of_birth,
        age=age_from_dob(payload.date_of_birth),
        ethnicity=payload.ethnicity,
        education_level=payload.education_level,
        language=payload.language or "en",
    )
    db.add(user)
    await db.flush()

    token, session = create_session(user.id)
    db.add(session)
    await db.commit()
    await db.refresh(user)

    return AuthResponse(token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> AuthResponse:
    user = (await db.execute(select(User).where(User.username == payload.username.strip()))).scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    token, session = create_session(user.id)
    db.add(session)
    await db.commit()
    await db.refresh(user)

    return AuthResponse(token=token, user=UserOut.model_validate(user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(default=""),
) -> None:
    token = authorization[7:].strip() if authorization.lower().startswith("bearer ") else ""
    if token:
        await db.execute(delete(Session).where(Session.token == token))
        await db.commit()


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(current_user)) -> UserOut:
    return UserOut.model_validate(user)


@router.patch("/me", response_model=UserOut)
async def update_me(
    payload: UserUpdate,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    data = payload.model_dump(exclude_unset=True)
    if "date_of_birth" in data:
        data["age"] = age_from_dob(data["date_of_birth"])
    for field, value in data.items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return UserOut.model_validate(user)
