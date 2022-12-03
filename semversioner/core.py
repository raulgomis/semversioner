import os
from datetime import datetime, timezone
from typing import List, Optional

import click
from jinja2 import Template

from semversioner.models import (Changeset, MissingChangesetException, SemversionerException, Release,
                                 ReleaseStatus, ReleaseType)
from semversioner.storage import SemversionerFileSystemStorage

ROOTDIR = os.getcwd()
INITIAL_VERSION = '0.0.0'
# To add support for dates you can use: {{ ' (' + release.created_at.strftime("%m-%d-%Y") + ')' if release.created_at }}
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

    def add_change(self, change_type: str, description: str) -> str:
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

        return self.fs.create_changeset(Changeset(type=change_type, description=description))

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

        Raises
        -------
        MissingChangesetException: SemversionerException
        """

        if not self.check():
            raise MissingChangesetException()

        current_version_number = self.get_last_version()
        next_version_number = self.get_next_version()
        changes: List[Changeset] = self.fs.list_changesets()

        if next_version_number is None:
            raise SemversionerException("Can't calculate next version number.")

        click.echo("Releasing version: %s -> %s" % (current_version_number, next_version_number))

        release = Release(version=next_version_number, changes=changes, created_at=datetime.now(timezone.utc))

        self.fs.create_version(release)
        self.fs.remove_all_changesets()

        return release

    def get_last_version(self) -> str:
        """ 
        Gets the current version. Returns '0.0.0' if there are not versions created.

        """
        return self.fs.get_last_version() or INITIAL_VERSION

    def get_next_version(self) -> Optional[str]:
        """
        Gets the next version. Returns None is there are not changeset files created.
        """
        changes = self.fs.list_changesets()
        current_version_number = self.get_last_version()

        if len(changes) == 0:
            return None

        release_type: str = sorted(list(map(lambda x: x.type, changes)))[0]
        next_version: str = self._get_next_version_from_type(current_version_number, release_type)
        return next_version

    def get_status(self) -> ReleaseStatus:
        """
        Displays the status of the working directory.
        """
        version = self.get_last_version()
        changes = self.fs.list_changesets()
        next_version = self.get_next_version()

        return ReleaseStatus(version=version, next_version=next_version, unreleased_changes=changes)

    def check(self) -> bool:
        """
        Check if changeset files are present.
        This is useful to enforce that changeset files are present before merging PRs to the target branch.
        """
        changes: List[Changeset] = self.fs.list_changesets()
        return len(changes) > 0

    def _get_next_version_from_type(self, current_version: str, release_type: str) -> str:
        """ 
        Returns a string like '1.0.0'.
        """
        # Convert to a list of ints: [1, 0, 0].
        version_parts = list(int(i) for i in current_version.split('.'))
        if release_type == ReleaseType.PATCH.value:
            version_parts[2] += 1
        elif release_type == ReleaseType.MINOR.value:
            version_parts[1] += 1
            version_parts[2] = 0
        elif release_type == ReleaseType.MAJOR.value:
            version_parts[0] += 1
            version_parts[1] = 0
            version_parts[2] = 0
        return '.'.join(str(i) for i in version_parts)
