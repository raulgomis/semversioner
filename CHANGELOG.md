# Changelog
Note: version releases in the 0.x.y range may introduce breaking changes.

## 2.0.6

- patch: Bump jinja2 from 3.1.4 to 3.1.6.

## 2.0.5

- patch: move main logic into __main__.py

## 2.0.4

- patch: Include CHANGELOG.md into package.

## 2.0.3

- patch: Bump jinja2 from 3.1.3 to 3.1.4 to patch CVE-2024-34064.

## 2.0.2

- patch: Bump jinja2 from 3.1.2 to 3.1.3 to fix CVE-2024-22195.

## 2.0.1

- patch: Add documentation for custom attributes in the changelog template.

## 2.0.0

- major: Drop support for Python 3.6 and 3.7 as they are not maintained. Minimum supported version is Python 3.8.
- major: Upgrade project third-party dependencies to latest version.
- minor: Add support for custom properties in changeset files.
- minor: Change deletion logic in `next-release` folder: only delete json files, and delete the folder only if empty. This will allow to keep the `next-release` folder if it contains other files such as `.gitkeep` for example.
- minor: Change json mapper to use granurality of seconds instead of milliseconds for `created_at` field in releases.
- patch: Clean up README Markdown syntax.

## 1.7.0

- minor: Validated JSON extension in the  folder.
- patch: Upgraded development libraries to latest version.

## 1.6.0

- minor: Decreased packaging minimum version requirements to version 21.0

## 1.5.2

- patch: Internal: improve CI/CD workflow

## 1.5.1

- patch: Fix install packaging module to fix module issues.

## 1.5.0

- minor: Fix remove StrictVersion deprecation notice by switching to package.version parse method.
- patch: Internal: Support python 3.11 in Github actions.

## 1.4.1

- patch: Fixed CVE-2022-40898 in pypa/wheel (development library).
- patch: Update development dependencies to the latest version.

## 1.4.0

- minor: Add support for storing release datetime in order to display it in the changelog.
- patch: All tests are now able to be run on Windows
- patch: Fix: bug showing incorrect error using release command with no changesets created.

## 1.3.0

- minor: Add CLI command to detect missing changeset files before merging to the destination branch.
- minor: Add exception handling support to use Semversioner as a library.
- patch: Fix next-version error command color.

## 1.2.0

- minor: Added command next-version, to compute the version of the next release, without actually performing the release

## 1.1.0

- minor: Expose models to use semversioner as a library.
- minor: Use models for better encapsulation and code refactoring.

## 1.0.0

- major: Drop support for Python 3.6.
- minor: Add type hinting.
- minor: Bump click dependency to 8.0.3.
- minor: Bump jinja2 dependency to 3.0.3.
- patch: Add Python 3.10 testing in the CI/CD process.
- patch: Bump importlib_resources dependency to 5.4.0.
- patch: Bump pytest dependency to 6.2.5.
- patch: Bump twine dependency to 3.7.1.
- patch: Bump wheel dependency to 0.37.0.
- patch: Remove unnecessary dependency: colorama.
- patch: Rename semversioner directory to .semversioner.

## 0.13.0

- minor: Add support for custom changelog template
- patch: Fix security vulnerability with jinja2 CVE-2020-28493

## 0.12.0

- minor: Improved performance by supporting multiple changeset files per second
- minor: Status command now sorts unreleased changes by type and description in order to display consistent results
- patch: Internal code refactor to improve code readability and maintanability

## 0.11.0

- minor: Add '--version' filter to the 'changelog' command to display the changelog only for a specific version

## 0.10.0

- minor: Add new 'status' command to display the state of the working directory and unreleased changes
- patch: Fix build and deployment configuration
- patch: Refactor method names and code for better code readability and testability

## 0.9.0

- minor: Deprecated .changes directory in favour of .semversioner directory
- patch: Internal refactor to improve code quality and test coverage

## 0.8.1

- patch: Fix installer error when referencing to LICENSE file

## 0.8.0

- minor: Enabled autocompletion by default

## 0.7.1

- patch: Improve docs for open source

## 0.7.0

- minor: Fail with error code when no changes are provided in the release command

## 0.6.16

- patch: Fix bug: add require module in setup.py

## 0.6.15

- patch: Fix packaging for LICENSE
- patch: Improve README.md documentation
- patch: Use jinja2 template engine internally to generate the changelog

## 0.6.14

- patch: Update docs

## 0.6.13

- patch: Fix README.md

## 0.6.12

- patch: Fix long description content type

## 0.6.11

- patch: Add README.md file

## 0.6.10

- patch: Fix code consistency

## 0.6.9

- patch: Fix packaging

## 0.6.8

- patch: Tag the repository when releasing

## 0.6.7

- patch: Fix tests and improve coverage

## 0.6.6

- minor: Initial version
