import json
import os
import re
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import List

from click.testing import CliRunner, Result
from importlib_resources import files

from semversioner import __version__
from semversioner.cli import cli, parse_key_value_pair
from tests import fixtures


def command_processor(commands: List[List[str]], path: str) -> Result:
    runner = CliRunner()
    result: Result
    for command in commands:
        command_with_path = ["--path", path] + command
        result = runner.invoke(cli, command_with_path)
        assert not result.exception
        assert result.exit_code == 0
    return result


def single_command_processor(command: List[str], path: str) -> Result:
    runner = CliRunner()
    command_with_path = ["--path", path] + command
    result: Result = runner.invoke(cli, command_with_path)
    return result


def get_file(filename: str) -> Path: 
    path: Path = files('tests.resources').joinpath(filename)
    return path


def read_file(filename: str) -> str:
    return files('tests.resources').joinpath(filename).read_text()  # type: ignore


class TestUtilsParseKeyValue(unittest.TestCase):

    def test_empty_input(self) -> None:
        # Test case 1: Empty input
        assert parse_key_value_pair(None, None, []) is None

    def test_single_key_value_pair(self) -> None:
        # Test case 2: Single key-value pair
        input1 = ['key1=value1']
        expected_output1 = {'key1': 'value1'}
        assert parse_key_value_pair(None, None, input1) == expected_output1

    def test_multiple_key_value_pairs(self) -> None:
        # Test case 3: Multiple key-value pairs
        input2 = ['key1=value1', 'key2=value2', 'key3=value3']
        expected_output2 = {'key1': 'value1', 'key2': 'value2', 'key3': 'value3'}
        assert parse_key_value_pair(None, None, input2) == expected_output2

    def test_special_characters_in_key_value_pairs(self) -> None:
        # Test case 4: Key-value pairs with special characters
        input3 = ['key1=value1', 'key2=value2', 'key3=value3', 'key4=1+2=3=3']
        expected_output3 = {'key1': 'value1', 'key2': 'value2', 'key3': 'value3', 'key4': '1+2=3=3'}
        assert parse_key_value_pair(None, None, input3) == expected_output3

    def test_empty_values_in_key_value_pairs(self) -> None:
        # Test case 5: Key-value pairs with empty values
        input4 = ['key1=', 'key2=value2', 'key3=']
        expected_output4 = {'key1': '', 'key2': 'value2', 'key3': ''}
        assert parse_key_value_pair(None, None, input4) == expected_output4


class CommandTest(unittest.TestCase):
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


class AddChangeCommandTest(CommandTest):

    def test_write_new_change(self) -> None:
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
        self.assertRegex(result.output, rf"Successfully created file {re.escape(self.next_release_dirname)}.*\.json")


class ReleaseCommandTest(CommandTest):

    def test_write_new_change(self) -> None:
        commands = [
            ["add-change", "--type", "major", "--description", "This is my major description"],
            ["add-change", "--type", "minor", "--description", "This is my minor description"],
            ["add-change", "--type", "patch", "--description", "This is my patch description"],
            ["release"]
        ]

        result = command_processor(commands, self.directory_name)
        self.assertEqual(result.output, f"Releasing version: 0.0.0 -> 1.0.0\nGenerated '{os.path.join(self.changes_dirname, '1.0.0.json')}' file.\nRemoving changeset files in '{self.next_release_dirname}' directory.\nRemoving '{self.next_release_dirname}' directory.\nSuccessfully created new release: 1.0.0\n")


