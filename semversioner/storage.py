import dataclasses
from datetime import datetime, timezone
import json
import os
from abc import ABCMeta, abstractmethod
from packaging.version import parse
from typing import List, Optional

import click

from semversioner.models import Changeset, Release


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
    def list_changesets(self) -> List[Changeset]:
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
    def list_versions(self) -> List[Release]:
        """
        Lists all versions in the storage.
        """
        pass

    @abstractmethod
    def get_last_version(self) -> Optional[str]:
        """
        Retrieves the latest version from the storage. Returns None if no versions exist.
        """
        pass


class EnhancedJSONEncoder(json.JSONEncoder):
    """
    This class extends the built-in json.JSONEncoder class to provide a custom encoding for dataclasses.
    By default, the json.JSONEncoder class doesn't know how to encode dataclasses, so we define a custom encoding here.
    """
    def default(self, o):  # type: ignore
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
            'version': release.version,
            'created_at': release.created_at.isoformat(timespec="seconds") if release.created_at else None,
            'changes': release.changes
        }

        return json.dumps(data, cls=EnhancedJSONEncoder, indent=2, sort_keys=True)

    @staticmethod
    def from_json(data: dict, release_identifier: str) -> Release:
        """
        Creates a Release object from a JSON-formatted string.
        """
        created_at: Optional[datetime] = None

        if 'created_at' in data:  # New format
            created_at = datetime.fromisoformat(data['created_at'])
            version = data['version']
            changes = sorted(data['changes'], key=lambda k: k['type'] + k['description'])
        else:
            changes = sorted(data, key=lambda k: k['type'] + k['description'])
            version = release_identifier

        return Release(version=version, changes=changes, created_at=created_at)


class SemversionerFileSystemStorage(SemversionerStorage):

    def __init__(self, path: str):
        semversioner_path_legacy: str = os.path.join(path, '.changes')
        semversioner_path_new: str = os.path.join(path, '.semversioner')
        semversioner_path: str = semversioner_path_new
        deprecated: bool = False

        if os.path.isdir(semversioner_path_legacy) and not os.path.isdir(semversioner_path_new):
            deprecated = True
            semversioner_path = semversioner_path_legacy
        if not os.path.isdir(semversioner_path):
            os.makedirs(semversioner_path)

        next_release_path = os.path.join(semversioner_path, 'next-release')
        if not os.path.isdir(next_release_path):
            os.makedirs(next_release_path)

        self.path: str = path
        self.semversioner_path: str = semversioner_path
        self.next_release_path: str = next_release_path
        self.deprecated: bool = deprecated

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
            filename = '{type_name}-{datetime}.json'.format(
                type_name=change.type,
                datetime="{:%Y%m%d%H%M%S%f}".format(datetime.now(timezone.utc))
            )
            full_path = os.path.join(self.next_release_path, filename)
            
            try:
                # Use 'x' mode for exclusive creation - fails if file already exists
                with open(full_path, 'x') as f:
                    f.write(json.dumps(change, cls=EnhancedJSONEncoder, indent=2) + "\n")
                return full_path
            except FileExistsError:
                # File already exists, retry with a new timestamp
                continue

    def remove_all_changesets(self) -> None:
        click.echo("Removing changeset files in '" + self.next_release_path + "' directory.")

        # Remove all json files in next_release_path
        for filename in os.listdir(self.next_release_path):
            if filename.endswith('.json'):
                full_path = os.path.join(self.next_release_path, filename)
                os.remove(full_path)
        # Remove next_release_path if the directory is empty
        if not os.listdir(self.next_release_path):
            click.echo("Removing '" + self.next_release_path + "' directory.")
            os.rmdir(self.next_release_path)

    def list_changesets(self) -> List[Changeset]:
        changes: List[Changeset] = []
        next_release_dir = self.next_release_path
        if not os.path.isdir(next_release_dir):
            return changes
        for filename in os.listdir(next_release_dir):
            if filename.endswith('.json'):
                full_path = os.path.join(next_release_dir, filename)
                with open(full_path) as f:
                    dict = json.load(f)
                    changes.append(Changeset(**dict))
        changes = sorted(changes, key=lambda k: k.type + k.description)
        return changes

    def create_version(self, release: Release) -> None:
        version: str = release.version
        release_json_filename: str = os.path.join(self.semversioner_path, '%s.json' % version)
        with open(release_json_filename, 'w') as f:
            f.write(ReleaseJsonMapper.to_json(release))
        click.echo("Generated '" + release_json_filename + "' file.")

    def list_versions(self) -> List[Release]:
        releases: List[Release] = []
        for release_identifier in self._list_release_numbers():
            with open(os.path.join(self.semversioner_path, release_identifier + '.json')) as f:
                data = json.load(f)
                releases.append(ReleaseJsonMapper.from_json(data, release_identifier))
        return releases

    def get_last_version(self) -> Optional[str]:
        releases = self._list_release_numbers()
        if len(releases) > 0:
            return releases[0]
        return None

    def _list_release_numbers(self) -> List[str]:
        files = [f for f in os.listdir(self.semversioner_path) if os.path.isfile(os.path.join(self.semversioner_path, f))]
        releases = sorted(list(map(lambda x: x[:-len('.json')], files)), key=lambda x: parse(x), reverse=True)
        return releases