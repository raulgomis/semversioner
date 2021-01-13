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
        command_with_path = ["--path", path] + command
        result = runner.invoke(cli, command_with_path)
        assert not result.exception
        assert result.exit_code == 0
    return result


class CommandTest(unittest.TestCase):
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


class AddChangeCommandTest(CommandTest):

    def test_write_new_change(self):
        commands = [
            ["add-change", "--type", "major", "--description", "This is my major description"],
            ["add-change", "--type", "minor", "--description", "This is my minor description"],
            ["add-change", "--type", "patch", "--description", "This is my patch description"]
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


class ChangelogCommandTest(CommandTest):

    def test_generate_changelog_empty(self):
        commands = [
            ["add-change", "--type", "major", "--description", "This is my major description"],
            ["add-change", "--type", "minor", "--description", "This is my minor description"],
            ["changelog"]
        ]

        result = command_processor(commands, self.directory_name)
        self.assertEqual(result.output, "# Changelog\nNote: version releases in the 0.x.y range may introduce breaking changes.\n")

    def test_generate_changelog_single_major(self):
        commands = [
            ["add-change", "--type", "major", "--description", "This is my major description"],
            ["release"],
            ["changelog"]
        ]

        commands = [
            ["add-change", "--type", "major", "--description", "This is my major description"],
            ["release"],
            ["changelog"]
        ]

        result = command_processor(commands, self.directory_name)
        self.assertEqual(result.output, fixtures.CHANGELOG_1)

    def test_generate_changelog_single_patch(self):
        commands = [
            ["add-change", "--type", "patch", "--description", "This is my patch description"],
            ["release"],
            ["changelog"]
        ]

        result = command_processor(commands, self.directory_name)
        self.assertEqual(result.output, fixtures.CHANGELOG_2)

    def test_generate_changelog_multiple(self):
        commands = [
            ["add-change", "--type", "patch", "--description", "This is my patch description"],
            ["release"],
            ["add-change", "--type", "major", "--description", "This is my major description"],
            ["release"],
            ["add-change", "--type", "major", "--description", "This is my major description"],
            ["release"],
            ["add-change", "--type", "minor", "--description", "This is my minor description"],
            ["release"],
            ["changelog"]
        ]

        result = command_processor(commands, self.directory_name)
        self.assertEqual(result.output, fixtures.CHANGELOG_3)

        commands = [
            ["changelog"]
        ]

        result = command_processor(commands, self.directory_name)
        self.assertEqual(result.output, fixtures.CHANGELOG_3)

    def test_generate_changelog_multiple_new(self):  
        commands = [
            ["add-change", "--type", "major", "--description", "This is my major description"],
            ["add-change", "--type", "minor", "--description", "This is my minor description"],
            ["add-change", "--type", "patch", "--description", "This is my patch description"],
            ["release"],
            ["add-change", "--type", "major", "--description", "This is my major description"],
            ["add-change", "--type", "minor", "--description", "This is my minor description"],
            ["add-change", "--type", "patch", "--description", "This is my patch description"],
            ["release"],
            ["changelog"]
        ]

        result = command_processor(commands, self.directory_name)
        self.assertEqual(result.output, fixtures.CHANGELOG_4)

        commands = [
            ["changelog", "--version", "2.0.0"]
        ]

        result = command_processor(commands, self.directory_name)
        self.assertEqual(result.output, fixtures.CHANGELOG_4_PARTIAL)

    def test_generate_changelog_filtering_non_existing_version(self):
        commands = [
            ["changelog", "--version", "2.0.0"]
        ]

        result = command_processor(commands, self.directory_name)
        self.assertEqual(result.output, "# Changelog\nNote: version releases in the 0.x.y range may introduce breaking changes.\n")


class CurrentVersionCommandTest(CommandTest):

    def test_cli_execution_current_version(self):
        commands = [
            ["current-version"]
        ]

        result = command_processor(commands, self.directory_name)
        self.assertIn("0.0.0", result.output)

    def test_cli_execution_add_change(self):
        commands = [
            ["add-change", "--type", "minor", "--description", "This is my minor description"],
            ["release"],
            ["current-version"]
        ]

        result = command_processor(commands, self.directory_name)
        self.assertIn("0.1.0", result.output)


class StatusCommandTest(CommandTest):

    def test_status_command_with_no_changes(self):
        commands = [
            ["status"],
        ]

        result = command_processor(commands, self.directory_name)
        self.assertEqual(fixtures.TEST_STATUS_COMMAND_WITH_NO_CHANGES, result.output)

    def test_status_command_with_released_changes(self):
        commands = [
            ["add-change", "--type", "minor", "--description", "This is my minor description"],
            ["release"],
            ["status"],
        ]

        result = command_processor(commands, self.directory_name)
        self.assertEqual(fixtures.TEST_STATUS_COMMAND_WITH_RELEASED_CHANGES, result.output)

    def test_status_command_with_unreleased_changes(self):
        commands = [
            ["add-change", "--type", "minor", "--description", "This is my minor description"],
            ["status"],
        ]

        result = command_processor(commands, self.directory_name)
        self.assertEqual(fixtures.TEST_STATUS_COMMAND_WITH_UNRELEASED_CHANGES, result.output)


class CliVersionCommandTest(CommandTest):
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
            ["changelog"]
        ]

        result = command_processor(commands, self.directory_name)
        self.assertEqual(result.output, fixtures.CHANGELOG_5)

    def test_cli_execution_current_version(self):
        commands = [
            ["current-version"]
        ]

        result = command_processor(commands, self.directory_name)
        self.assertIn("0.2.0", result.output)

    def test_generate_changelog_add_new_patch(self):
        commands = [
            ["add-change", "--type", "patch", "--description", "This is my patch description"],
            ["release"],
            ["changelog"]
        ]

        result = command_processor(commands, self.directory_name)
        self.assertEqual(result.output, fixtures.CHANGELOG_6)


if __name__ == '__main__':
    unittest.main()
