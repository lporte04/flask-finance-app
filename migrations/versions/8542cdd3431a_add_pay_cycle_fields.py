"""add pay cycle fields

Revision ID: 8542cdd3431a
Revises: 4f7868ed03ba
Create Date: 2025-04-30 23:34:31.515011

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8542cdd3431a'
down_revision = '4f7868ed03ba'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('account', schema=None) as batch_op:
        batch_op.add_column(sa.Column('pay_frequency', sa.String(length=10), nullable=True))
        batch_op.add_column(sa.Column('pay_day_of_week', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('last_pay_credit', sa.Date(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('account', schema=None) as batch_op:
        batch_op.drop_column('last_pay_credit')
        batch_op.drop_column('pay_day_of_week')
        batch_op.drop_column('pay_frequency')

    # ### end Alembic commands ###
