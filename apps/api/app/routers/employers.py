"""Employer records — the full intake form, stored per authenticated user."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..deps import current_user
from ..models import Employer, User
from ..schemas.employer import EmployerCreate, EmployerOut, EmployerUpdate
from ..services.calculations import compute_employer_background

router = APIRouter(prefix="/api/employers", tags=["employers"])


def _apply(data: dict, payload) -> None:
    """Copy incoming fields onto the ORM object, then add computed totals."""
    for field in payload.model_dump(exclude_none=True):
        setattr(data, field, getattr(payload, field))
    background = compute_employer_background(payload.model_dump())
    for field, value in background.items():
        setattr(data, field, value)


@router.get("", response_model=list[EmployerOut])
async def list_employers(
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Employer]:
    result = await db.execute(
        select(Employer).where(Employer.user_id == user.id).order_by(Employer.created_at)
    )
    return list(result.scalars().all())


@router.post("", response_model=EmployerOut, status_code=status.HTTP_201_CREATED)
async def create_employer(
    payload: EmployerCreate,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> Employer:
    employer = Employer(user_id=user.id)
    _apply(employer, payload)
    db.add(employer)
    await db.commit()
    await db.refresh(employer)
    return employer


@router.get("/{employer_id}", response_model=EmployerOut)
async def get_employer(
    employer_id: UUID,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> Employer:
    employer = await _owned(db, employer_id, user.id)
    return employer


@router.patch("/{employer_id}", response_model=EmployerOut)
async def update_employer(
    employer_id: UUID,
    payload: EmployerUpdate,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> Employer:
    employer = await _owned(db, employer_id, user.id)
    _apply(employer, payload)
    await db.commit()
    await db.refresh(employer)
    return employer


@router.delete("/{employer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employer(
    employer_id: UUID,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    employer = await _owned(db, employer_id, user.id)
    await db.delete(employer)
    await db.commit()


async def _owned(db: AsyncSession, employer_id: UUID, user_id: UUID) -> Employer:
    employer = await db.get(Employer, employer_id)
    if employer is None or employer.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Employer not found")
    return employer
