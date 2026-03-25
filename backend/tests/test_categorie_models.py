from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Categorie, RelationCategorie


def test_categorie_name_is_case_insensitive_unique(db_session) -> None:
    db_session.add(Categorie(name="Solar"))
    db_session.commit()

    db_session.add(Categorie(name="solar"))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_categorie_name_cannot_be_blank(db_session) -> None:
    db_session.add(Categorie(name="   "))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_relation_categorie_rejects_invalid_type_and_duplicates(db_session) -> None:
    categorie = Categorie(name="Storage")
    db_session.add(categorie)
    db_session.commit()

    relation = RelationCategorie(id_categorie=categorie.id, type="SCENARIO", id_relation=123)
    db_session.add(relation)
    db_session.commit()

    db_session.add(RelationCategorie(id_categorie=categorie.id, type="USER", id_relation=123))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    db_session.add(RelationCategorie(id_categorie=categorie.id, type="SCENARIO", id_relation=123))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