class ChangelogCommandTest(CommandTest):

    def test_generate_changelog_empty(self) -> None:
        commands = [
            ["add-change", "--type", "major", "--description", "This is my major description"],
            ["add-change", "--type", "minor", "--description", "This is my minor description"],
            ["changelog"]
        ]

        result = command_processor(commands, self.directory_name)
        self.assertEqual(result.output, "# Changelog\nNote: version releases in the 0.x.y range may introduce breaking changes.\n")

    def test_generate_changelog_single_major(self) -> None:
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

    def test_generate_changelog_single_patch(self) -> None:
        commands = [
            ["add-change", "--type", "patch", "--description", "This is my patch description"],
            ["release"],
            ["changelog"]
        ]

        result = command_processor(commands, self.directory_name)
        self.assertEqual(result.output, fixtures.CHANGELOG_2)

    def test_generate_changelog_multiple(self) -> None:
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

    def test_generate_changelog_multiple_new(self) -> None:  
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

    def test_generate_changelog_filtering_non_existing_version(self) -> None:
        commands = [
            ["changelog", "--version", "2.0.0"]
        ]

        result = command_processor(commands, self.directory_name)
        self.assertEqual(result.output, "# Changelog\nNote: version releases in the 0.x.y range may introduce breaking changes.\n")

    def test_generate_changelog_with_custom_template(self) -> None:  
        commands = [
            ["add-change", "--type", "major", "--description", "This is my major description"],
            ["add-change", "--type", "minor", "--description", "This is my minor description"],
            ["add-change", "--type", "patch", "--description", "This is my patch description"],
            ["release"],
            ["add-change", "--type", "major", "--description", "This is my major description"],
            ["add-change", "--type", "minor", "--description", "This is my minor description"],
            ["add-change", "--type", "patch", "--description", "This is my patch description", "--attributes", "pr_id=322", "--attributes", "issue_id=123"],
            ["release"],
            ["changelog"]
        ]

        result = command_processor(commands, self.directory_name)
        self.assertEqual(result.output, fixtures.CHANGELOG_4)

        result = command_processor([
            ["changelog", "--template", str(get_file("template_01.j2"))]
        ], self.directory_name)

        self.assertEqual(result.output, read_file("template_01_readme.md"))

        result = command_processor([
            ["changelog", "--template", str(get_file("template_02.j2"))]
        ], self.directory_name)

        self.assertEqual(result.output, read_file("template_02_readme.md"))

        result = command_processor([
            ["changelog", "--template", str(get_file("template_03.j2"))]
        ], self.directory_name)

        self.assertEqual(result.output, read_file("template_03_readme.md"))

        result = command_processor([
            ["changelog", "--template", str(get_file("template_04.j2"))]
        ], self.directory_name)

        self.assertEqual(result.output, read_file("template_04_readme.md"))

        result = command_processor([
            ["changelog", "--version", "1.0.0", "--template", str(get_file("template_04.j2"))]
        ], self.directory_name)

        self.assertEqual(result.output, fixtures.CHANGELOG_4_TEMPLATE_CURRENT_VERSION_PARTIAL)

        result = command_processor([
            ["changelog"]
        ], self.directory_name)

        self.assertEqual(result.output, fixtures.CHANGELOG_4)

    def test_generate_changelog_with_custom_template_empty(self) -> None:  
        commands = [
            ["changelog", "--template", str(get_file("template_01.j2"))]
        ]

        result = command_processor(commands, self.directory_name)
        self.assertEqual(result.output, "# Changelog\n")

    def test_generate_changelog_with_custom_not_existent(self) -> None: 
        result = single_command_processor(["changelog", "--template", "non-existent-file.j2"], self.directory_name)
        assert result.exit_code == 2
        assert "Error: Invalid value for '--template': 'non-existent-file.j2': No such file or directory" in result.output


class CurrentVersionCommandTest(CommandTest):

    def test_cli_execution_current_version(self) -> None:
        commands = [
            ["current-version"]
        ]

        result = command_processor(commands, self.directory_name)
        self.assertIn("0.0.0", result.output)

    def test_cli_execution_add_change(self) -> None:
        commands = [
            ["add-change", "--type", "minor", "--description", "This is my minor description"],
            ["release"],
            ["current-version"]
        ]

        result = command_processor(commands, self.directory_name)
        self.assertIn("0.1.0", result.output)


class NextVersionCommandTest(CommandTest):

    def test_cli_execution_next_version(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli=cli, args=["--path", self.directory_name, "next-version"])
        assert "Error: No changes found. No next version available." in result.output
        assert result.exit_code == -1

    def test_cli_execution_next_change(self) -> None:
        commands = [
            ["add-change", "--type", "minor", "--description", "This is my minor description"],
            ["next-version"]
        ]

        result = command_processor(commands, self.directory_name)
        self.assertEqual("0.1.0", result.output)

    def test_cli_execution_next_change_existing_version(self) -> None:
        commands = [
            ["add-change", "--type", "minor", "--description", "This is my minor description"],
            ["release"],
            ["add-change", "--type", "minor", "--description", "This is my minor description"],
            ["next-version"]
        ]

        result = command_processor(commands, self.directory_name)
        self.assertEqual("0.2.0", result.output)


