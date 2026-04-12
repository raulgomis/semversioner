import unittest
import shutil
import os
import tempfile
import threading

from semversioner import Semversioner
from semversioner import ReleaseStatus
from semversioner.models import Changeset, MissingChangesetException


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

    def test_increase_version(self) -> None:
        releaser = Semversioner(self.directory_name)
        self.assertEqual(releaser._get_next_version_from_type("1.0.0", "minor"), "1.1.0")
        self.assertEqual(releaser._get_next_version_from_type("1.0.0", "major"), "2.0.0")
        self.assertEqual(releaser._get_next_version_from_type("1.0.0", "patch"), "1.0.1")
        self.assertEqual(releaser._get_next_version_from_type("0.1.1", "minor"), "0.2.0")
        self.assertEqual(releaser._get_next_version_from_type("0.1.1", "major"), "1.0.0")
        self.assertEqual(releaser._get_next_version_from_type("0.1.1", "patch"), "0.1.2")
        self.assertEqual(releaser._get_next_version_from_type("9.9.9", "minor"), "9.10.0")
        self.assertEqual(releaser._get_next_version_from_type("9.9.9", "major"), "10.0.0")
        self.assertEqual(releaser._get_next_version_from_type("9.9.9", "patch"), "9.9.10")

    def test_commands_with_no_changesets(self) -> None:
        releaser = Semversioner(path=self.directory_name)
        self.assertEqual(releaser.generate_changelog(), "# Changelog\nNote: version releases in the 0.x.y range may introduce breaking changes.\n")
        self.assertEqual(releaser.get_last_version(), "0.0.0")
        self.assertEqual(releaser.get_status(), ReleaseStatus(version='0.0.0', next_version=None, unreleased_changes=[]))
        with self.assertRaises(MissingChangesetException):
            releaser.release()

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
        with self.assertRaises(MissingChangesetException):
            releaser.release()

    def test_release_with_attributes(self) -> None:

        releaser = Semversioner(path=self.directory_name)

        releaser.add_change("minor", "My description", attributes={"key": "value"})
        releaser.add_change("major", "My description", attributes={"key2": "value2", "key3": "value3"})
        self.assertEqual(releaser.get_status(), ReleaseStatus(version='0.0.0', next_version='1.0.0', unreleased_changes=[
            Changeset(type='major', description='My description', attributes={"key2": "value2", "key3": "value3"}),
            Changeset(type='minor', description='My description', attributes={"key": "value"})]
        ))
        releaser.release()
        self.assertEqual(releaser.get_status(), ReleaseStatus(version='1.0.0', next_version=None, unreleased_changes=[]))
        with self.assertRaises(MissingChangesetException):
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

    def test_concurrent_changeset_creation_race_condition(self) -> None:
        """
        Test that concurrent changeset creation does not result in file creation race conditions.
        """
        releaser = Semversioner(self.directory_name)
        num_threads = 20
        threads = []
        descriptions = [f"desc {i}" for i in range(num_threads)]

        def add_change(desc: str) -> None:
            # Each thread tries to add a changeset with a unique description
            releaser.add_change("patch", desc)

        for desc in descriptions:
            t = threading.Thread(target=add_change, args=(desc,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Check that all changeset files were created and are unique
        files = [f for f in os.listdir(self.next_release_dirname) if f.endswith('.json')]
        self.assertEqual(len(files), num_threads)
        # Optionally, check that all descriptions are present
        found_descriptions = set()
        for f in files:
            with open(os.path.join(self.next_release_dirname, f)) as fh:
                data = fh.read()
                for desc in descriptions:
                    if desc in data:
                        found_descriptions.add(desc)
        self.assertEqual(set(descriptions), found_descriptions)

    def test_is_deprecated(self) -> None:
        releaser = Semversioner(self.directory_name)
        self.assertFalse(releaser.is_deprecated())

    def test_has_changesets_nok(self) -> None:
        releaser = Semversioner(path=self.directory_name)
        self.assertFalse(releaser.has_changesets())

    def test_has_changesets_ok(self) -> None:

        releaser = Semversioner(path=self.directory_name)

        self.assertFalse(releaser.has_changesets())
        releaser.add_change("major", "My description")
        self.assertTrue(releaser.has_changesets())

    def test_has_changesets_after_release(self) -> None:

        releaser = Semversioner(path=self.directory_name)
        releaser.add_change("major", "My description")
        releaser.release()
        self.assertFalse(releaser.has_changesets())


if __name__ == '__main__':
    unittest.main()
