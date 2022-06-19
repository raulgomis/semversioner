from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class ReleaseType(Enum):
    """
    Represents the type of release.
    """
    MAJOR = 'major'
    MINOR = 'minor'
    PATCH = 'patch'


class PreReleaseType(Enum):
    """
    Represents the type of prerelease.
    """
    ALPHA = 'alpha'
    BETA = 'beta'
    RC = 'rc'


@dataclass(frozen=True)
class Changeset:
    """
    Represents a change in the version.
    """
    type: str
    description: str
    pre: Optional[str] = None


@dataclass(frozen=True)
class Release:
    """
    Represents a release.
    """
    version: str
    changes: List[Changeset]


@dataclass(frozen=True)
class ReleaseStatus:
    """
    Represents the status of the release in a particular point of time.
    """
    version: str
    next_version: Optional[str]
    unreleased_changes: List[Changeset]
