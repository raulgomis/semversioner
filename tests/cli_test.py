import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import List

from click.testing import CliRunner, Result
from importlib_resources import files

from semversioner import __version__
from semversioner.cli import cli
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
    return files('tests.resources').joinpath(filename)  # type: ignore


def read_file(filename: str) -> str:
    return files('tests.resources').joinpath(filename).read_text()  # type: ignore


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
        self.assertRegex(result.output, f"Successfully created file {self.next_release_dirname}.*\\.json")


class ReleaseCommandTest(CommandTest):

    def test_write_new_change(self) -> None:
        commands = [
            ["add-change", "--type", "major", "--description", "This is my major description"],
            ["add-change", "--type", "minor", "--description", "This is my minor description"],
            ["add-change", "--type", "patch", "--description", "This is my patch description"],
            ["release"]
        ]

        result = command_processor(commands, self.directory_name)
        self.assertEqual(result.output, f"Releasing version: 0.0.0 -> 1.0.0\nGenerated '{self.changes_dirname}/1.0.0.json' file.\nRemoving '{self.next_release_dirname}' directory.\nSuccessfully created new release: 1.0.0\n")


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
            ["add-change", "--type", "patch", "--description", "This is my patch description"],
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


class ExistingDataTestCase(unittest.TestCase):
    directory_name: str
    changes_dirname: str
    next_release_dirname: str

    def setUp(self) -> None:
        self.directory_name = tempfile.mkdtemp()
        self.changes_dirname = os.path.join(self.directory_name, '.changes')
        self.next_release_dirname = os.path.join(self.changes_dirname, 'next-release')
        os.mkdir(self.changes_dirname)
        with open(os.path.join(self.changes_dirname, "0.1.0.json"), 'x') as output:
            output.write(fixtures.VERSION_0_1_0)
        with open(os.path.join(self.changes_dirname, "0.2.0.json"), 'x') as output:
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


if __name__ == '__main__':
    unittest.main()
