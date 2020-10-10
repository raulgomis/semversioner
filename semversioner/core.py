import os
import sys
import json
import click
import datetime
from distutils.version import StrictVersion
from jinja2 import Template

ROOTDIR = os.getcwd()
INITIAL_VERSION = '0.0.0'
DEFAULT_TEMPLATE = """# Changelog
Note: version releases in the 0.x.y range may introduce breaking changes.
{% for release in releases %}

## {{ release.id }}

{% for data in release.data %}
- {{ data.type }}: {{ data.description }}
{% endfor %}
{% endfor %}
"""


class Semversioner:

    def __init__(self, path=ROOTDIR):
        semversioner_path_legacy = os.path.join(path, '.changes')
        semversioner_path_new = os.path.join(path, '.semversioner')
        semversioner_path = semversioner_path_new
        deprecated = False

        if os.path.isdir(semversioner_path_legacy) and not os.path.isdir(semversioner_path_new):
            deprecated = True
            semversioner_path = semversioner_path_legacy
        if not os.path.isdir(semversioner_path):
            os.makedirs(semversioner_path)

        next_release_path = os.path.join(semversioner_path, 'next-release')
        if not os.path.isdir(next_release_path):
            os.makedirs(next_release_path)

        self.path = path
        self.semversioner_path = semversioner_path
        self.next_release_path = next_release_path
        self.deprecated = deprecated

    def is_deprecated(self):
        return self.deprecated

    def add_change(self, change_type, description):
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
                datetime="{:%Y%m%d%H%M%S}".format(datetime.datetime.utcnow()))

        with open(os.path.join(self.next_release_path, filename), 'w') as f:
            f.write(json.dumps(parsed_values, indent=2) + "\n")

        return { 
            'path': os.path.join(self.next_release_path, filename)
        }

    def generate_changelog(self):
        """ 
        Generates the changelog.

        The method generates the changelog based on the template file defined 
        in ``DEFAULT_TEMPLATE``.

        Returns
        -------
        str
            Changelog string.
        """
        releases = []
        for release_identifier in self._sorted_releases():
            with open(os.path.join(self.semversioner_path, release_identifier + '.json')) as f:
                data = json.load(f)
            data = sorted(data, key=lambda k: k['type'] + k['description'])
            releases.append({'id': release_identifier, 'data': data})
        return Template(DEFAULT_TEMPLATE, trim_blocks=True).render(releases=releases)

    def release(self):
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
        changes = []
        next_release_dir = self.next_release_path
        for filename in os.listdir(next_release_dir):
            full_path = os.path.join(next_release_dir, filename)
            with open(full_path) as f:
                changes.append(json.load(f))

        if len(changes) == 0:
            click.secho("Error: No changes to release. Skipping release process.", fg='red')
            sys.exit(-1)

        current_version_number = self.get_version()
        next_version_number = self._get_next_version_number(changes, current_version_number)
        click.echo("Releasing version: %s -> %s" % (current_version_number, next_version_number))

        release_json_filename = os.path.join(self.semversioner_path, '%s.json' % next_version_number)

        click.echo("Generated '" + release_json_filename + "' file.")
        with open(release_json_filename, 'w') as f:
            f.write(json.dumps(changes, indent=2, sort_keys=True))

        click.echo("Removing '" + next_release_dir + "' directory.")
        for filename in os.listdir(next_release_dir):
            full_path = os.path.join(next_release_dir, filename)
            os.remove(full_path)
        os.rmdir(next_release_dir)

        return {
            'previous_version': current_version_number,
            'new_version': next_version_number
        }

    def get_version(self):
        """ 
        Gets the current version.

        """
        releases = self._sorted_releases()
        if len(releases) > 0:
            return releases[0]
        return INITIAL_VERSION

    def _sorted_releases(self):
        files = [f for f in os.listdir(self.semversioner_path) if os.path.isfile(os.path.join(self.semversioner_path, f))]
        releases = list(map(lambda x: x[:-len('.json')], files))
        releases = sorted(releases, key=StrictVersion, reverse=True)
        return releases

    def _get_next_version_number(self, changes, current_version_number):
        release_type = sorted(list(map(lambda x: x['type'], changes)))[0]
        return self._increase_version(current_version_number, release_type)

    def _increase_version(self, current_version, release_type):
        """ 
        Returns a string like '1.0.0'.
        """
        # Convert to a list of ints: [1, 0, 0].
        version_parts = list(int(i) for i in current_version.split('.'))
        if release_type == 'patch':
            version_parts[2] += 1
        elif release_type == 'minor':
            version_parts[1] += 1
            version_parts[2] = 0
        elif release_type == 'major':
            version_parts[0] += 1
            version_parts[1] = 0
            version_parts[2] = 0
        return '.'.join(str(i) for i in version_parts)
