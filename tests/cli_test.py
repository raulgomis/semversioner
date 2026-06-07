import json
import os
import re
import shutil
import tempfile

import pytest
from click.testing import CliRunner, Result
from importlib_resources import files
from importlib_resources.abc import Traversable

from semversioner import __version__
from semversioner.cli import cli, parse_key_value_pair
from tests import fixtures


def command_processor(commands: list[list[str]], path: str) -> Result:
    runner = CliRunner()
    result: Result
    for command in commands:
        command_with_path = ["--path", path] + command
        result = runner.invoke(cli, command_with_path)
        assert not result.exception
        assert result.exit_code == 0
    return result


def single_command_processor(command: list[str], path: str) -> Result:
    runner = CliRunner()
    command_with_path = ["--path", path] + command
    result: Result = runner.invoke(cli, command_with_path)
    return result


def get_file(filename: str) -> Traversable:
    path: Traversable = files("tests.resources").joinpath(filename)
    return path


def read_file(filename: str) -> str:
    return files("tests.resources").joinpath(filename).read_text()


# TestUtilsParseKeyValue
def test_empty_input() -> None:
    # Test case 1: Empty input
    assert parse_key_value_pair(None, None, []) is None


def test_single_key_value_pair() -> None:
    # Test case 2: Single key-value pair
    input1 = ["key1=value1"]
    expected_output1 = {"key1": "value1"}
    assert parse_key_value_pair(None, None, input1) == expected_output1


def test_multiple_key_value_pairs() -> None:
    # Test case 3: Multiple key-value pairs
    input2 = ["key1=value1", "key2=value2", "key3=value3"]
    expected_output2 = {"key1": "value1", "key2": "value2", "key3": "value3"}
    assert parse_key_value_pair(None, None, input2) == expected_output2


def test_special_characters_in_key_value_pairs() -> None:
    # Test case 4: Key-value pairs with special characters
    input3 = ["key1=value1", "key2=value2", "key3=value3", "key4=1+2=3=3"]
    expected_output3 = {"key1": "value1", "key2": "value2", "key3": "value3", "key4": "1+2=3=3"}
    assert parse_key_value_pair(None, None, input3) == expected_output3


def test_empty_values_in_key_value_pairs() -> None:
    # Test case 5: Key-value pairs with empty values
    input4 = ["key1=", "key2=value2", "key3="]
    expected_output4 = {"key1": "", "key2": "value2", "key3": ""}
    assert parse_key_value_pair(None, None, input4) == expected_output4


@pytest.fixture
def directory_name():
    dir_name = tempfile.mkdtemp()
    yield dir_name
    shutil.rmtree(dir_name)


@pytest.fixture
def changes_dirname(directory_name):
    return os.path.join(directory_name, ".semversioner")


@pytest.fixture
def next_release_dirname(changes_dirname):
    return os.path.join(changes_dirname, "next-release")


# AddChangeCommandTest
def test_add_change_write_new_change(directory_name, next_release_dirname) -> None:
    commands = [
        ["add-change", "--type", "major", "--description", "This is my major description"],
        ["add-change", "--type", "minor", "--description", "This is my minor description"],
        ["add-change", "--type", "patch", "--description", "This is my patch description"],
    ]

    result = command_processor(commands, directory_name)

    data = []
    files = sorted(os.listdir(next_release_dirname))

    for filename in files:
        with open(os.path.join(next_release_dirname, filename)) as f:
            data.append(json.load(f))

    expected = [
        {"type": "major", "description": "This is my major description"},
        {"type": "minor", "description": "This is my minor description"},
        {"type": "patch", "description": "This is my patch description"},
    ]

    assert expected == data
    assert re.search(rf"Successfully created file {re.escape(next_release_dirname)}.*\.json", result.output)


# ReleaseCommandTest
def test_release_write_new_change(directory_name, changes_dirname, next_release_dirname) -> None:
    commands = [
        ["add-change", "--type", "major", "--description", "This is my major description"],
        ["add-change", "--type", "minor", "--description", "This is my minor description"],
        ["add-change", "--type", "patch", "--description", "This is my patch description"],
        ["release"],
    ]

    result = command_processor(commands, directory_name)
    assert (
        result.output
        == f"Releasing version: 0.0.0 -> 1.0.0\nGenerated '{os.path.join(changes_dirname, '1.0.0.json')}' file.\nRemoving changeset files in '{next_release_dirname}' directory.\nRemoving '{next_release_dirname}' directory.\nSuccessfully created new release: 1.0.0\n"
    )


