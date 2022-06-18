import os
import sys
from typing import List, Optional

import click
from jinja2 import Template
from semversioner.models import Changeset, Release, ReleaseStatus, ReleaseType
from packaging.version import Version

from semversioner.storage import SemversionerFileSystemStorage

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

        return self.fs.create_changeset(change_type=change_type, description=description)

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

        # is_pre_release = False
        # if any(change.pre is not None for change in changes):
        #     is_pre_release = True

        release_type: str = sorted(list(map(lambda x: x.type, changes)))[0]  # type: ignore
        next_version: str = self._get_next_version_from_type(current_version_number, release_type)
        return next_version

    def get_status(self) -> ReleaseStatus:
        """
        Displays the status of the working directory.
        """
        version = self.get_last_version()
        changes = self.fs.list_changesets()
        next_version = self.get_next_version(changes, version)

        return ReleaseStatus(version=version, next_version=next_version, unreleased_changes=changes)

    def _get_next_version_from_type(self, current_version: str, release_type: str, prerelease_type: str = None) -> str:
        """ 
        Returns a string like '1.0.0'.

        '1.0.0' + 'major' = '2.0.0'
        '1.0.0' + 'minor' = '1.1.0'
        '1.0.0' + 'patch' = '1.0.1'
        '1.0.0' + 'major' + 'alpha' = '2.0.0-alpha.1'
        '1.0.0' + 'minor' + 'alpha' = '1.1.0-alpha.1'
        '2.0.0-alpha.1' + 'major' + 'alpha' = '2.0.0-alpha.2'
        '2.0.0-alpha.1' + 'major' = '2.0.0'
        '2.0.0-alpha.1' + 'minor' = '2.0.0'
        '2.0.0-alpha.1' + 'patch' = '2.0.0'
        """

        ver = Version(current_version)
        version_parts = [ver.major, ver.minor, ver.micro]

        if ver.is_prerelease:
            next_major = next_minor = False
            if ver.micro == 0 and ver.minor == 0:
                next_major = True
            elif ver.micro == 0 and ver.minor != 0:
                next_minor = True

            if prerelease_type is None:
                if next_major:
                    version_parts = [ver.major, ver.minor, ver.micro] 
                elif next_minor:
                    if release_type == ReleaseType.PATCH.value or release_type == ReleaseType.MINOR.value:
                        version_parts = [ver.major, ver.minor, ver.micro] 
                    elif release_type == ReleaseType.MAJOR.value:
                        version_parts = [ver.major + 1, 0, 0]
                else:
                    if release_type == ReleaseType.PATCH.value:
                        version_parts = [ver.major, ver.minor, ver.micro] 
                    elif release_type == ReleaseType.MINOR.value:
                        version_parts = [ver.major, ver.minor + 1, 0]
                    elif release_type == ReleaseType.MAJOR.value:
                        version_parts = [ver.major + 1, 0, 0]
            else:
                print("Hello")

        # Convert to a list of ints: [1, 0, 0].
        else:
            if release_type == ReleaseType.PATCH.value:
                version_parts = [ver.major, ver.minor, ver.micro + 1]
            elif release_type == ReleaseType.MINOR.value:
                version_parts = [ver.major, ver.minor + 1, 0]
            elif release_type == ReleaseType.MAJOR.value:
                version_parts = [ver.major + 1, 0, 0]

        return '.'.join(str(i) for i in version_parts)