class StatusCommandTest(CommandTest):

    def test_status_command_with_no_changes(self) -> None:
        commands = [
            ["status"],
        ]

        result = command_processor(commands, self.directory_name)
        self.assertEqual(fixtures.TEST_STATUS_COMMAND_WITH_NO_CHANGES, result.output)

    def test_status_command_with_released_changes(self) -> None:
        commands = [
            ["add-change", "--type", "minor", "--description", "This is my minor description"],
            ["release"],
            ["status"],
        ]

        result = command_processor(commands, self.directory_name)
        self.assertEqual(fixtures.TEST_STATUS_COMMAND_WITH_RELEASED_CHANGES, result.output)

    def test_status_command_with_unreleased_changes(self) -> None:
        commands = [
            ["add-change", "--type", "minor", "--description", "This is my minor description"],
            ["status"],
        ]

        result = command_processor(commands, self.directory_name)
        self.assertEqual(fixtures.TEST_STATUS_COMMAND_WITH_UNRELEASED_CHANGES, result.output)


class CheckCommandTest(CommandTest):

    def test_check_ok(self) -> None:
        commands = [
            ["add-change", "--type", "major", "--description", "This is my major description"],
            ["add-change", "--type", "minor", "--description", "This is my minor description"],
            ["add-change", "--type", "patch", "--description", "This is my patch description"],
            ["check"]
        ]

        result = command_processor(commands, self.directory_name)
        self.assertEqual('OK\n', result.output)

    def test_check_nok(self) -> None:
        result = single_command_processor(["check"], self.directory_name)
        assert result.exit_code == -1
        assert "Error: No changes to release." in result.output


class CliVersionCommandTest(CommandTest):
    def test_cli_version(self) -> None:
        result = single_command_processor(["--version"], self.directory_name)
        assert not result.exception
        assert result.exit_code == 0
        assert __version__.__version__ in result.output


class LegacyChangesDataTestCase(unittest.TestCase):
    directory_name: str
    changes_dirname: str
    next_release_dirname: str

    def setUp(self) -> None:
        self.directory_name = tempfile.mkdtemp()
        self.changes_dirname = os.path.join(self.directory_name, '.changes')
        self.next_release_dirname = os.path.join(self.changes_dirname, 'next-release')
        os.mkdir(self.changes_dirname)
        with open(os.path.join(self.changes_dirname, "0.1.0.json"), 'w') as output:
            output.write(fixtures.VERSION_0_1_0)
        with open(os.path.join(self.changes_dirname, "0.2.0.json"), 'w') as output:
            output.write(fixtures.VERSION_0_2_0)
        print("Created directory: " + self.directory_name)

    def tearDown(self) -> None:
        print("Removing directory: " + self.directory_name)
        shutil.rmtree(self.directory_name)

    def test_generate_changelog_single_patch(self) -> None:
        commands = [
            ["changelog"]
        ]

        result = command_processor(commands, self.directory_name)
        self.assertEqual(result.output, fixtures.CHANGELOG_5)

    def test_cli_execution_current_version(self) -> None:
        commands = [
            ["current-version"]
        ]

        result = command_processor(commands, self.directory_name)
        self.assertIn("0.2.0", result.output)

    def test_generate_changelog_add_new_patch(self) -> None:
        commands = [
            ["add-change", "--type", "patch", "--description", "This is my patch description"],
            ["release"],
            ["changelog"]
        ]

        result = command_processor(commands, self.directory_name)
        self.assertEqual(result.output, fixtures.CHANGELOG_6)


