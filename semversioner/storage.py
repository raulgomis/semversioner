import datetime
import json
import os
from abc import ABCMeta, abstractmethod
from distutils.version import StrictVersion
from typing import Any, Dict, List, Optional

import click


class SemversionerStorage(metaclass=ABCMeta):

    @abstractmethod
    def is_deprecated(self) -> bool:
        pass

    @abstractmethod
    def create_changeset(self, change_type: str, description: str) -> Dict[str, str]:
        pass

    @abstractmethod
    def remove_all_changesets(self) -> None:
        pass

    @abstractmethod
    def list_changesets(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def create_version(self, version: str, changes: List[Dict[str, Any]]) -> None:
        pass

    @abstractmethod
    def list_versions(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_last_version(self) -> Optional[str]:
        pass


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

    def create_changeset(self, change_type: str, description: str) -> Dict[str, Any]:
        """ 
        Create a new changeset file.

        The method creates a new json file in the ``.semversioner/next-release/`` directory 
        with the type and description provided.

        Parameters
        -------
        change_type (str): Change type. Allowed values: major, minor, patch.
        description (str): Change description.

        Returns
        -------
        path : str
            Absolute path of the file generated.
        """

        parsed_values = {
            'type': change_type,
            'description': description,
        }

        filename = None
        while (filename is None or os.path.isfile(os.path.join(self.next_release_path, filename))):
            filename = '{type_name}-{datetime}.json'.format(
                type_name=parsed_values['type'],
                datetime="{:%Y%m%d%H%M%S%f}".format(datetime.datetime.utcnow()))

        with open(os.path.join(self.next_release_path, filename), 'w') as f:
            f.write(json.dumps(parsed_values, indent=2) + "\n")

        return { 
            'path': os.path.join(self.next_release_path, filename)
        }

    def remove_all_changesets(self) -> None:
        click.echo("Removing '" + self.next_release_path + "' directory.")

        for filename in os.listdir(self.next_release_path):
            full_path = os.path.join(self.next_release_path, filename)
            os.remove(full_path)
        os.rmdir(self.next_release_path)

    def list_changesets(self) -> List[Dict[str, Any]]:
        changes: List[Dict[str, Any]] = []
        next_release_dir = self.next_release_path
        if not os.path.isdir(next_release_dir):
            return changes
        for filename in os.listdir(next_release_dir):
            full_path = os.path.join(next_release_dir, filename)
            with open(full_path) as f:
                changes.append(json.load(f))
        changes = sorted(changes, key=lambda k: k['type'] + k['description'])  # type: ignore
        return changes

    def create_version(self, version: str, changes: List[Dict[str, Any]]) -> None:
        release_json_filename: str = os.path.join(self.semversioner_path, '%s.json' % version)
        with open(release_json_filename, 'w') as f:
            f.write(json.dumps(changes, indent=2, sort_keys=True))
        click.echo("Generated '" + release_json_filename + "' file.")

    def list_versions(self) -> List[Dict[str, Any]]:
        releases: List[Dict[str, Any]] = []
        for release_identifier in self._list_release_numbers():
            with open(os.path.join(self.semversioner_path, release_identifier + '.json')) as f:
                data = json.load(f)
            data = sorted(data, key=lambda k: k['type'] + k['description'])  # type: ignore
            releases.append({'version': release_identifier, 'changes': data})
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
