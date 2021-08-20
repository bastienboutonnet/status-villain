import uuid
from abc import ABC
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import questionary
import yaml
from pydantic import BaseModel
from rich.console import Console
from rich.markdown import Markdown
from sqlalchemy.exc import IntegrityError

from status_villain.commands import check_password, create_user
from status_villain.database import database_connector
from status_villain.models import Message, User

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
            # TODO: Maybe I should look into importing those prompts from the init task
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
        # we will need to check that there are credentials or ask for user to log in.
        self.attempt_login()

    @staticmethod
    def calculate_streak_length(user_reports: List[Message]) -> int:
        completion_list = [message.has_completed_yesterday for message in user_reports]
        streak_length = 0
        for i in completion_list:
            if i:
                streak_length += 1
            else:
                break
        return streak_length

    def get_user_report_messages(self):
        with database_connector.session_manager() as session:
            user_status_reports = (
                session.query(Message)
                .filter(Message.user_id == self.credentials.email)
                .order_by(Message.created_at.desc())
                .all()
            )
            if user_status_reports is not None:
                streak_length = self.calculate_streak_length(user_reports=user_status_reports)
                if streak_length > 1:
                    streak_celebration_prefix = (
                        f"\n:sports_medal: You're on a [purple][bold]{streak_length}[/purple][/bold]-day "
                        "completion streak! Keep it up!\n"
                    )
                    console.print(streak_celebration_prefix, justify="center")
                md_message = f"# Yesterday\n{user_status_reports[0].today_message}"
                md_message = Markdown(md_message)
                console.print(md_message)
                # this is to hack a new line because markdown conversion removes it anyway
                console.print("\n")
                return user_status_reports[0].today_message
            return None

    def update_user_report(self, yesterday_message: Optional[str]):
        message_id = uuid.uuid1()
        try:
            today_report_message = questionary.text(
                message="What are you planning to do today?", multiline=True
            ).unsafe_ask()
            has_completed_yesterday = False
            if yesterday_message:
                has_completed_yesterday = questionary.confirm(
                    "Did you complete all of yesterday's goals?"
                ).unsafe_ask()
            elif has_completed_yesterday is False or yesterday_message is None:
                yesterday_message = questionary.text(
                    message="What did you do yesterday?", multiline=True
                ).unsafe_ask()

        except KeyboardInterrupt:
            console.print("[red]Status report interrupted by user. Nothing saved.")
            return None

        report = Message(
            id=message_id,
            user_id=self.credentials.email,
            created_at=datetime.utcnow(),
            today_message=today_report_message,
            yesterday_message=yesterday_message,
            has_completed_yesterday=has_completed_yesterday,
        )

        with database_connector.session_manager() as session:
            try:
                session.add(report)
                session.commit()
                console.print(
                    "Status report [green]completed[/green]. [purple]Have a fantastic day![/purple]"
                )
            except IntegrityError:
                print(f"A report with {message_id} already exists")
                return

    def run(self):
        # get the potential previous status report for this user.
        user_last_status_report = self.get_user_report_messages()
        self.update_user_report(yesterday_message=user_last_status_report)
