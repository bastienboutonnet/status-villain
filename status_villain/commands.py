import binascii
import hashlib
import os
import uuid
from datetime import datetime

from sqlalchemy.exc import IntegrityError

from status_villain.database import database_connector
from status_villain.models import User


def hash_password(password):
    """Hash a password for storing."""
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode("ascii")
    pwdhash = hashlib.pbkdf2_hmac("sha512", password.encode("utf-8"), salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash).decode("ascii")


def check_password(stored_password, provided_password):
    """Verify a stored password against one provided by user"""
    salt = stored_password[:64]
    stored_password = stored_password[64:]
    pwdhash = hashlib.pbkdf2_hmac(
        "sha512", provided_password.encode("utf-8"), salt.encode("ascii"), 100000
    )
    pwdhash = binascii.hexlify(pwdhash).decode("ascii")
    return pwdhash == stored_password


def create_user(email: str, username: str, first_name: str, last_name: str, password: str):
    user_id = uuid.uuid1()
    hashed_password = hash_password(password)
    user = User(
        id=user_id,
        email=email,
        username=username,
        first_name=first_name,
        password=hashed_password,
        last_name=last_name,
        created_at=datetime.utcnow(),
    )

    with database_connector.session_manager() as session:
        try:
            session.add(user)
            session.commit()
        except IntegrityError:
            print("An account already exists under that email address. Please log in.")
            return