# ChangelogCommandTest
def test_generate_changelog_empty(directory_name) -> None:
    commands = [
        ["add-change", "--type", "major", "--description", "This is my major description"],
        ["add-change", "--type", "minor", "--description", "This is my minor description"],
        ["changelog"],
    ]

    result = command_processor(commands, directory_name)
    assert result.output == "# Changelog\nNote: version releases in the 0.x.y range may introduce breaking changes.\n"


def test_generate_changelog_single_major(directory_name) -> None:
    commands = [
        ["add-change", "--type", "major", "--description", "This is my major description"],
        ["release"],
        ["changelog"],
    ]

    result = command_processor(commands, directory_name)
    assert result.output == fixtures.CHANGELOG_1


def test_generate_changelog_single_patch(directory_name) -> None:
    commands = [
        ["add-change", "--type", "patch", "--description", "This is my patch description"],
        ["release"],
        ["changelog"],
    ]

    result = command_processor(commands, directory_name)
    assert result.output == fixtures.CHANGELOG_2


def test_generate_changelog_multiple(directory_name) -> None:
    commands = [
        ["add-change", "--type", "patch", "--description", "This is my patch description"],
        ["release"],
        ["add-change", "--type", "major", "--description", "This is my major description"],
        ["release"],
        ["add-change", "--type", "major", "--description", "This is my major description"],
        ["release"],
        ["add-change", "--type", "minor", "--description", "This is my minor description"],
        ["release"],
        ["changelog"],
    ]

    result = command_processor(commands, directory_name)
    assert result.output == fixtures.CHANGELOG_3

    commands = [["changelog"]]

    result = command_processor(commands, directory_name)
    assert result.output == fixtures.CHANGELOG_3


def test_generate_changelog_multiple_new(directory_name) -> None:
    commands = [
        ["add-change", "--type", "major", "--description", "This is my major description"],
        ["add-change", "--type", "minor", "--description", "This is my minor description"],
        ["add-change", "--type", "patch", "--description", "This is my patch description"],
        ["release"],
        ["add-change", "--type", "major", "--description", "This is my major description"],
        ["add-change", "--type", "minor", "--description", "This is my minor description"],
        ["add-change", "--type", "patch", "--description", "This is my patch description"],
        ["release"],
        ["changelog"],
    ]

    result = command_processor(commands, directory_name)
    assert result.output == fixtures.CHANGELOG_4

    commands = [["changelog", "--version", "2.0.0"]]

    result = command_processor(commands, directory_name)
    assert result.output == fixtures.CHANGELOG_4_PARTIAL


def test_generate_changelog_filtering_non_existing_version(directory_name) -> None:
    commands = [["changelog", "--version", "2.0.0"]]

    result = command_processor(commands, directory_name)
    assert result.output == "# Changelog\nNote: version releases in the 0.x.y range may introduce breaking changes.\n"


def test_generate_changelog_with_custom_template(directory_name) -> None:
    commands = [
        ["add-change", "--type", "major", "--description", "This is my major description"],
        ["add-change", "--type", "minor", "--description", "This is my minor description"],
        ["add-change", "--type", "patch", "--description", "This is my patch description"],
        ["release"],
        ["add-change", "--type", "major", "--description", "This is my major description"],
        ["add-change", "--type", "minor", "--description", "This is my minor description"],
        [
            "add-change",
            "--type",
            "patch",
            "--description",
            "This is my patch description",
            "--attributes",
            "pr_id=322",
            "--attributes",
            "issue_id=123",
        ],
        ["release"],
        ["changelog"],
    ]

    result = command_processor(commands, directory_name)
    assert result.output == fixtures.CHANGELOG_4

    result = command_processor([["changelog", "--template", str(get_file("template_01.j2"))]], directory_name)
    assert result.output == read_file("template_01_readme.md")

    result = command_processor([["changelog", "--template", str(get_file("template_02.j2"))]], directory_name)
    assert result.output == read_file("template_02_readme.md")

    result = command_processor([["changelog", "--template", str(get_file("template_03.j2"))]], directory_name)
    assert result.output == read_file("template_03_readme.md")

    result = command_processor([["changelog", "--template", str(get_file("template_04.j2"))]], directory_name)
    assert result.output == read_file("template_04_readme.md")

    result = command_processor(
        [["changelog", "--version", "1.0.0", "--template", str(get_file("template_04.j2"))]], directory_name
    )
    assert result.output == fixtures.CHANGELOG_4_TEMPLATE_CURRENT_VERSION_PARTIAL

    result = command_processor([["changelog"]], directory_name)
    assert result.output == fixtures.CHANGELOG_4


