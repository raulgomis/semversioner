
CHANGELOG_1 = """# Changelog
Note: version releases in the 0.x.y range may introduce breaking changes.

## 1.0.0

- major: This is my major description
"""

CHANGELOG_2 = """# Changelog
Note: version releases in the 0.x.y range may introduce breaking changes.

## 0.0.1

- patch: This is my patch description
"""

CHANGELOG_3 = """# Changelog
Note: version releases in the 0.x.y range may introduce breaking changes.

## 2.1.0

- minor: This is my minor description

## 2.0.0

- major: This is my major description

## 1.0.0

- major: This is my major description

## 0.0.1

- patch: This is my patch description
"""

CHANGELOG_4 = """# Changelog
Note: version releases in the 0.x.y range may introduce breaking changes.

## 2.0.0

- major: This is my major description
- minor: This is my minor description
- patch: This is my patch description

## 1.0.0

- major: This is my major description
- minor: This is my minor description
- patch: This is my patch description
"""

# Existing Data Fixtures

VERSION_0_1_0 = """[
  {
    "description": "Initial version",
    "type": "minor"
  }
]"""

VERSION_0_2_0 = """[
  {
    "description": "Second version",
    "type": "minor"
  }
]"""

CHANGELOG_5 = """# Changelog
Note: version releases in the 0.x.y range may introduce breaking changes.

## 0.2.0

- minor: Second version

## 0.1.0

- minor: Initial version
"""

CHANGELOG_6 = """# Changelog
Note: version releases in the 0.x.y range may introduce breaking changes.

## 0.2.1

- patch: This is my patch description

## 0.2.0

- minor: Second version

## 0.1.0

- minor: Initial version
"""


TEST_STATUS_COMMAND_WITH_NO_CHANGES = """Version: 0.0.0
No changes to release (use "semversioner add-change")
"""

TEST_STATUS_COMMAND_WITH_RELEASED_CHANGES = """Version: 0.1.0
No changes to release (use "semversioner add-change")
"""

TEST_STATUS_COMMAND_WITH_UNRELEASED_CHANGES = """Version: 0.0.0
Next version: 0.1.0
Unreleased changes:
\tminor:\tThis is my minor description
(use "semversioner release" to release the next version)
"""