class ExistingDataTestCase(unittest.TestCase):
    directory_name: str
    changes_dirname: str
    next_release_dirname: str

    def setUp(self) -> None:
        self.directory_name = tempfile.mkdtemp()
        self.changes_dirname = os.path.join(self.directory_name, '.semversioner')
        self.next_release_dirname = os.path.join(self.changes_dirname, 'next-release')
        os.makedirs(self.changes_dirname)
        with open(os.path.join(self.changes_dirname, "0.1.0.json"), 'w') as output:
            output.write(fixtures.VERSION_0_1_0)
        with open(os.path.join(self.changes_dirname, "0.2.0.json"), 'w') as output:
            output.write(fixtures.VERSION_0_2_0)
        print("Created directory: " + self.directory_name)

    def tearDown(self) -> None:
        print("Removing directory: " + self.directory_name)
        shutil.rmtree(self.directory_name)

    def test_generate_changelog_single_patch(self) -> None:
        commands = [
            ["changelog"]
        ]

        result = command_processor(commands, self.directory_name)
        self.assertEqual(result.output, fixtures.CHANGELOG_5)

    def test_cli_execution_current_version(self) -> None:
        commands = [
            ["current-version"]
        ]

        result = command_processor(commands, self.directory_name)
        self.assertIn("0.2.0", result.output)

    def test_generate_changelog_add_new_patch(self) -> None:
        commands = [
            ["add-change", "--type", "patch", "--description", "This is my patch description"],
            ["release"],
            ["changelog"]
        ]

        result = command_processor(commands, self.directory_name)
        self.assertEqual(result.output, fixtures.CHANGELOG_6)

    def test_cli_execution_creating_correct_changeset_files(self) -> None:
        # Check directory doesn't exist
        self.assertFalse(os.path.isdir(self.next_release_dirname))

        result = command_processor([
            ["add-change", "--type", "patch", "--description", "This is my patch description"],
        ], self.directory_name)

        self.assertTrue(os.path.isdir(self.next_release_dirname))
        self.assertEqual(len(os.listdir(self.next_release_dirname)), 1)

        result = command_processor([
            ["release"]
        ], self.directory_name)

        # Check directory was deleted
        self.assertFalse(os.path.isdir(self.next_release_dirname))

        result = command_processor([
            ["changelog"]
        ], self.directory_name)
        self.assertEqual(result.output, fixtures.CHANGELOG_6)

        # Check directory was deleted
        self.assertTrue(os.path.isdir(self.next_release_dirname))


class NonEmptyNextReleaseFolder(unittest.TestCase):
    directory_name: str
    changes_dirname: str
    next_release_dirname: str

    def setUp(self) -> None:
        self.directory_name = tempfile.mkdtemp()
        self.changes_dirname = os.path.join(self.directory_name, '.semversioner')
        self.next_release_dirname = os.path.join(self.changes_dirname, 'next-release')
        os.makedirs(self.next_release_dirname)
        with open(os.path.join(self.changes_dirname, "0.1.0.json"), 'w') as output:
            output.write(fixtures.VERSION_0_1_0)
        with open(os.path.join(self.changes_dirname, "0.2.0.json"), 'w') as output:
            output.write(fixtures.VERSION_0_2_0)
        with open(os.path.join(self.next_release_dirname, ".gitkeep"), 'w') as output:
            pass
        print("Created directory: " + self.directory_name)

    def tearDown(self) -> None:
        print("Removing directory: " + self.directory_name)
        shutil.rmtree(self.directory_name)

    def test_generate_changelog_single_patch(self) -> None:
        commands = [
            ["changelog"]
        ]

        result = command_processor(commands, self.directory_name)
        self.assertEqual(result.output, fixtures.CHANGELOG_5)

    def test_cli_execution_current_version(self) -> None:
        commands = [
            ["current-version"]
        ]

        result = command_processor(commands, self.directory_name)
        self.assertIn("0.2.0", result.output)

    def test_cli_execution_creating_correct_changeset_files(self) -> None:
        self.assertEqual(len(os.listdir(self.next_release_dirname)), 1)

        result = command_processor([
            ["add-change", "--type", "patch", "--description", "This is my patch description"],
        ], self.directory_name)

        self.assertEqual(len(os.listdir(self.next_release_dirname)), 2)

        result = command_processor([
            ["release"],
            ["changelog"]
        ], self.directory_name)
        self.assertEqual(result.output, fixtures.CHANGELOG_6)
        self.assertEqual(len(os.listdir(self.next_release_dirname)), 1)


if __name__ == '__main__':
    unittest.main()