def test_generate_changelog_with_custom_template_empty(directory_name) -> None:
    commands = [["changelog", "--template", str(get_file("template_01.j2"))]]

    result = command_processor(commands, directory_name)
    assert result.output == "# Changelog\n"


def test_generate_changelog_with_custom_not_existent(directory_name) -> None:
    result = single_command_processor(["changelog", "--template", "non-existent-file.j2"], directory_name)
    assert result.exit_code == 2
    assert "Error: Invalid value for '--template': 'non-existent-file.j2': No such file or directory" in result.output


# CurrentVersionCommandTest
def test_cli_execution_current_version(directory_name) -> None:
    commands = [["current-version"]]

    result = command_processor(commands, directory_name)
    assert "0.0.0" in result.output


def test_cli_execution_add_change_current_version(directory_name) -> None:
    commands = [
        ["add-change", "--type", "minor", "--description", "This is my minor description"],
        ["release"],
        ["current-version"],
    ]

    result = command_processor(commands, directory_name)
    assert "0.1.0" in result.output


# NextVersionCommandTest
def test_cli_execution_next_version(directory_name) -> None:
    runner = CliRunner()
    result = runner.invoke(cli=cli, args=["--path", directory_name, "next-version"])
    assert "Error: No changes found. No next version available." in result.output
    assert result.exit_code == -1


def test_cli_execution_next_change(directory_name) -> None:
    commands = [
        ["add-change", "--type", "minor", "--description", "This is my minor description"],
        ["next-version"],
    ]

    result = command_processor(commands, directory_name)
    assert result.output == "0.1.0"


def test_cli_execution_next_change_existing_version(directory_name) -> None:
    commands = [
        ["add-change", "--type", "minor", "--description", "This is my minor description"],
        ["release"],
        ["add-change", "--type", "minor", "--description", "This is my minor description"],
        ["next-version"],
    ]

    result = command_processor(commands, directory_name)
    assert result.output == "0.2.0"


# StatusCommandTest
def test_status_command_with_no_changes(directory_name) -> None:
    commands = [
        ["status"],
    ]

    result = command_processor(commands, directory_name)
    assert result.output == fixtures.TEST_STATUS_COMMAND_WITH_NO_CHANGES


def test_status_command_with_released_changes(directory_name) -> None:
    commands = [
        ["add-change", "--type", "minor", "--description", "This is my minor description"],
        ["release"],
        ["status"],
    ]

    result = command_processor(commands, directory_name)
    assert result.output == fixtures.TEST_STATUS_COMMAND_WITH_RELEASED_CHANGES


def test_status_command_with_unreleased_changes(directory_name) -> None:
    commands = [
        ["add-change", "--type", "minor", "--description", "This is my minor description"],
        ["status"],
    ]

    result = command_processor(commands, directory_name)
    assert result.output == fixtures.TEST_STATUS_COMMAND_WITH_UNRELEASED_CHANGES


# CheckCommandTest
def test_check_ok(directory_name) -> None:
    commands = [
        ["add-change", "--type", "major", "--description", "This is my major description"],
        ["add-change", "--type", "minor", "--description", "This is my minor description"],
        ["add-change", "--type", "patch", "--description", "This is my patch description"],
        ["check"],
    ]

    result = command_processor(commands, directory_name)
    assert result.output == "OK\n"


def test_check_nok(directory_name) -> None:
    result = single_command_processor(["check"], directory_name)
    assert result.exit_code == -1
    assert "Error: No changes to release." in result.output


# CliVersionCommandTest
def test_cli_version(directory_name) -> None:
    result = single_command_processor(["--version"], directory_name)
    assert not result.exception
    assert result.exit_code == 0
    assert __version__ in result.output


