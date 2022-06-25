import unittest

import pytest

from semversioner.version import SemVersion, SemVersionError


class VersionTestCase(unittest.TestCase):

    def test_parse(self) -> None:
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

    def test_next_version(self) -> None:

        params_list = [
            ("1.0.0", ("minor", ), "1.1.0"),
            ("1.0.0", ("major", ), "2.0.0"),
            ("1.0.0", ("patch", ), "1.0.1"),
            ("0.1.1", ("minor", ), "0.2.0"),
            ("0.1.1", ("major", ), "1.0.0"),
            ("0.1.1", ("patch", ), "0.1.2"),
            ("9.9.9", ("minor", ), "9.10.0"),
            ("9.9.9", ("major", ), "10.0.0"),
            ("9.9.9", ("patch", ), "9.9.10"),
            ("2.0.0-alpha.1", ("patch", ), "2.0.0"),
            ("2.0.0-alpha.1", ("minor", ), "2.0.0"),
            ("2.0.0-alpha.1", ("major", ), "2.0.0"),
            ("2.1.0-alpha.1", ("patch", ), "2.1.0"),
            ("2.1.0-alpha.1", ("minor", ), "2.1.0"),
            ("2.1.0-alpha.1", ("major", ), "3.0.0"),  # weird case (should we fail?)
            ("2.1.1-alpha.1", ("patch", ), "2.1.1"),
            ("2.1.1-alpha.1", ("minor", ), "2.2.0"),  # weird case (should we fail?)
            ("2.1.1-alpha.1", ("major", ), "3.0.0"),  # weird case (should we fail?)
            # Pre-release
            ("1.0.0", ("minor", "alpha"), "1.1.0alpha1"),
            ("1.0.0", ("major", "alpha"), "2.0.0alpha1"),
            ("1.0.0", ("patch", "alpha"), "1.0.1alpha1"),
            ("0.1.1", ("minor", "alpha"), "0.2.0alpha1"),
            ("0.1.1", ("major", "alpha"), "1.0.0alpha1"),
            ("0.1.1", ("patch", "alpha"), "0.1.2alpha1"),
            ("9.9.9", ("minor", "alpha"), "9.10.0alpha1"),
            ("9.9.9", ("major", "alpha"), "10.0.0alpha1"),
            ("9.9.9", ("patch", "alpha"), "9.9.10alpha1"),
            ("2.0.0-alpha.1", ("patch", "alpha"), "2.0.0alpha2"),
            ("2.0.0-alpha.1", ("minor", "alpha"), "2.0.0alpha2"),
            ("2.0.0-alpha.1", ("major", "alpha"), "2.0.0alpha2"),
            ("2.1.0-alpha.1", ("patch", "beta"), "2.1.0beta1"),
            ("2.1.0-alpha.1", ("minor", "beta"), "2.1.0beta1"),
            # ("2.1.0-alpha.1", ("major", "beta"), "3.0.0beta1"),  # weird case (should we fail?)
            ("2.1.1-alpha1", ("patch", "rc"), "2.1.1rc1"),
            # ("2.1.1-alpha.1", ("minor", "rc"), "2.2.0rc1"),  # weird case (should we fail?)
            # ("2.1.1-alpha.1", ("major", "rc"), "3.0.0rc1")  # weird case (should we fail?)
        ]

        for p1, p2, p3 in params_list:
            with self.subTest():
                self.assertEqual(SemVersion(p1).next_version(*p2), SemVersion(p3))

    def test_comparison(self):
        assert SemVersion("1.2.32") > SemVersion("1.2.5")
        assert SemVersion("1.2.3") > SemVersion("1.2.3.rc3")
        assert SemVersion("1.2.3.rc3") > SemVersion("1.2.3.rc2")
        assert SemVersion("1.2.3rc3") == SemVersion("1.2.3.rc3")
        assert SemVersion("1.2.3alpha3") == SemVersion("1.2.3a3")
        assert SemVersion("1.2.3.rc3") < SemVersion("1.2.3.rc4")
        assert SemVersion("1.2.3.rc3") < SemVersion("1.2.3")
        assert SemVersion("1.2.3.dev3") < SemVersion("1.2.3a1")
        assert SemVersion("1.2.3.post3") > SemVersion("1.2.3")

    def test_bump_prerelease(self):
        assert SemVersion("1.2.3")._bump_prerelease("patch", "rc").to_string() == "1.2.4rc1"
        assert SemVersion("1.2.3alpha")._bump_prerelease("patch", "alpha").to_string() == "1.2.3a2"
        assert SemVersion("1.2.3rc4")._bump_prerelease("patch", "rc").to_string() == "1.2.3rc5"
        # assert SemVersion("1.2.3rc4")._bump_prerelease("patch", "alpha").to_string() == "1.2.4a0"  # weird case
        assert SemVersion("1.2.3")._bump_prerelease("minor", "alpha").to_string() == "1.3.0a1"
        assert SemVersion("1.2.3")._bump_prerelease("major", "alpha").to_string() == "2.0.0a1"
        assert SemVersion("1.2.3a3")._bump_prerelease("patch", "alpha").to_string() == "1.2.3a4"
        assert SemVersion("1.2.3a3")._bump_prerelease("major", "rc").to_string() == "1.2.3rc1"

    def test_get_stable(self):
        assert SemVersion("1.2.3").get_stable().to_string() == "1.2.3"
        assert SemVersion("2.1.0a2").get_stable().to_string() == "2.1.0"
        assert SemVersion("1.2.5.post3").get_stable().to_string() == "1.2.5"
