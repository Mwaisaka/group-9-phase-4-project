"""corrected typos

Revision ID: 404a8893011a
Revises: e55a1efeadb7
Create Date: 2024-03-26 21:02:56.537022

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '404a8893011a'
down_revision = 'e55a1efeadb7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('_alembic_tmp_salaries')
    with op.batch_alter_table('salaries', schema=None) as batch_op:
        batch_op.add_column(sa.Column('amount_usd', sa.Numeric(precision=10, scale=2), nullable=True))
        batch_op.drop_column('amount')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('salaries', schema=None) as batch_op:
        batch_op.add_column(sa.Column('amount', sa.NUMERIC(precision=10, scale=2), nullable=True))
        batch_op.drop_column('amount_usd')

    op.create_table('_alembic_tmp_salaries',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('amount_usd', sa.NUMERIC(precision=10, scale=2), nullable=True),
    sa.Column('employee_id', sa.INTEGER(), nullable=False),
    sa.Column('pay_date', sa.DATE(), nullable=True),
    sa.Column('description', sa.VARCHAR(length=255), nullable=True),
    sa.ForeignKeyConstraint(['employee_id'], ['users.id'], name='fk_salaries_employee_id_users'),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###
