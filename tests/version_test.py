import pytest

from semversioner.version import SemVersion, SemVersionError


def test_parse() -> None:
    assert SemVersion("1.2.3").major == 1
    assert SemVersion("1.2.3").minor == 2
    assert SemVersion("1.2.3").micro == 3
    assert SemVersion("1.2.3").pre is None
    assert SemVersion("1.2.3rc4").pre == ("rc", 4)
    assert SemVersion("1.2.3.alpha4").pre == ("a", 4)
    assert SemVersion("1.2.3.alpha").pre == ("a", 0)
    assert SemVersion("1.2.3-rc4").pre == ("rc", 4)
    assert SemVersion("1.2.3-dev5").is_devrelease
    assert SemVersion("1.2.3").is_stable
    assert not SemVersion("1.2.3").is_devrelease
    assert SemVersion("1.2.3.post3").is_stable
    assert SemVersion("1.2.3.post3").is_postrelease
    assert SemVersion("1.2.3.post3").to_string() == "1.2.3.post3"
    assert SemVersion("1.2.3.alpha2").to_string() == "1.2.3a2"
    assert SemVersion("1.2.3.alpha").to_string() == "1.2.3a0"

    with pytest.raises(SemVersionError):
        SemVersion("invalid")


def test_next_version() -> None:
    params_list = [
        ("1.0.0", ("minor",), "1.1.0"),
        ("1.0.0", ("major",), "2.0.0"),
        ("1.0.0", ("patch",), "1.0.1"),
        ("0.1.1", ("minor",), "0.2.0"),
        ("0.1.1", ("major",), "1.0.0"),
        ("0.1.1", ("patch",), "0.1.2"),
        ("9.9.9", ("minor",), "9.10.0"),
        ("9.9.9", ("major",), "10.0.0"),
        ("9.9.9", ("patch",), "9.9.10"),
        ("2.0.0-alpha.1", ("patch",), "2.0.0"),
        ("2.0.0-alpha.1", ("minor",), "2.0.0"),
        ("2.0.0-alpha.1", ("major",), "2.0.0"),
        ("2.1.0-alpha.1", ("patch",), "2.1.0"),
        ("2.1.0-alpha.1", ("minor",), "2.1.0"),
        ("2.1.0-alpha.1", ("major",), "3.0.0"),
        ("2.1.1-alpha.1", ("patch",), "2.1.1"),
        ("2.1.1-alpha.1", ("minor",), "2.2.0"),
        ("2.1.1-alpha.1", ("major",), "3.0.0"),
        # Pre-release
        ("1.0.0", ("minor", "alpha"), "1.1.0a1"),
        ("1.0.0", ("major", "alpha"), "2.0.0a1"),
        ("1.0.0", ("patch", "alpha"), "1.0.1a1"),
        ("0.1.1", ("minor", "alpha"), "0.2.0a1"),
        ("0.1.1", ("major", "alpha"), "1.0.0a1"),
        ("0.1.1", ("patch", "alpha"), "0.1.2a1"),
        ("9.9.9", ("minor", "alpha"), "9.10.0a1"),
        ("9.9.9", ("major", "alpha"), "10.0.0a1"),
        ("9.9.9", ("patch", "alpha"), "9.9.10a1"),
        ("2.0.0-alpha.1", ("patch", "alpha"), "2.0.0a2"),
        ("2.0.0-alpha.1", ("minor", "alpha"), "2.0.0a2"),
        ("2.0.0-alpha.1", ("major", "alpha"), "2.0.0a2"),
        ("2.1.0-alpha.1", ("patch", "beta"), "2.1.0b1"),
        ("2.1.0-alpha.1", ("minor", "beta"), "2.1.0b1"),
        ("2.1.1-alpha1", ("patch", "rc"), "2.1.1rc1"),
    ]

    for p1, p2, p3 in params_list:
        assert SemVersion(p1).next_version(*p2) == SemVersion(p3)


def test_comparison() -> None:
    assert SemVersion("1.2.32") > SemVersion("1.2.5")
    assert SemVersion("1.2.3") > SemVersion("1.2.3.rc3")
    assert SemVersion("1.2.3.rc3") > SemVersion("1.2.3.rc2")
    assert SemVersion("1.2.3rc3") == SemVersion("1.2.3.rc3")
    assert SemVersion("1.2.3alpha3") == SemVersion("1.2.3a3")
    assert SemVersion("1.2.3.rc3") < SemVersion("1.2.3.rc4")
    assert SemVersion("1.2.3.rc3") < SemVersion("1.2.3")
    assert SemVersion("1.2.3.dev3") < SemVersion("1.2.3a1")
    assert SemVersion("1.2.3.post3") > SemVersion("1.2.3")


def test_bump_prerelease() -> None:
    assert SemVersion("1.2.3")._bump_prerelease("patch", "rc").to_string() == "1.2.4rc1"
    assert SemVersion("1.2.3alpha")._bump_prerelease("patch", "alpha").to_string() == "1.2.3a1"
    assert SemVersion("1.2.3rc4")._bump_prerelease("patch", "rc").to_string() == "1.2.3rc5"
    assert SemVersion("1.2.3")._bump_prerelease("minor", "alpha").to_string() == "1.3.0a1"
    assert SemVersion("1.2.3")._bump_prerelease("major", "alpha").to_string() == "2.0.0a1"
    assert SemVersion("1.2.3a3")._bump_prerelease("patch", "alpha").to_string() == "1.2.3a4"
    assert SemVersion("1.2.3a3")._bump_prerelease("major", "rc").to_string() == "1.2.3rc1"


def test_get_stable() -> None:
    assert SemVersion("1.2.3").get_stable().to_string() == "1.2.3"
    assert SemVersion("2.1.0a2").get_stable().to_string() == "2.1.0"
    assert SemVersion("1.2.5.post3").get_stable().to_string() == "1.2.5"


def test_prerelease_type() -> None:
    assert SemVersion("1.2.3").prerelease_type is None
    assert SemVersion("1.2.3rc1").prerelease_type == "rc"
    assert SemVersion("1.2.3a2").prerelease_type == "alpha"
    assert SemVersion("1.2.3b3").prerelease_type == "beta"
    assert SemVersion("1.2.3.dev1").prerelease_type is None


def test_from_string_and_clone() -> None:
    assert SemVersion.from_string("1.2.3").to_string() == "1.2.3"
    assert SemVersion("1.2.3").clone().to_string() == "1.2.3"


def test_from_params_all() -> None:
    assert SemVersion.from_params(epoch=1, release=(1, 2, 3)).to_string() == "1!1.2.3"
    assert SemVersion.from_params(epoch=0, release=(1, 2, 3), post=("post", 4)).to_string() == "1.2.3.post4"
    assert SemVersion.from_params(epoch=0, release=(1, 2, 3), dev=("dev", 5)).to_string() == "1.2.3.dev5"
    assert SemVersion.from_params(epoch=0, release=(1, 2, 3), local=("local", 6)).to_string() == "1.2.3+local.6"
