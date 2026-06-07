import os
import shutil
import tempfile
import threading

import pytest

from semversioner import ReleaseStatus, Semversioner
from semversioner.models import Changeset, MissingChangesetError, SemversionerError


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


def test_increase_version(directory_name: str) -> None:
    releaser = Semversioner(directory_name)
    assert releaser._get_next_version_from_type("1.0.0", "minor") == "1.1.0"
    assert releaser._get_next_version_from_type("1.0.0", "major") == "2.0.0"
    assert releaser._get_next_version_from_type("1.0.0", "patch") == "1.0.1"
    assert releaser._get_next_version_from_type("0.1.1", "minor") == "0.2.0"
    assert releaser._get_next_version_from_type("0.1.1", "major") == "1.0.0"
    assert releaser._get_next_version_from_type("0.1.1", "patch") == "0.1.2"
    assert releaser._get_next_version_from_type("9.9.9", "minor") == "9.10.0"
    assert releaser._get_next_version_from_type("9.9.9", "major") == "10.0.0"
    assert releaser._get_next_version_from_type("9.9.9", "patch") == "9.9.10"


def test_commands_with_no_changesets(directory_name: str) -> None:
    releaser = Semversioner(path=directory_name)
    assert (
        releaser.generate_changelog()
        == "# Changelog\nNote: version releases in the 0.x.y range may introduce breaking changes.\n"
    )
    assert releaser.get_last_version() == "0.0.0"
    assert releaser.get_status() == ReleaseStatus(version="0.0.0", next_version=None, unreleased_changes=[])
    with pytest.raises(MissingChangesetError):
        releaser.release()


def test_release(directory_name: str) -> None:
    releaser = Semversioner(path=directory_name)

    releaser.add_change("minor", "My description")
    releaser.add_change("major", "My description")
    assert releaser.get_status() == ReleaseStatus(
        version="0.0.0",
        next_version="1.0.0",
        unreleased_changes=[
            Changeset(type="major", description="My description"),
            Changeset(type="minor", description="My description"),
        ],
    )
    releaser.release()
    assert releaser.get_status() == ReleaseStatus(version="1.0.0", next_version=None, unreleased_changes=[])
    with pytest.raises(MissingChangesetError):
        releaser.release()


def test_release_with_attributes(directory_name: str) -> None:
    releaser = Semversioner(path=directory_name)

    releaser.add_change("minor", "My description", attributes={"key": "value"})
    releaser.add_change("major", "My description", attributes={"key2": "value2", "key3": "value3"})
    assert releaser.get_status() == ReleaseStatus(
        version="0.0.0",
        next_version="1.0.0",
        unreleased_changes=[
            Changeset(type="major", description="My description", attributes={"key2": "value2", "key3": "value3"}),
            Changeset(type="minor", description="My description", attributes={"key": "value"}),
        ],
    )
    releaser.release()
    assert releaser.get_status() == ReleaseStatus(version="1.0.0", next_version=None, unreleased_changes=[])
    with pytest.raises(MissingChangesetError):
        releaser.release()


def test_release_stress(directory_name: str) -> None:
    releaser = Semversioner(path=directory_name)

    expected = []
    for i in range(100):
        releaser.add_change("major", f"My description {i}")
        expected.append(Changeset(type="major", description=f"My description {i}"))

    expected = sorted(expected, key=lambda k: k.type + k.description)
    assert releaser.get_status() == ReleaseStatus(version="0.0.0", next_version="1.0.0", unreleased_changes=expected)
    releaser.release()
    assert releaser.get_status() == ReleaseStatus(version="1.0.0", next_version=None, unreleased_changes=[])


def test_concurrent_changeset_creation_race_condition(directory_name: str, next_release_dirname: str) -> None:
    """
    Test that concurrent changeset creation does not result in file creation race conditions.
    """
    releaser = Semversioner(directory_name)
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
    files = [f for f in os.listdir(next_release_dirname) if f.endswith(".json")]
    assert len(files) == num_threads
    # Optionally, check that all descriptions are present
    found_descriptions = set()
    for f in files:
        with open(os.path.join(next_release_dirname, f)) as fh:
            data = fh.read()
            for desc in descriptions:
                if desc in data:
                    found_descriptions.add(desc)
    assert set(descriptions) == found_descriptions


def test_is_deprecated(directory_name: str) -> None:
    releaser = Semversioner(directory_name)
    assert not releaser.is_deprecated()


