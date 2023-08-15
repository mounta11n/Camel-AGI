"""empty message

Revision ID: b8c29a59e102
Revises: 
Create Date: 2023-08-15 03:11:47.750824

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b8c29a59e102'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('admin',
    sa.Column('id', sa.String(length=100), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=True),
    sa.Column('email', sa.String(length=100), nullable=True),
    sa.Column('google_id', sa.String(length=100), nullable=True),
    sa.Column('openai_key', sa.String(length=100), nullable=True),
    sa.Column('profile_image', sa.String(length=100000), nullable=True),
    sa.Column('password', sa.String(length=100), nullable=True),
    sa.Column('created_date', sa.DateTime(), nullable=True),
    sa.Column('gpt_model', sa.String(), server_default='gpt-4-0613', nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_admin'))
    )
    with op.batch_alter_table('admin', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_admin_email'), ['email'], unique=True)

    op.create_table('agent_session',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('role_1', sa.String(length=200), server_default='', nullable=True),
    sa.Column('role_2', sa.String(length=200), server_default='', nullable=True),
    sa.Column('task', sa.String(length=3000), server_default='', nullable=True),
    sa.Column('user_store', sa.String(), server_default='', nullable=True),
    sa.Column('assistant_store', sa.String(), server_default='', nullable=True),
    sa.Column('admin_id', sa.String(length=100), nullable=True),
    sa.ForeignKeyConstraint(['admin_id'], ['admin.id'], name=op.f('fk_agent_session_admin_id_admin')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_agent_session'))
    )
    with op.batch_alter_table('agent_session', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_agent_session_admin_id'), ['admin_id'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('agent_session', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_agent_session_admin_id'))

    op.drop_table('agent_session')
    with op.batch_alter_table('admin', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_admin_email'))

    op.drop_table('admin')
    # ### end Alembic commands ###
