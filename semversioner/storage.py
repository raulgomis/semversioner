import dataclasses
import json
import logging
from abc import ABCMeta, abstractmethod
from datetime import datetime, timezone
from pathlib import Path

from packaging.version import parse

from semversioner.models import Changeset, Release

logger = logging.getLogger("semversioner")


class SemversionerStorage(metaclass=ABCMeta):
    """
    Abstract base class that defines the interface for a storage class in a semversioner system.
    The storage class is responsible for creating, listing, and managing changesets and versions.
    """

    @abstractmethod
    def is_deprecated(self) -> bool:
        """
        Determines if the storage is deprecated.
        """
        pass

    @abstractmethod
    def create_changeset(self, change: Changeset) -> str:
        """
        Creates a changeset in the storage.
        """
        pass

    @abstractmethod
    def remove_all_changesets(self) -> None:
        """
        Removes all changesets from the storage.
        """
        pass

    @abstractmethod
    def list_changesets(self) -> list[Changeset]:
        """
        Retrieves a list of all changesets in the storage.
        """
        pass

    @abstractmethod
    def create_version(self, release: Release) -> None:
        """
        Creates a new version in the storage.
        """
        pass

    @abstractmethod
    def list_versions(self) -> list[Release]:
        """
        Lists all versions in the storage.
        """
        pass

    @abstractmethod
    def get_last_version(self) -> str | None:
        """
        Retrieves the latest version from the storage. Returns None if no versions exist.
        """
        pass


class EnhancedJSONEncoder(json.JSONEncoder):
    """
    This class extends the built-in json.JSONEncoder class to provide a custom encoding for dataclasses.
    By default, the json.JSONEncoder class doesn't know how to encode dataclasses, so we define a custom encoding here.
    """

    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o, dict_factory=lambda x: {k: v for (k, v) in x if v is not None})
        return super().default(o)


class ReleaseJsonMapper:
    """
    Provides functionality to convert a Release object to JSON and vice versa.
    """

    @staticmethod
    def to_json(release: Release) -> str:
        """
        Converts a Release object to a JSON-formatted string.
        """
        data = {
            "version": release.version,
            "created_at": release.created_at.isoformat(timespec="seconds") if release.created_at else None,
            "changes": release.changes,
        }

        return json.dumps(data, cls=EnhancedJSONEncoder, indent=2, sort_keys=True)

    @staticmethod
    def from_json(data: dict, release_identifier: str) -> Release:
        """
        Creates a Release object from a JSON-formatted string.
        """
        created_at: datetime | None = None

        if "created_at" in data:  # New format
            created_at = datetime.fromisoformat(data["created_at"])
            version = data["version"]
            raw_changes = data["changes"]
        else:
            raw_changes = data
            version = release_identifier

        changes = [Changeset(**c) for c in raw_changes]
        changes = sorted(changes, key=lambda k: k.type + k.description)

        return Release(version=version, changes=changes, created_at=created_at)


class SemversionerFileSystemStorage(SemversionerStorage):
    def __init__(self, path: str):
        base_path = Path(path)
        semversioner_path_legacy = base_path / ".changes"
        semversioner_path_new = base_path / ".semversioner"
        semversioner_path = semversioner_path_new
        deprecated = False

        if semversioner_path_legacy.is_dir() and not semversioner_path_new.is_dir():
            deprecated = True
            semversioner_path = semversioner_path_legacy
        if not semversioner_path.is_dir():
            semversioner_path.mkdir(parents=True)

        next_release_path = semversioner_path / "next-release"
        if not next_release_path.is_dir():
            next_release_path.mkdir(parents=True)

        self.path = base_path
        self.semversioner_path = semversioner_path
        self.next_release_path = next_release_path
        self.deprecated = deprecated

    def is_deprecated(self) -> bool:
        return self.deprecated

    def create_changeset(self, change: Changeset) -> str:
        """
        Create a new changeset file.

        The method creates a new json file in the ``.semversioner/next-release/`` directory
        with the type and description provided.

        Parameters
        -------
        change (Changeset): Changeset.

        Returns
        -------
        path : str
            Absolute path of the file generated.
        """

        # Retry loop with atomic file creation to prevent race conditions
        while True:
            filename = f"{change.type}-{datetime.now(timezone.utc):%Y%m%d%H%M%S%f}.json"
            full_path = self.next_release_path / filename

            try:
                # Use 'x' mode for exclusive creation - fails if file already exists
                with full_path.open("x") as f:
                    f.write(json.dumps(change, cls=EnhancedJSONEncoder, indent=2) + "\n")
                return str(full_path)
            except FileExistsError:
                # File already exists, retry with a new timestamp
                continue

    def remove_all_changesets(self) -> None:
        logger.info(f"Removing changeset files in '{self.next_release_path}' directory.")

        # Remove all json files in next_release_path
        for file_path in self.next_release_path.iterdir():
            if file_path.suffix == ".json":
                file_path.unlink()
        # Remove next_release_path if the directory is empty
        if not any(self.next_release_path.iterdir()):
            logger.info(f"Removing '{self.next_release_path}' directory.")
            self.next_release_path.rmdir()

    def list_changesets(self) -> list[Changeset]:
        changes: list[Changeset] = []
        next_release_dir = self.next_release_path
        if not next_release_dir.is_dir():
            return changes
        for file_path in next_release_dir.iterdir():
            if file_path.suffix == ".json":
                with file_path.open() as f:
                    change_data = json.load(f)
                    changes.append(Changeset(**change_data))
        return sorted(changes, key=lambda k: k.type + k.description)

    def create_version(self, release: Release) -> None:
        version: str = release.version
        release_json_file = self.semversioner_path / f"{version}.json"
        with release_json_file.open("w") as f:
            f.write(ReleaseJsonMapper.to_json(release))
        logger.info(f"Generated '{release_json_file}' file.")

    def list_versions(self) -> list[Release]:
        releases: list[Release] = []
        for release_identifier in self._list_release_numbers():
            release_json_file = self.semversioner_path / f"{release_identifier}.json"
            with release_json_file.open() as f:
                data = json.load(f)
                releases.append(ReleaseJsonMapper.from_json(data, release_identifier))
        return releases

    def get_last_version(self) -> str | None:
        releases = self._list_release_numbers()
        if len(releases) > 0:
            return releases[0]
        return None

    def _list_release_numbers(self) -> list[str]:
        files = [f.name for f in self.semversioner_path.iterdir() if f.is_file()]
        return sorted((x[: -len(".json")] for x in files if x.endswith(".json")), key=lambda x: parse(x), reverse=True)
