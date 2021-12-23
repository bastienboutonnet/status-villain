from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey

from status_villain.database import SQLAlchemyBase


class User(SQLAlchemyBase):
    __tablename__ = "users"
    id = Column(String)
    email = Column(String, primary_key=True)
    # TODO: warn the user about the charactere limit on user so that we dont
    # have to handle this through a db error
    username = Column(String(50))
    password = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    created_at = Column(DateTime)

    # relationships
    status_reports = relationship("Message", back_populates="user")


class Message(SQLAlchemyBase):
    __tablename__ = "status_reports"
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.email"))
    created_at = Column(DateTime)
    today_message = Column(String)
    yesterday_message = Column(String)
    has_completed_yesterday = Column(Boolean)

    # relationships
    user = relationship("User", back_populates="status_reports")


# Orgnanisation Table?
