"""categorie and relation_categorie

Revision ID: 20260324_0024
Revises: 20260319_0023
Create Date: 2026-03-24
"""

from alembic import op
import sqlalchemy as sa


revision = "20260324_0024"
down_revision = "20260319_0023"
branch_labels = None
depends_on = None


SCHEMA = "osemosys"


def upgrade() -> None:
    op.create_table(
        "categorie",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.CheckConstraint("length(trim(name)) > 0", name="categorie_name_not_blank"),
        sa.PrimaryKeyConstraint("id"),
        schema=SCHEMA,
    )
    op.create_index(
        "ux_categorie_name_lower",
        "categorie",
        [sa.text("lower(name)")],
        unique=True,
        schema=SCHEMA,
    )

    op.create_table(
        "relation_categorie",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("id_categorie", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("id_relation", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "type IN ('SCENARIO','SIMULATION')",
            name="relation_categorie_type",
        ),
        sa.ForeignKeyConstraint(
            ["id_categorie"],
            ["osemosys.categorie.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "id_categorie",
            "type",
            "id_relation",
            name="relation_categorie_unique_relation",
        ),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_relation_categorie_id_categorie",
        "relation_categorie",
        ["id_categorie"],
        unique=False,
        schema=SCHEMA,
    )
    op.create_index(
        "ix_relation_categorie_type_id_relation",
        "relation_categorie",
        ["type", "id_relation"],
        unique=False,
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_relation_categorie_type_id_relation",
        table_name="relation_categorie",
        schema=SCHEMA,
    )
    op.drop_index(
        "ix_relation_categorie_id_categorie",
        table_name="relation_categorie",
        schema=SCHEMA,
    )
    op.drop_table("relation_categorie", schema=SCHEMA)

    op.drop_index("ux_categorie_name_lower", table_name="categorie", schema=SCHEMA)
    op.drop_table("categorie", schema=SCHEMA)
