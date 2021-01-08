import unittest
import shutil
import os
import tempfile

from semversioner.core import Semversioner


class CoreTestCase(unittest.TestCase):

    directory_name = None
    changes_dirname = None
    next_release_dirname = None

    def setUp(self):
        self.directory_name = tempfile.mkdtemp()
        self.changes_dirname = os.path.join(self.directory_name, '.semversioner')
        self.next_release_dirname = os.path.join(self.changes_dirname, 'next-release')
        print("Created directory: " + self.directory_name)

    def tearDown(self):
        print("Removing directory: " + self.directory_name)
        shutil.rmtree(self.directory_name)

    def test_increase_version(self):
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

    def test_commands_with_no_changesets(self):
        releaser = Semversioner(self.directory_name)
        self.assertEqual(releaser.generate_changelog(), "# Changelog\nNote: version releases in the 0.x.y range may introduce breaking changes.\n")
        self.assertEqual(releaser.get_version(), "0.0.0")
        self.assertEqual(releaser.get_status(), {
            'version': '0.0.0',
            'next_version': None,
            'unreleased_changes': [],
        })
        with self.assertRaises(SystemExit):
            releaser.release()

    def test_is_deprecated(self):
        releaser = Semversioner(self.directory_name)
        self.assertFalse(releaser.is_deprecated())


if __name__ == '__main__':
    unittest.main()
