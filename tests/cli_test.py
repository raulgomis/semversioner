import unittest
import shutil
import os
import tempfile
import json
from click.testing import CliRunner
from semversioner.cli import cli
from semversioner import __version__
from tests import fixtures


def command_processor(commands, path):
    runner = CliRunner()
    result = None
    for command in commands:
        command_id = command["id"]
        if command_id == "add-change":
            result = runner.invoke(cli, ["--path", path, "add-change", "--type", command["type"], "--description", command["description"]])
            assert not result.exception
            assert result.exit_code == 0
        elif command_id == "release":
            result = runner.invoke(cli, ["--path", path, "release"])
            assert not result.exception
            assert result.exit_code == 0
        elif command_id == "changelog":
            result = runner.invoke(cli, ["--path", path, "changelog"])
            assert not result.exception
            assert result.exit_code == 0
        elif command_id == "current-version":
            result = runner.invoke(cli, ['--path', path, "current-version"])
            assert not result.exception
            assert result.exit_code == 0
        else:
            print("Unknown command.")
    return result


class NewDataTestCase(unittest.TestCase):
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

    def test_write_new_change(self):
        commands = [
            {"id": "add-change", "type": "major", "description": "This is my major description"},
            {"id": "add-change", "type": "minor", "description": "This is my minor description"},
            {"id": "add-change", "type": "patch", "description": "This is my patch description"}
        ]

        result = command_processor(commands, self.directory_name)

        data = []
        files = sorted([i for i in os.listdir(self.next_release_dirname)])

        for filename in files:
            with open(os.path.join(self.next_release_dirname, filename)) as f:
                data.append(json.load(f))

        expected = [
            json.loads('{"type": "major","description": "This is my major description"}'),
            json.loads('{"type": "minor","description": "This is my minor description"}'),
            json.loads('{"type": "patch","description": "This is my patch description"}')
        ]

        self.assertListEqual(expected, data)
        self.assertRegex(result.output, f"Successfully created file {self.next_release_dirname}.*\\.json")

    def test_generate_changelog_empty(self):
        commands = [
            {"id": "add-change", "type": "major", "description": "This is my major description"},
            {"id": "add-change", "type": "minor", "description": "This is my minor description"},
            {"id": "changelog"}
        ]

        result = command_processor(commands, self.directory_name)
        self.assertEqual(result.output, "# Changelog\nNote: version releases in the 0.x.y range may introduce breaking changes.\n")

    def test_generate_changelog_single_major(self):
        commands = [
            {"id": "add-change", "type": "major", "description": "This is my major description"},
            {"id": "release"},
            {"id": "changelog"}
        ]

        result = command_processor(commands, self.directory_name)
        self.assertEqual(result.output, fixtures.CHANGELOG_1)

    def test_generate_changelog_single_patch(self):
        commands = [
            {"id": "add-change", "type": "patch", "description": "This is my patch description"},
            {"id": "release"},
            {"id": "changelog"}
        ]

        result = command_processor(commands, self.directory_name)
        self.assertEqual(result.output, fixtures.CHANGELOG_2)

    def test_generate_changelog_multiple(self):
        commands = [
            {"id": "add-change", "type": "patch", "description": "This is my patch description"},
            {"id": "release"},
            {"id": "add-change", "type": "major", "description": "This is my major description"},
            {"id": "release"},
            {"id": "add-change", "type": "major", "description": "This is my major description"},
            {"id": "release"},
            {"id": "add-change", "type": "minor", "description": "This is my minor description"},
            {"id": "release"},
            {"id": "changelog"}
        ]

        result = command_processor(commands, self.directory_name)
        self.assertEqual(result.output, fixtures.CHANGELOG_3)

    def test_generate_changelog_multiple_new(self):  
        commands = [
            {"id": "add-change", "type": "major", "description": "This is my major description"},
            {"id": "add-change", "type": "minor", "description": "This is my minor description"},
            {"id": "add-change", "type": "patch", "description": "This is my patch description"},
            {"id": "release"},
            {"id": "add-change", "type": "major", "description": "This is my major description"},
            {"id": "add-change", "type": "minor", "description": "This is my minor description"},
            {"id": "add-change", "type": "patch", "description": "This is my patch description"},
            {"id": "release"},
            {"id": "changelog"}
        ]

        result = command_processor(commands, self.directory_name)
        self.assertEqual(result.output, fixtures.CHANGELOG_4)

    def test_cli_execution_current_version(self):
        commands = [
            {"id": "current-version"}
        ]

        result = command_processor(commands, self.directory_name)
        self.assertIn("0.0.0", result.output)

    def test_cli_execution_add_change(self):
        commands = [
            {"id": "add-change", "type": "minor", "description": "This is my minor description"},
            {"id": "release"},
            {"id": "current-version"}
        ]

        result = command_processor(commands, self.directory_name)
        self.assertIn("0.1.0", result.output)

    def test_cli_version(self):
        runner = CliRunner()
        result = runner.invoke(cli=cli, args=['--version'])

        assert not result.exception
        assert result.exit_code == 0
        assert __version__.__version__ in result.output


class ExistingDataTestCase(unittest.TestCase):
    directory_name = None
    changes_dirname = None
    next_release_dirname = None

    def setUp(self):
        self.directory_name = tempfile.mkdtemp()
        self.changes_dirname = os.path.join(self.directory_name, '.changes')
        self.next_release_dirname = os.path.join(self.changes_dirname, 'next-release')
        os.mkdir(self.changes_dirname)
        with open(os.path.join(self.changes_dirname, "0.1.0.json"), 'x') as output:
            output.write(fixtures.VERSION_0_1_0)
        with open(os.path.join(self.changes_dirname, "0.2.0.json"), 'x') as output:
            output.write(fixtures.VERSION_0_2_0)
        print("Created directory: " + self.directory_name)

    def tearDown(self):
        print("Removing directory: " + self.directory_name)
        shutil.rmtree(self.directory_name)

    def test_generate_changelog_single_patch(self):
        commands = [
            {"id": "changelog"}
        ]

        result = command_processor(commands, self.directory_name)
        self.assertEqual(result.output, fixtures.CHANGELOG_5)

    def test_cli_execution_current_version(self):
        commands = [
            {"id": "current-version"}
        ]

        result = command_processor(commands, self.directory_name)
        self.assertIn("0.2.0", result.output)

    def test_generate_changelog_add_new_patch(self):
        commands = [
            {"id": "add-change", "type": "patch", "description": "This is my patch description"},
            {"id": "release"},
            {"id": "changelog"}
        ]

        result = command_processor(commands, self.directory_name)
        self.assertEqual(result.output, fixtures.CHANGELOG_6)


if __name__ == '__main__':
    unittest.main()
