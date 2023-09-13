from enum import Enum
from pathlib import Path

import toml
from platformdirs import user_data_dir

from encord_consensus.app.common.constants import (
    CHOOSE_PROJECT_PAGE_NAME,
    EXPORT_PAGE_NAME,
    INSPECT_FILES_PAGE_NAME,
)


class Settings:
    API_URL: str = "http://localhost:8501"

    # ---------- INTERNAL URLS ----------
    CHOOSE_PROJECT_PAGE_URL: str = API_URL + "/" + CHOOSE_PROJECT_PAGE_NAME.replace(" ", "_")
    EXPORT_PAGE_URL: str = API_URL + "/" + EXPORT_PAGE_NAME.replace(" ", "_")
    HOME_PAGE_URL: str = API_URL + "/"
    INSPECT_FILES_PAGE_URL: str = API_URL + "/" + INSPECT_FILES_PAGE_NAME.replace(" ", "_")


class AppConfigProperties(Enum):
    """Enumeration for properties of the AppConfig class."""

    ENCORD_SSH_KEY_PATH = "encord_ssh_key_path"


class AppConfig:
    """
    Manage application configuration.
    """

    def __init__(self, app_name: str, app_author: str):
        """
        Initialize a new AppConfig instance.

        :param str app_name: The name of the application.
        :param str app_author: The name of the application's author.
        """
        self.app_name = app_name

        # Get the user data directory for the application where the configuration file is stored
        app_dir = Path(user_data_dir(appname=self.app_name, appauthor=app_author))
        if not app_dir.is_dir():
            app_dir.mkdir(parents=True)

        # Load the configuration file
        self.config_file = app_dir / "config.toml"
        self.load()

    @property
    def contents(self) -> dict:
        """
        Get all configuration properties and their values.

        :return: A dictionary containing AppConfig properties and their values.
        """
        c = {p.value: getattr(self, p.value) for p in AppConfigProperties if hasattr(self, p.value)}
        return c

    def save(self):
        """
        Save the configuration to the config file.
        """
        self.config_file.write_text(toml.dumps(self.contents), encoding="utf-8")

    def load(self):
        """
        Load the configuration from the config file.
        """
        # Create an empty config file if it doesn't exist
        if not self.config_file.is_file():
            self.config_file.touch()

        # Load the configuration from the TOML file and set the attributes
        for name, value in toml.load(self.config_file).items():
            setattr(self, name, value)

        # Fill the missing attributes from AppConfigProperties as `None`
        for p in AppConfigProperties:
            if not hasattr(self, p.value):
                setattr(self, p.value, None)


app_config = AppConfig("encord-consensus")
