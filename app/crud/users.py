from sqlalchemy.future import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import selectinload
from app.models.users import User
from sqlalchemy.orm.session import Session


async def create_user(db: Session, user_data: dict):
    user = User(**user_data)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


async def read_users(db: Session):
    result = db.execute(select(User).options(selectinload("*")))
    return result.scalars().all()


async def read_user(db: Session, user_id: int):
    result = db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NoResultFound(f"User with ID {user_id} not found.")
    return user


async def read_user_by_identifier(db: Session, identifier: str):
    result = db.execute(
        select(User).where(
            (User.username == identifier)
            | (User.phone == identifier)
            | (User.email == identifier)
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise NoResultFound(f"User with '{identifier}' not found.")
    return user


async def update_user(db: Session, user_id: int, update_data: dict):
    user = await read_user(db, user_id)
    for key, value in update_data.items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


async def delete_user(db: Session, user_id: int):
    user = await read_user(db, user_id)
    db.delete(user)
    db.commit()
    return {"message": f"User with ID {user_id} deleted successfully."}
