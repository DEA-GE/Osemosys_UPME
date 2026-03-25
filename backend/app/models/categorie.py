"""Modelo ORM para categorías genéricas."""

from sqlalchemy import CheckConstraint, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Categorie(Base):
    """Catálogo de categorías reutilizable por otras relaciones."""

    __tablename__ = "categorie"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)

    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="categorie_name_not_blank"),
        Index("ux_categorie_name_lower", func.lower(name), unique=True),
        {"schema": "osemosys"},
    )
