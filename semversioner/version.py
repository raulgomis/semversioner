from typing import Literal, Optional, TypeVar

from semversioner.models import ReleaseType
from packaging.version import Version, _Version as BaseVersion, InvalidVersion

_T = TypeVar("_T", bound="SemVersion")


class SemVersionError(InvalidVersion):
    pass


class SemVersion(Version):
    def __init__(self, version: str) -> None:
        try:
            super().__init__(version)
        except InvalidVersion as e:
            raise SemVersionError(e)

    @staticmethod
    def from_string(version: str) -> _T:
        """
        Returns a new version from a string.

        Parameters
        ----------
        version : str
            Version string.

        Returns
        -------
        SemVersion
            New version.
        """
        return SemVersion(version)

    @staticmethod
    def from_params(
        epoch,
        release,
        dev,
        pre,
        post,
        local
    ) -> _T:
        """
        Returns a new version from the parameters.
        """
        version = SemVersion('0.0.0')

        version._version = BaseVersion(
            epoch=epoch,
            release=release,
            dev=dev,
            pre=pre,
            post=post,
            local=local
        )
        return version.clone()

    def to_string(self) -> str:
        """
        Returns the string representation of the version.
        """
        return str(self)

    def clone(self: _T) -> _T:
        """
        Returns a clone of the version.
        """
        return self.__class__(self.to_string())

    def get_stable(self: _T) -> _T:
        return SemVersion.from_params(
            epoch=0,
            release=(self.major, self.minor, self.micro),
            pre=None,
            post=None,
            dev=None,
            local=None,
        )

    @property
    def is_stable(self) -> bool:
        return not self.is_prerelease

    @property
    def prerelease_type(self) -> Optional[Literal["rc", "alpha", "beta"]]:
        if not self.pre:
            return None

        letter = self.pre[0]
        if letter == "rc":
            return "rc"
        if letter == "a":
            return "alpha"
        if letter == "b":
            return "beta"

        return None

    def _bump_stable_release(
        self,
        release_type: Literal["major", "minor", "patch"]
    ) -> _T:
        """
        Bump the release self.
        """
        version_parts = [self.major, self.minor, self.micro]

        if release_type == ReleaseType.MAJOR.value:
            if self.is_prerelease and self.micro == 0 and self.minor == 0:
                version_parts = [self.major, self.minor, self.micro]
            else:
                version_parts = [self.major + 1, 0, 0]
        elif release_type == ReleaseType.MINOR.value:
            if self.is_prerelease and self.micro == 0:
                version_parts = [self.major, self.minor, self.micro]
            else:
                version_parts = [self.major, self.minor + 1, 0]
        elif release_type == ReleaseType.PATCH.value:
            if self.is_prerelease:
                version_parts = [self.major, self.minor, self.micro]
            else:
                version_parts = [self.major, self.minor, self.micro + 1]

        return SemVersion('.'.join(str(i) for i in version_parts))

    def _bump_prerelease(
        self,
        release_type: Literal["major", "minor", "patch"], 
        prerelease_type: Literal["rc", "alpha", "beta", "a", "b"] = "rc"
    ) -> _T:
        """
        Bump the prerelease version.
        """

        inc = 1 if not self.is_prerelease else (max(1, self.pre[-1]) + 1)

        ptype = prerelease_type or self.prerelease_type or "rc"

        pre = (ptype, inc)

        new_version = SemVersion.from_params(
            epoch=self.epoch,
            release=self.release,
            pre=pre,
            post=self.post,
            dev=self.dev,
            local=self.local
        )

        if new_version < self:
            ptype = prerelease_type or "rc"
            new_version = self._bump_stable_release(release_type)

        if prerelease_type != self.prerelease_type:
            inc = 1

        return SemVersion.from_params(
            epoch=0,
            release=new_version.release,
            pre=(ptype, inc),
            post=None,
            dev=None,
            local=None,
        )

    def next_version(
        self, 
        release_type: Literal["major", "minor", "patch"], 
        prerelease_type: Optional[Literal["rc", "alpha", "beta"]] = None
    ) -> _T:
        """
        Returns the next version.

        Parameters
        ----------
        release_type : Literal["major", "minor", "patch"]
            Type of release.
        prerelease_type : Optional[Literal["rc", "alpha", "beta"]]
            Type of prerelease.

        Returns
        -------
        SemVersion
            Next version.

        Examples:

            ```python 
            SemVersion('1.0.0').next_version('major') # '2.0.0'
            SemVersion('1.0.0').next_version('minor') # '1.1.0'
            SemVersion('1.0.0').next_version('patch') # '1.0.1'
            SemVersion('2.0.0-alpha.1').next_version('major') # '2.0.0'
            SemVersion('2.0.0-alpha.1').next_version('minor') # '2.0.0'
            SemVersion('2.0.0-alpha.1').next_version('patch') # '2.0.0'
            SemVersion('1.0.0').next_version('major', 'alpha') # '2.0.0-alpha.1'
            SemVersion('1.0.0').next_version('minor', 'alpha') # '1.1.0-alpha.1'
            SemVersion('2.0.0-alpha.1').next_version('major', 'alpha') # '2.0.0-alpha.2'
            SemVersion('2.0.0-alpha.1').next_version('major', 'beta') # '2.0.0-beta.1'
            ```
        """

        if prerelease_type:
            new_version = self._bump_prerelease(release_type, prerelease_type)
        else:
            new_version = self._bump_stable_release(release_type)

        return new_version
