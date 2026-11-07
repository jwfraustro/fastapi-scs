"""This module contains the settings for the application."""

import os
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """The settings for the application."""

    # DB Settings
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "")
    ROOT_PATH: str = os.getenv("ROOT_PATH", "")

    # Largest search radius (decimal degrees) accepted; corresponds to maxSR in the registry capability.
    MAX_SR: float = 10.0

    # DALI MAXREC handling: the limit applied when the client does not send MAXREC,
    # and the hard ceiling applied to whatever the client asks for.
    DEFAULT_MAXREC: int = 1000
    MAX_MAXREC: int = 10000

    # DALI-1.2 makes parameter names case-sensitive. Set this to True to accept any case
    # (the SCS 1.0 / pre-DALI-1.2 behaviour) for old clients.
    CASE_INSENSITIVE_PARAMS: bool = False

    # SCS 1.1 says unknown parameters "can" be ignored (with an INFO name="warning" in the response),
    # while DALI-1.2 says services "must" reject them. False follows SCS 1.1, True follows DALI-1.2.
    REJECT_UNKNOWN_PARAMS: bool = False

    class Config:
        """The configuration for the settings."""

        env_file = ".env"


@lru_cache
def get_settings():
    """This function returns the settings obj for the application."""
    return Settings()
