from abc import ABC
from pathlib import Path
from typing import Dict

import questionary
import yaml
from pydantic import BaseModel
from rich.console import Console

from status_villain.commands import check_password, create_user
from status_villain.database import database_connector
from status_villain.models import User

console = Console()

DEFAULT_PROFILES_DIR = Path("~/.status_villain/").expanduser().resolve()
DEFAULT_PROFILES_FILE = DEFAULT_PROFILES_DIR.joinpath("credentials.yaml")


def make_dir(path: Path):
    """Creates a directory.
    Args:
        path (Path): Where you want it to be.
    """
    # logger.debug(f"Making folder: {path}")
    path.mkdir()


def make_file(path: Path, contents: Dict[str, str]):
    """Creates a text file with potential things in it. WOW!
    Args:
        path (Path): Where you want it to be
        contents (str, optional): What you want to put in that text file. Defaults to str().
    """
    # logger.debug(f"Making file: {path}")
    with open(path, "w") as outfile:
        yaml.dump(contents, outfile)


class CredentialsFilesAlreadyPopulated(Exception):
    """When the credentials file is already created."""


class UserInfoInputModel(BaseModel):
    first_name: str
    last_name: str
    password: str
    username: str
    email: str


class InteractiveLoginInputModel(BaseModel):
    email: str
    username: str
    password: str


class BaseTask(ABC):
    def __init__(self):
        self.is_authed_user: bool = False

    def run(self):
        ...

    def attempt_login(self):
        _credentials = {}
        if DEFAULT_PROFILES_FILE.exists():
            with open(DEFAULT_PROFILES_FILE, "r") as file:
                _credentials = yaml.safe_load(file)
                self.credentials = UserInfoInputModel(**_credentials)
        else:
            login_prompts = [
                {"type": "text", "name": "email", "message": "e-mail address"},
                {"type": "text", "name": "username", "message": "Username"},
                {"type": "password", "name": "password", "message": "Password"},
            ]
            user_info = questionary.prompt(login_prompts)
            self.credentials = InteractiveLoginInputModel(**user_info)

        if self.credentials:
            self.is_authed_user = self.authenticate()
            if self.is_authed_user is False:
                console.print("Could not authenticate, check your credentials")
        else:
            return

    def authenticate(self) -> bool:
        with database_connector.session_manager() as session:
            user_password = (
                session.query(User.password)
                .filter(
                    User.email == self.credentials.email, User.username == self.credentials.username
                )
                .first()
            )
            if user_password:
                stored_password = user_password[0]
                is_valid_user = check_password(stored_password, self.credentials.password)
                return is_valid_user
            else:
                return False


class InitTask(BaseTask):
    def __init__(self):
        self.username: str
        self.first_name: str
        self.last_name: str
        self.password: str
        self.user_info: UserInfoInputModel

    def create_profiles_dir(self):
        if not DEFAULT_PROFILES_DIR.exists():
            make_dir(DEFAULT_PROFILES_DIR)

    def create_profiles_file(self):
        if not DEFAULT_PROFILES_FILE.exists():
            make_file(DEFAULT_PROFILES_FILE, self.user_info.dict())
        else:
            response = questionary.confirm(
                f"A credentials file already exists at {DEFAULT_PROFILES_FILE}. Do you want to overwrite it?"
            ).ask()
            if response is True:
                make_file(DEFAULT_PROFILES_FILE, self.user_info.dict())
            else:
                raise CredentialsFilesAlreadyPopulated(
                    f"A credentials file already exists at {DEFAULT_PROFILES_FILE}. "
                    "Please update it with your new credentials if they have changed"
                )

    def persist_credentials(self):
        if self.user_info is not None:
            self.create_profiles_dir()
            self.create_profiles_file()
        else:
            raise AttributeError("user_info was not filled in")

    def run(self):
        questions = [
            {"type": "text", "name": "email", "message": "Please provide your email address"},
            {"type": "text", "name": "first_name", "message": "What is your first name?"},
            {"type": "text", "name": "last_name", "message": "What is your last name?"},
            {"type": "text", "name": "username", "message": "Choose your user name?"},
            {
                "type": "password",
                "name": "password",
                "message": "Choose your password? Make it hard to guess.",
            },
        ]
        console.print("Let's get you started, with creating your user profile")
        user_info = questionary.prompt(questions)
        self.user_info = UserInfoInputModel(**user_info)

        self.username = self.user_info.username
        self.first_name = self.user_info.first_name
        self.last_name = self.user_info.last_name
        self.password = self.user_info.password
        self.email = self.user_info.email
        create_user(self.email, self.username, self.first_name, self.last_name, self.password)
        self.persist_credentials()
        console.print("You're all set")


class ReportTask(BaseTask):
    def __init__(self) -> None:
        ...

    def run(self):
        self.attempt_login()
        # we will need to check that there are credentials or ask for user to log in.

        # get the potential previous status report for this user.

        # if we have it display it in a nice fashion using `rich` markdown rendering capabilities

        # did you complete all your tasks from yesterday
        #    # if so, we will set a "completed" boolean --which is going to be nice to display streaks
        #    # and we will pre-fill yesterdays message for "today" with the content of yeterday.
        #    # if not, we pop a txt editor and allow the user to write an amended version of his yesterday status.

        # pop an editor again to ask for TODAY's update.

        # persist reports to the messages tables.
