from pathlib import Path
from typing import Dict

import questionary
import yaml
from pydantic import BaseModel
from rich.console import Console

from status_villain.commands import create_user

console = Console()

DEFAULT_PROFILES_DIR = Path("~/.status_villain/").expanduser().resolve()


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


class InitTask:
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
        credentials_file_path = DEFAULT_PROFILES_DIR.joinpath("credentials.yaml")
        if not credentials_file_path.exists():
            make_file(credentials_file_path, self.user_info.dict())
        else:
            response = questionary.confirm(
                "A credentials file already exists at {credentials_file_path}. Do you want to overwrite it?"
            ).ask()
            if response is True:
                make_file(credentials_file_path, self.user_info.dict())
            else:
                raise CredentialsFilesAlreadyPopulated(
                    f"A credentials file already exists at {credentials_file_path}. "
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