def test_check_nok(directory_name: str) -> None:
    releaser = Semversioner(path=directory_name)
    assert not releaser.check()


def test_check_ok(directory_name: str) -> None:
    releaser = Semversioner(path=directory_name)

    assert not releaser.check()
    releaser.add_change("major", "My description")
    assert releaser.check()


def test_check_after_release(directory_name: str) -> None:
    releaser = Semversioner(path=directory_name)
    releaser.add_change("major", "My description")
    releaser.release()
    assert not releaser.check()


def test_get_next_version_prerelease(directory_name: str) -> None:
    releaser = Semversioner(directory_name)

    # 1. Test alpha prerelease patch bump from 0.0.0 -> 0.0.1a1
    releaser.add_change("patch", "change 1", pre="alpha")
    releaser.add_change("patch", "change 2", pre="alpha")
    assert releaser.get_next_version() == "0.0.1a1"
    releaser.release()
    assert releaser.get_last_version() == "0.0.1a1"

    # 2. Test beta prerelease bump from 0.0.1a1 -> 0.0.1b1
    releaser.add_change("patch", "change 3", pre="beta")
    assert releaser.get_next_version() == "0.0.1b1"
    releaser.release()
    assert releaser.get_last_version() == "0.0.1b1"

    # 3. Test mixed stable and prerelease changes raises SemversionerError
    releaser.add_change("patch", "stable change")
    releaser.add_change("patch", "prerelease change", pre="alpha")
    with pytest.raises(SemversionerError):
        releaser.get_next_version()


def test_core_status_with_prerelease(directory_name: str) -> None:
    # Test status command with unreleased prerelease changes.
    releaser = Semversioner(directory_name)
    releaser.add_change("minor", "Alpha feature", pre="alpha")
    status = releaser.get_status()
    assert status.version == "0.0.0"
    assert status.next_version == "0.1.0a1"
    assert len(status.unreleased_changes) == 1
    assert status.unreleased_changes[0].type == "minor"
    assert status.unreleased_changes[0].description == "Alpha feature"
    assert status.unreleased_changes[0].pre == "alpha"


def test_core_next_version_with_prerelease(directory_name: str) -> None:
    # Test next-version command with prerelease change.
    releaser = Semversioner(directory_name)
    releaser.add_change("minor", "Alpha feature", pre="alpha")
    assert releaser.get_next_version() == "0.1.0a1"


def test_core_mixed_stable_and_prerelease_error(directory_name: str) -> None:
    # Test release, next-version, and status when both stable and prerelease changes exist.
    releaser = Semversioner(directory_name)
    releaser.add_change("minor", "Stable feature")
    releaser.add_change("minor", "Alpha feature", pre="alpha")

    with pytest.raises(SemversionerError, match="Cannot have both stable and prerelease changes in the same release."):
        releaser.get_next_version()

    with pytest.raises(SemversionerError, match="Cannot have both stable and prerelease changes in the same release."):
        releaser.get_status()

    with pytest.raises(SemversionerError, match="Cannot have both stable and prerelease changes in the same release."):
        releaser.release()


def test_core_release_sequential_prerelease_flow(directory_name: str) -> None:
    # Test subsequent prerelease and stable release flows.
    releaser = Semversioner(directory_name)

    # Step 1: 0.0.0 -> 0.1.0a1 (minor alpha)
    releaser.add_change("minor", "a1", pre="alpha")
    res = releaser.release()
    assert res.version == "0.1.0a1"

    # Step 2: 0.1.0a1 -> 0.1.0a2 (minor alpha)
    releaser.add_change("minor", "a2", pre="alpha")
    res = releaser.release()
    assert res.version == "0.1.0a2"

    # Step 3: 0.1.0a2 -> 0.1.0b1 (minor beta)
    releaser.add_change("minor", "b1", pre="beta")
    res = releaser.release()
    assert res.version == "0.1.0b1"

    # Step 4: 0.1.0b1 -> 0.1.0rc1 (minor rc)
    releaser.add_change("minor", "rc1", pre="rc")
    res = releaser.release()
    assert res.version == "0.1.0rc1"

    # Step 5: 0.1.0rc1 -> 0.1.0 (minor stable)
    releaser.add_change("minor", "stable")
    res = releaser.release()
    assert res.version == "0.1.0"

    # Step 6: 0.1.0 -> 1.0.0a1 (major alpha)
    releaser.add_change("major", "maj a1", pre="alpha")
    res = releaser.release()
    assert res.version == "1.0.0a1"
