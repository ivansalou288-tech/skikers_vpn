"""Учёт переходов и покупок по реферальной ссылке ?start=merch"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime, create_engine, func
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import IntegrityError

MERCH_SOURCE = "merch"

Base = declarative_base()
engine = create_engine("sqlite:///vpn_bot.db", echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class MerchUser(Base):
    __tablename__ = "merch_users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, index=True)
    username = Column(String, nullable=True)
    registered_at = Column(DateTime, default=datetime.utcnow)


class MerchSale(Base):
    __tablename__ = "merch_sales"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    amount = Column(Float, nullable=False)
    months = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)


def register_merch_visit(user_id: int, username: str = None) -> bool:
    """Регистрирует переход по ссылке merch. True — новый пользователь."""
    db = SessionLocal()
    try:
        record = MerchUser(user_id=user_id, username=username)
        db.add(record)
        db.commit()
        return True
    except IntegrityError:
        db.rollback()
        existing = db.query(MerchUser).filter(MerchUser.user_id == user_id).first()
        if existing and username and existing.username != username:
            existing.username = username
            db.commit()
        return False
    finally:
        db.close()


def is_merch_user(user_id: int) -> bool:
    db = SessionLocal()
    try:
        return db.query(MerchUser).filter(MerchUser.user_id == user_id).first() is not None
    finally:
        db.close()


def record_merch_sale(user_id: int, amount: float, months: int) -> bool:
    """Записывает покупку, если пользователь пришёл по ссылке merch."""
    if not is_merch_user(user_id):
        return False
    db = SessionLocal()
    try:
        db.add(MerchSale(user_id=user_id, amount=float(amount), months=int(months)))
        db.commit()
        return True
    finally:
        db.close()


def get_merch_stats() -> dict:
    db = SessionLocal()
    try:
        visits = db.query(func.count(MerchUser.id)).scalar() or 0
        buyers = db.query(func.count(func.distinct(MerchSale.user_id))).scalar() or 0
        purchases = db.query(func.count(MerchSale.id)).scalar() or 0
        total_revenue = db.query(func.coalesce(func.sum(MerchSale.amount), 0)).scalar() or 0
        return {
            "visits": visits,
            "buyers": buyers,
            "purchases": purchases,
            "total_revenue": float(total_revenue),
        }
    finally:
        db.close()
