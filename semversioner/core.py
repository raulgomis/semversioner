import os
import sys
from typing import List, Optional

import click
from jinja2 import Template
from semversioner.models import Changeset, Release, ReleaseStatus

from semversioner.storage import SemversionerFileSystemStorage
from semversioner.version import SemVersion

ROOTDIR = os.getcwd()
INITIAL_VERSION = '0.0.0'
DEFAULT_TEMPLATE = """# Changelog
Note: version releases in the 0.x.y range may introduce breaking changes.
{% for release in releases %}

## {{ release.version }}

{% for change in release.changes %}
- {{ change.type }}: {{ change.description }}
{% endfor %}
{% endfor %}
"""


class Semversioner:

    def __init__(self, path: str = ROOTDIR):
        self.fs = SemversionerFileSystemStorage(path=path)

    def is_deprecated(self) -> bool:
        return self.fs.is_deprecated()

    def add_change(self, change_type: str, description: str, pre: Optional[str] = None) -> str:
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

        return self.fs.create_changeset(change_type=change_type, description=description, pre=pre)

    def generate_changelog(self, version: Optional[str] = None, template: str = DEFAULT_TEMPLATE) -> str:
        """ 
        Generates the changelog.

        The method generates the changelog based on the template file defined 
        in ``DEFAULT_TEMPLATE``.

        Returns
        -------
        str
            Changelog string.
        """
        releases: List[Release] = self.fs.list_versions()

        if version is not None:
            releases = [x for x in releases if x.version == version]

        return Template(template, trim_blocks=True).render(releases=releases)

    def release(self) -> Release:
        """ 
        Performs the release.

        The method performs the release by taking everything in ``next-release`` folder 
        and aggregating all together in a single JSON file for that release (e.g ``1.12.0.json``). 
        The JSON file generated is a list of all the individual JSON files from ``next-release``.
        After aggregating the files, it removes the ``next-release`` directory.

        Returns
        -------
        previous_version : str
            Previous version.
        new_version : str
            New version.
        """
        changes: List[Changeset] = self.fs.list_changesets()

        current_version_number = self.get_last_version()
        next_version_number = self.get_next_version(changes, current_version_number)

        if next_version_number is None:
            click.secho("Error: No changes to release. Skipping release process.", fg='red')
            sys.exit(-1)

        click.echo("Releasing version: %s -> %s" % (current_version_number, next_version_number))
        self.fs.create_version(version=next_version_number, changes=changes)
        self.fs.remove_all_changesets()

        return Release(version=next_version_number, changes=changes)

    def get_last_version(self) -> str:
        """ 
        Gets the current version.

        """
        return self.fs.get_last_version() or INITIAL_VERSION

    def get_next_version(self, changes: List[Changeset], current_version_number: str) -> Optional[str]:
        if len(changes) == 0:
            return None

        release_type: str = sorted(list(map(lambda x: x.type, changes)))[0]  # type: ignore

        stable_releases = [x.pre for x in changes if x.pre is None]
        prereleases = [x.pre for x in changes if x.pre is not None]

        if len(stable_releases) > 0 and len(prereleases) > 0:
            click.secho("Error: Cannot have both stable and prerelease changes in the same release.", fg='red')
            sys.exit(-1)

        prerelease_type = None
        if len(prereleases) > 0:
            prerelease_type = sorted(list(prereleases), reverse=True)[0]

        return SemVersion(current_version_number).next_version(
            release_type=release_type, 
            prerelease_type=prerelease_type).to_string()

    def get_status(self) -> ReleaseStatus:
        """
        Displays the status of the working directory.
        """
        version = self.get_last_version()
        changes = self.fs.list_changesets()
        next_version = self.get_next_version(changes, version)

        return ReleaseStatus(version=version, next_version=next_version, unreleased_changes=changes)
