from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Ebook(Base):
    __tablename__ = "ebooks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    author: Mapped[str] = mapped_column(String(200), default="Unknown")
    filename: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
