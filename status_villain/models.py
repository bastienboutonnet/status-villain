from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.sql.schema import ForeignKey

from status_villain.database import SQLAlchemyBase

# users table
# # user_id PK
# # user_name
# # created_at


class User(SQLAlchemyBase):
    __tablename__ = "user"
    id = Column(String)
    email = Column(String, primary_key=True)
    # TODO: warn the user about the charactere limit on user so that we dont
    # have to handle this through a db error
    username = Column(String(50))
    password = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    created_at = Column(DateTime)


# standup messages table
# # message_id PK
# # user_id FK on users table
# # created_at
# # message_content


class Message(SQLAlchemyBase):
    __tablename__ = "message"
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("user.email"))
    created_at = Column(DateTime)
    today_message = Column(String)
    yesterday_message = Column(String)
    has_completed_yesterday = Column(Boolean)


# Orgnanisation Table?