# LegacyChangesDataTestCase
@pytest.fixture
def legacy_changes_dir():
    directory_name = tempfile.mkdtemp()
    changes_dirname = os.path.join(directory_name, ".changes")
    next_release_dirname = os.path.join(changes_dirname, "next-release")
    os.mkdir(changes_dirname)
    with open(os.path.join(changes_dirname, "0.1.0.json"), "w") as output:
        output.write(fixtures.VERSION_0_1_0)
    with open(os.path.join(changes_dirname, "0.2.0.json"), "w") as output:
        output.write(fixtures.VERSION_0_2_0)
    yield directory_name, changes_dirname, next_release_dirname
    shutil.rmtree(directory_name)


def test_legacy_generate_changelog_single_patch(legacy_changes_dir) -> None:
    directory_name, _, _ = legacy_changes_dir
    commands = [["changelog"]]

    result = command_processor(commands, directory_name)
    assert result.output == fixtures.CHANGELOG_5


def test_legacy_cli_execution_current_version(legacy_changes_dir) -> None:
    directory_name, _, _ = legacy_changes_dir
    commands = [["current-version"]]

    result = command_processor(commands, directory_name)
    assert "0.2.0" in result.output


def test_legacy_generate_changelog_add_new_patch(legacy_changes_dir) -> None:
    directory_name, _, _ = legacy_changes_dir
    commands = [
        ["add-change", "--type", "patch", "--description", "This is my patch description"],
        ["release"],
        ["changelog"],
    ]

    result = command_processor(commands, directory_name)
    assert result.output == fixtures.CHANGELOG_6


# ExistingDataTestCase
@pytest.fixture
def existing_data_dir():
    directory_name = tempfile.mkdtemp()
    changes_dirname = os.path.join(directory_name, ".semversioner")
    next_release_dirname = os.path.join(changes_dirname, "next-release")
    os.makedirs(changes_dirname)
    with open(os.path.join(changes_dirname, "0.1.0.json"), "w") as output:
        output.write(fixtures.VERSION_0_1_0)
    with open(os.path.join(changes_dirname, "0.2.0.json"), "w") as output:
        output.write(fixtures.VERSION_0_2_0)
    yield directory_name, changes_dirname, next_release_dirname
    shutil.rmtree(directory_name)


def test_existing_generate_changelog_single_patch(existing_data_dir) -> None:
    directory_name, _, _ = existing_data_dir
    commands = [["changelog"]]

    result = command_processor(commands, directory_name)
    assert result.output == fixtures.CHANGELOG_5


def test_existing_cli_execution_current_version(existing_data_dir) -> None:
    directory_name, _, _ = existing_data_dir
    commands = [["current-version"]]

    result = command_processor(commands, directory_name)
    assert "0.2.0" in result.output


def test_existing_generate_changelog_add_new_patch(existing_data_dir) -> None:
    directory_name, _, _ = existing_data_dir
    commands = [
        ["add-change", "--type", "patch", "--description", "This is my patch description"],
        ["release"],
        ["changelog"],
    ]

    result = command_processor(commands, directory_name)
    assert result.output == fixtures.CHANGELOG_6


def test_existing_cli_execution_creating_correct_changeset_files(existing_data_dir) -> None:
    directory_name, _, next_release_dirname = existing_data_dir
    # Check directory doesn't exist
    assert not os.path.isdir(next_release_dirname)

    result = command_processor(
        [
            ["add-change", "--type", "patch", "--description", "This is my patch description"],
        ],
        directory_name,
    )

    assert os.path.isdir(next_release_dirname)
    assert len(os.listdir(next_release_dirname)) == 1

    result = command_processor([["release"]], directory_name)

    # Check directory was deleted
    assert not os.path.isdir(next_release_dirname)

    result = command_processor([["changelog"]], directory_name)
    assert result.output == fixtures.CHANGELOG_6

    # Check directory was deleted
    assert os.path.isdir(next_release_dirname)


# NonEmptyNextReleaseFolder
@pytest.fixture
def non_empty_next_release_dir():
    directory_name = tempfile.mkdtemp()
    changes_dirname = os.path.join(directory_name, ".semversioner")
    next_release_dirname = os.path.join(changes_dirname, "next-release")
    os.makedirs(next_release_dirname)
    with open(os.path.join(changes_dirname, "0.1.0.json"), "w") as output:
        output.write(fixtures.VERSION_0_1_0)
    with open(os.path.join(changes_dirname, "0.2.0.json"), "w") as output:
        output.write(fixtures.VERSION_0_2_0)
    with open(os.path.join(next_release_dirname, ".gitkeep"), "w") as output:
        pass
    yield directory_name, changes_dirname, next_release_dirname
    shutil.rmtree(directory_name)


