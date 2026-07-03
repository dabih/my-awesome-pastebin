from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Category(Base):
    __tablename__ = "pastes_category"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    pastes: Mapped[list["Paste"]] = relationship(back_populates="category")


class Paste(Base):
    __tablename__ = "pastes_paste"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    uid: Mapped[str] = mapped_column(String(21), unique=True)
    title: Mapped[str] = mapped_column(String(200))
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("pastes_category.id"))
    expiration_datetime: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    password: Mapped[str | None] = mapped_column(String(100), nullable=True)
    burn_after_read: Mapped[bool] = mapped_column(Boolean, default=False)
    syntax: Mapped[str] = mapped_column(String(50), default="plain")
    raw_data: Mapped[str] = mapped_column(Text)
    deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    category: Mapped[Category] = relationship(back_populates="pastes")
    visit_count: Mapped["VisitCount | None"] = relationship(back_populates="paste", uselist=False)


class VisitCount(Base):
    __tablename__ = "pastes_visitcount"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    paste_id: Mapped[int] = mapped_column(Integer, ForeignKey("pastes_paste.id"), unique=True)
    count: Mapped[int] = mapped_column(Integer, default=0)
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    paste: Mapped[Paste] = relationship(back_populates="visit_count")
