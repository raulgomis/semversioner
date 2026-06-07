from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class SemversionerError(Exception):
    """
    Base Exception
    """

    pass


class MissingChangesetError(SemversionerError):
    """
    Missing changeset files
    """

    pass


class ReleaseType(Enum):
    """
    Represents the type of release.
    """

    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"


@dataclass(frozen=True)
class Changeset:
    """
    Represents a change in the version.
    """

    type: str
    description: str
    attributes: dict[str, str] | None = None
    pre: str | None = None


@dataclass(frozen=True)
class Release:
    """
    Represents a release.
    """

    version: str
    changes: list[Changeset]
    created_at: datetime | None = None


@dataclass(frozen=True)
class ReleaseStatus:
    """
    Represents the status of the release in a particular point of time.
    """

    version: str
    next_version: str | None
    unreleased_changes: list[Changeset]
