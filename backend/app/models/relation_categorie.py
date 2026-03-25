"""Modelo ORM para relación entre categorías y entidades tipadas."""

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RelationCategorie(Base):
    """Relación genérica entre una categoría y una entidad identificada por tipo/id."""

    __tablename__ = "relation_categorie"
    __table_args__ = (
        CheckConstraint("type IN ('SCENARIO','SIMULATION')", name="relation_categorie_type"),
        UniqueConstraint(
            "id_categorie",
            "type",
            "id_relation",
            name="relation_categorie_unique_relation",
        ),
        Index("ix_relation_categorie_id_categorie", "id_categorie"),
        Index("ix_relation_categorie_type_id_relation", "type", "id_relation"),
        {"schema": "osemosys"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_categorie: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("osemosys.categorie.id", ondelete="RESTRICT"),
        nullable=False,
    )
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    id_relation: Mapped[int] = mapped_column(Integer, nullable=False)
