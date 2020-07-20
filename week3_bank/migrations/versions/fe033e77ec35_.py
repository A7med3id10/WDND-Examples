"""empty message

Revision ID: fe033e77ec35
Revises: 0428bc583bae
Create Date: 2020-07-20 23:44:50.664069

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fe033e77ec35'
down_revision = '0428bc583bae'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###

    # HANDLING MIGRATIONS OF ADDING A NEW ATTRIBUTE TO CLASS
    op.add_column('user_account', sa.Column(
        'last_name', sa.String(), nullable=True))
    op.execute('UPDATE user_account SET last_name = \'\' where last_name is NULL;')
    op.alter_column('user_account', 'last_name', nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user_account', 'last_name')
    # ### end Alembic commands ###
