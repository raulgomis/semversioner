import dataclasses
from datetime import datetime
import json
import os
from abc import ABCMeta, abstractmethod
from distutils.version import StrictVersion
from typing import List, Optional

import click

from semversioner.models import Changeset, Release


class SemversionerStorage(metaclass=ABCMeta):

    @abstractmethod
    def is_deprecated(self) -> bool:
        pass

    @abstractmethod
    def create_changeset(self, change: Changeset) -> str:
        pass

    @abstractmethod
    def remove_all_changesets(self) -> None:
        pass

    @abstractmethod
    def list_changesets(self) -> List[Changeset]:
        pass

    @abstractmethod
    def create_version(self, release: Release) -> None:
        pass

    @abstractmethod
    def list_versions(self) -> List[Release]:
        pass

    @abstractmethod
    def get_last_version(self) -> Optional[str]:
        pass


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):  # type: ignore
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


class ReleaseJsonMapper:
    """
    Release Json Mapper class
    """

    @staticmethod
    def to_json(release: Release) -> str:
        data = {
            'version': release.version,
            'created_at': release.created_at.isoformat() if release.created_at else None,
            'changes': release.changes
        }

        return json.dumps(data, cls=EnhancedJSONEncoder, indent=2, sort_keys=True)

    @staticmethod
    def from_json(data: dict, release_identifier: str) -> Release:
        created_at: Optional[datetime] = None

        if 'created_at' in data:  # New format
            created_at = datetime.fromisoformat(data['created_at'])
            version = data['version']
            changes = sorted(data['changes'], key=lambda k: k['type'] + k['description'])  # type: ignore
        else:
            changes = sorted(data, key=lambda k: k['type'] + k['description'])  # type: ignore
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

        filename = None
        while (filename is None or os.path.isfile(os.path.join(self.next_release_path, filename))):
            filename = '{type_name}-{datetime}.json'.format(
                type_name=change.type,
                datetime="{:%Y%m%d%H%M%S%f}".format(datetime.utcnow())
            )

        with open(os.path.join(self.next_release_path, filename), 'w') as f:
            f.write(json.dumps(change, cls=EnhancedJSONEncoder, indent=2) + "\n")

        return os.path.join(self.next_release_path, filename)

    def remove_all_changesets(self) -> None:
        click.echo("Removing '" + self.next_release_path + "' directory.")

        for filename in os.listdir(self.next_release_path):
            full_path = os.path.join(self.next_release_path, filename)
            os.remove(full_path)
        os.rmdir(self.next_release_path)

    def list_changesets(self) -> List[Changeset]:
        changes: List[Changeset] = []
        next_release_dir = self.next_release_path
        if not os.path.isdir(next_release_dir):
            return changes
        for filename in os.listdir(next_release_dir):
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
        """ 
        Gets the current version number. None if there is nothing released yet.

        """
        releases = self._list_release_numbers()
        if len(releases) > 0:
            return releases[0]
        return None

    def _list_release_numbers(self) -> List[str]:
        files = [f for f in os.listdir(self.semversioner_path) if os.path.isfile(os.path.join(self.semversioner_path, f))]
        releases = sorted(list(map(lambda x: x[:-len('.json')], files)), key=StrictVersion, reverse=True)
        return releases
