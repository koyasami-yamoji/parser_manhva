from typing import List

from sqlalchemy.exc import NoResultFound, IntegrityError, PendingRollbackError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, update, select
from sqlalchemy.orm import selectinload

from db.models import Manhva, User, ManhvaUserAssociation
from utils.manhva_names import manhva_names


async def add_manhva(names: List[str], user_id: int, session: AsyncSession):
    user = await get_or_create_user(session=session, user_id=user_id)
    for name in names:
        manhva = await get_or_create_manhva(session=session, manhva_name=name)
        user.manhva_details.append(ManhvaUserAssociation(manhva=manhva))
        try:
            await session.commit()
        except (IntegrityError, PendingRollbackError):
            continue
    await manhva_names.refresh_list()


async def delete_manhva(name: str, user_id: int, session: AsyncSession):
    await session.execute(
        delete(Manhva).where((Manhva.user_id == user_id) & (Manhva.manhva_name == name))
    )
    await manhva_names.refresh_list()
    await session.commit()


async def get_or_create_user(session: AsyncSession, user_id: int):
    stmt = (
        select(User)
        .where(User.user_id == user_id)
        .options(selectinload(User.manhva_details))
    )
    instance = await session.scalars(stmt)

    try:
        return instance.one()
    except NoResultFound:
        new_user = User(user_id=user_id)
        session.add(new_user)
        await session.commit()
        return new_user


async def get_or_create_manhva(session: AsyncSession, manhva_name: str):
    stmt = select(Manhva).where(Manhva.manhva_name == manhva_name)
    instance = await session.scalars(stmt)
    try:
        return instance.one()
    except NoResultFound:
        instance = Manhva(manhva_name=manhva_name)
        session.add(instance)
        await session.commit()
        print("manhva", instance)
        return instance
