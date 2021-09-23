from pathlib import Path

import pytest

from status_villain.tasks.tasks import InitTask

TEST_DIR = Path(__file__).resolve().parent


class Question:
    def __init__(self, return_value):
        self._return_value = return_value

    def ask(self):
        return self._return_value


@pytest.mark.datafiles(TEST_DIR)
def test_create_profiles_dir(datafiles):

    profiles_dir_path = datafiles  # noqa: F811

    init_task = InitTask(profiles_dir_path=profiles_dir_path)
    init_task.create_profiles_dir()
    assert Path(profiles_dir_path).exists()


@pytest.mark.datafiles(TEST_DIR)
def test_create_profiles_file(datafiles, mocker):
    from status_villain.tasks.tasks import UserInfoInputModel

    profiles_dir_path = datafiles  # noqa: F811
    profiles_file_path = Path(profiles_dir_path).joinpath("credentials.yaml")
    # mock the user input
    mocker.patch("questionary.confirm", return_value=Question(True))

    init_task = InitTask(profiles_dir_path=profiles_dir_path, profiles_file_path=profiles_file_path)

    init_task.user_info = UserInfoInputModel(
        first_name="Bastien",
        last_name="Boutonnet",
        password="hunter123",
        username="bb",
        email="bb@gmail.com",
    )

    init_task.create_profiles_file()
    assert profiles_file_path.exists()


@pytest.mark.datafiles(TEST_DIR)
def test_persist_credentials(datafiles, mocker):
    from status_villain.tasks.tasks import UserInfoInputModel

    profiles_dir_path = datafiles  # noqa: F811
    profiles_file_path = Path(profiles_dir_path).joinpath("credentials.yaml")
    # mock the user input
    mocker.patch("questionary.confirm", return_value=Question(True))

    init_task = InitTask(profiles_dir_path=profiles_dir_path, profiles_file_path=profiles_file_path)

    init_task.user_info = UserInfoInputModel(
        first_name="Bastien",
        last_name="Boutonnet",
        password="hunter123",
        username="bb",
        email="bb@gmail.com",
    )
    init_task.persist_credentials()
    assert profiles_dir_path.exists()
    assert profiles_file_path.exists()


@pytest.mark.datafiles(TEST_DIR)
def test_persist_credentials_no_user_info(datafiles, mocker):

    profiles_dir_path = datafiles  # noqa: F811
    profiles_file_path = Path(profiles_dir_path).joinpath("credentials.yaml")
    # mock the user input
    mocker.patch("questionary.confirm", return_value=Question(True))

    init_task = InitTask(profiles_dir_path=profiles_dir_path, profiles_file_path=profiles_file_path)

    with pytest.raises(AttributeError, match="'InitTask' object has no attribute 'user_info'"):
        init_task.persist_credentials()


@pytest.mark.datafiles(TEST_DIR)
def test_run(datafiles, mocker, monkeypatch):
    profiles_dir_path = datafiles  # noqa: F811
    profiles_file_path = Path(profiles_dir_path).joinpath("credentials.yaml")
    # mock the user input
    mocker.patch("questionary.confirm", return_value=Question(True))
    mocker.patch(
        "questionary.prompt",
        return_value=dict(
            first_name="Bastien",
            last_name="Boutonnet",
            password="hunter123",
            username="bb",
            email="bb@gmail.com",
        ),
    )
    init_task = InitTask(profiles_dir_path=profiles_dir_path, profiles_file_path=profiles_file_path)

    def create_user_mock(*args, **kwargs):
        return None

    monkeypatch.setattr("status_villain.tasks.tasks.create_user", create_user_mock)

    init_task.run()
    assert profiles_dir_path.exists()
    assert profiles_file_path.exists()
