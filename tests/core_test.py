import unittest
import shutil
import os
import tempfile

from semversioner import Semversioner
from semversioner import ReleaseStatus
from semversioner.models import Changeset


class CoreTestCase(unittest.TestCase):

    directory_name: str
    changes_dirname: str
    next_release_dirname: str

    def setUp(self) -> None:
        self.directory_name = tempfile.mkdtemp()
        self.changes_dirname = os.path.join(self.directory_name, '.semversioner')
        self.next_release_dirname = os.path.join(self.changes_dirname, 'next-release')
        print("Created directory: " + self.directory_name)

    def tearDown(self) -> None:
        print("Removing directory: " + self.directory_name)
        shutil.rmtree(self.directory_name)

    def test_commands_with_no_changesets(self) -> None:
        releaser = Semversioner(path=self.directory_name)
        self.assertEqual(releaser.generate_changelog(), "# Changelog\nNote: version releases in the 0.x.y range may introduce breaking changes.\n")
        self.assertEqual(releaser.get_last_version(), "0.0.0")
        self.assertEqual(releaser.get_status(), ReleaseStatus(version='0.0.0', next_version=None, unreleased_changes=[]))
        with self.assertRaises(SystemExit):
            releaser.release()

    def test_get_next_version_stable(self) -> None:
        releaser = Semversioner(self.directory_name)

        params_list = [
            (
                [
                    Changeset(type="minor", description="My description"),
                ], 
                "1.0.0", "1.1.0"
            ),
            (
                [
                    Changeset(type="major", description="My description"),
                ], 
                "1.0.0", "2.0.0"
            ),
            (
                [
                    Changeset(type="patch", description="My description"),
                ], 
                "1.0.0", "1.0.1"
            ),
            (
                [
                    Changeset(type="minor", description="My description"),
                    Changeset(type="minor", description="My description"),
                    Changeset(type="minor", description="My description"),
                ], 
                "1.0.0", "1.1.0"
            ),
            (
                [
                    Changeset(type="major", description="My description"),
                    Changeset(type="minor", description="My description"),
                    Changeset(type="minor", description="My description"),
                ], 
                "1.0.0", "2.0.0"
            ),
            (
                [
                    Changeset(type="patch", description="My description"),
                    Changeset(type="minor", description="My description"),
                    Changeset(type="minor", description="My description"),
                ], 
                "1.0.0", "1.1.0"
            ),
        ]

        for p1, p2, p3 in params_list:
            with self.subTest():
                self.assertEqual(releaser.get_next_version(p1, p2), p3)

    def test_get_next_version_prerelease(self) -> None:
        releaser = Semversioner(self.directory_name)

        params_list = [
            (
                [
                    Changeset(type="patch", description="My description", pre="alpha"),
                    Changeset(type="patch", description="My description", pre="alpha"),
                ], 
                "1.0.0", "1.0.1a1"
            ),
            (
                [
                    Changeset(type="patch", description="My description", pre="alpha"),
                    Changeset(type="patch", description="My description", pre="beta"),
                ], 
                "1.0.0", "1.0.1b1"
            ),
            (
                [
                    Changeset(type="patch", description="My description", pre="beta"),
                    Changeset(type="patch", description="My description", pre="beta"),
                ], 
                "1.0.1a1", "1.0.1b1"
            ),
        ]

        for p1, p2, p3 in params_list:
            with self.subTest():
                self.assertEqual(releaser.get_next_version(p1, p2), p3)

    def test_release(self) -> None:

        releaser = Semversioner(path=self.directory_name)

        releaser.add_change("minor", "My description")
        releaser.add_change("major", "My description")
        self.assertEqual(releaser.get_status(), ReleaseStatus(version='0.0.0', next_version='1.0.0', unreleased_changes=[
            Changeset(type='major', description='My description'),
            Changeset(type='minor', description='My description')]
        ))
        releaser.release()
        self.assertEqual(releaser.get_status(), ReleaseStatus(version='1.0.0', next_version=None, unreleased_changes=[]))
        with self.assertRaises(SystemExit):
            releaser.release()

    def test_release_stress(self) -> None:

        releaser = Semversioner(path=self.directory_name)

        expected = []
        for i in range(100):
            releaser.add_change("major", f"My description {i}")
            expected.append(Changeset(type='major', description=f"My description {i}"))

        expected = sorted(expected, key=lambda k: k.type + k.description)
        self.assertEqual(releaser.get_status(), ReleaseStatus(version='0.0.0', next_version='1.0.0', unreleased_changes=expected))
        releaser.release()
        self.assertEqual(releaser.get_status(), ReleaseStatus(version='1.0.0', next_version=None, unreleased_changes=[]))

    def test_is_deprecated(self) -> None:
        releaser = Semversioner(self.directory_name)
        self.assertFalse(releaser.is_deprecated())


if __name__ == '__main__':
    unittest.main()