def test_non_empty_generate_changelog_single_patch(non_empty_next_release_dir) -> None:
    directory_name, _, _ = non_empty_next_release_dir
    commands = [["changelog"]]

    result = command_processor(commands, directory_name)
    assert result.output == fixtures.CHANGELOG_5


def test_non_empty_cli_execution_current_version(non_empty_next_release_dir) -> None:
    directory_name, _, _ = non_empty_next_release_dir
    commands = [["current-version"]]

    result = command_processor(commands, directory_name)
    assert "0.2.0" in result.output


def test_non_empty_cli_execution_creating_correct_changeset_files(non_empty_next_release_dir) -> None:
    directory_name, _, next_release_dirname = non_empty_next_release_dir
    assert len(os.listdir(next_release_dirname)) == 1

    result = command_processor(
        [
            ["add-change", "--type", "patch", "--description", "This is my patch description"],
        ],
        directory_name,
    )

    assert len(os.listdir(next_release_dirname)) == 2

    result = command_processor([["release"], ["changelog"]], directory_name)
    assert result.output == fixtures.CHANGELOG_6
    assert len(os.listdir(next_release_dirname)) == 1


def test_cli_add_change_with_pre(directory_name, next_release_dirname) -> None:
    commands = [
        ["add-change", "--type", "patch", "--description", "Alpha change", "--pre", "alpha"],
    ]

    result = command_processor(commands, directory_name)

    files = os.listdir(next_release_dirname)
    assert len(files) == 1
    with open(os.path.join(next_release_dirname, files[0])) as f:
        data = json.load(f)

    assert data == {"type": "patch", "description": "Alpha change", "pre": "alpha"}
    assert "Successfully created file" in result.output


def test_cli_release_prerelease(directory_name) -> None:
    commands = [
        ["add-change", "--type", "minor", "--description", "Alpha feature", "--pre", "alpha"],
        ["release"],
    ]
    result = command_processor(commands, directory_name)
    assert "Successfully created new release: 0.1.0a1" in result.output


def test_cli_release_missing_changeset(directory_name) -> None:
    # Test releasing when there are no changesets (MissingChangesetError).
    result = single_command_processor(["release"], directory_name)
    assert result.exit_code == 0
    assert "Error: No changes to release. Skipping release process." in result.output


def test_cli_add_change_invalid_prerelease_type(directory_name) -> None:
    # Test add-change with an invalid prerelease type.
    result = single_command_processor(
        ["add-change", "--type", "patch", "--description", "Invalid prerelease", "--pre", "invalid"],
        directory_name,
    )
    assert result.exit_code == 2
    assert "Error: Invalid value for '--pre' / '-p': 'invalid' is not one of 'alpha', 'beta', 'rc'." in result.output


def test_cli_mixed_stable_and_prerelease_error(directory_name) -> None:
    # Test release, next-version, and status when both stable and prerelease changes exist.
    # 1. Add stable and prerelease changes
    commands = [
        ["add-change", "--type", "minor", "--description", "Stable feature"],
        ["add-change", "--type", "minor", "--description", "Alpha feature", "--pre", "alpha"],
    ]
    runner = CliRunner()
    for command in commands:
        result = runner.invoke(cli, ["--path", directory_name] + command)
        assert result.exit_code == 0

    # 2. Test status command fails cleanly
    result_status = runner.invoke(cli, ["--path", directory_name, "status"])
    assert result_status.exit_code != 0
    assert "Error: Cannot have both stable and prerelease changes in the same release." in result_status.output

    # 3. Test next-version command fails cleanly
    result_next = runner.invoke(cli, ["--path", directory_name, "next-version"])
    assert result_next.exit_code != 0
    assert "Error: Cannot have both stable and prerelease changes in the same release." in result_next.output

    # 4. Test release command fails cleanly
    result_release = runner.invoke(cli, ["--path", directory_name, "release"])
    assert result_release.exit_code != 0
    assert "Error: Cannot have both stable and prerelease changes in the same release." in result_release.output
