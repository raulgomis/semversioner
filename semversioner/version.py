from packaging.version import InvalidVersion, Version


class SemVersionError(InvalidVersion):
    pass


class SemVersion(Version):
    def __init__(self, version: str) -> None:
        try:
            super().__init__(version)
        except InvalidVersion as e:
            raise SemVersionError(str(e)) from e

    @classmethod
    def from_string(cls, version: str) -> "SemVersion":
        return cls(version)

    @classmethod
    def from_params(
        cls,
        epoch: int,
        release: tuple[int, ...],
        dev: tuple[str, int] | None = None,
        pre: tuple[str, int] | None = None,
        post: tuple[str, int] | None = None,
        local: tuple[str, ...] | None = None,
    ) -> "SemVersion":
        parts = []
        if epoch != 0:
            parts.append(f"{epoch}!")
        parts.append(".".join(str(i) for i in release))
        if pre:
            parts.append(f"{pre[0]}{pre[1]}")
        if post:
            parts.append(f".post{post[1]}")
        if dev:
            parts.append(f".dev{dev[1]}")
        if local:
            parts.append("+" + ".".join(str(i) for i in local))
        return cls("".join(parts))

    def to_string(self) -> str:
        return str(self)

    def clone(self) -> "SemVersion":
        return self.__class__(self.to_string())

    def get_stable(self) -> "SemVersion":
        return self.from_params(
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
    def prerelease_type(self) -> str | None:
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

    def _bump_stable_release(self, release_type: str) -> "SemVersion":
        version_parts = [self.major, self.minor, self.micro]

        if release_type == "major":
            if self.is_prerelease and self.micro == 0 and self.minor == 0:
                version_parts = [self.major, self.minor, self.micro]
            else:
                version_parts = [self.major + 1, 0, 0]
        elif release_type == "minor":
            if self.is_prerelease and self.micro == 0:
                version_parts = [self.major, self.minor, self.micro]
            else:
                version_parts = [self.major, self.minor + 1, 0]
        elif release_type == "patch":
            if self.is_prerelease:
                version_parts = [self.major, self.minor, self.micro]
            else:
                version_parts = [self.major, self.minor, self.micro + 1]

        return self.__class__(".".join(str(i) for i in version_parts))

    def _bump_prerelease(self, release_type: str, prerelease_type: str = "rc") -> "SemVersion":
        ptype = prerelease_type
        if ptype == "alpha":
            ptype = "a"
        elif ptype == "beta":
            ptype = "b"

        # Determine initial prerelease increment
        inc = self.pre[1] + 1 if self.is_prerelease and self.pre and self.pre[0] == ptype else 1

        candidate = self.from_params(
            epoch=self.epoch,
            release=self.release,
            pre=(ptype, inc),
            post=self.post,
            dev=self.dev,
            local=self.local,
        )

        if candidate <= self:
            stable_version = self.get_stable()
            new_stable = stable_version._bump_stable_release(release_type)
            return self.from_params(
                epoch=self.epoch,
                release=new_stable.release,
                pre=(ptype, 1),
                post=self.post,
                dev=self.dev,
                local=self.local,
            )

        return candidate

    def next_version(self, release_type: str, prerelease_type: str | None = None) -> "SemVersion":
        if prerelease_type:
            return self._bump_prerelease(release_type, prerelease_type)
        return self._bump_stable_release(release_type)
