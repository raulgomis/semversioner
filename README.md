# Semversioner

The easiest way to manage [semantic versioning](https://semver.org/) in your project and generate `CHANGELOG.md` files automatically.

Semversioner provides the tooling to automate the semver release process for libraries, docker images, microservices, and more.

This project was inspired by the way AWS manages their versioning for [AWS-cli](https://github.com/aws/aws-cli/).

[![PyPI Version](https://img.shields.io/pypi/v/semversioner.svg)](https://pypi.org/project/semversioner/)

## Semantic Versioning

The [semantic versioning](https://semver.org/) spec involves several possible variations, but to simplify, in _Semversioner_ we are using the three-part version number:

`<major>.<minor>.<patch>`

Constructed with the following guidelines:

- Breaking backward compatibility or major features bumps the **major** (and resets the minor and patch).
- New additions without breaking backward compatibility bumps the **minor** (and resets the patch).
- Bug fixes and misc changes bumps the **patch**.

An example would be `1.0.0`.

## How it works

At any given time, the `.semversioner/` directory looks like:

```text
.semversioner
├── next-release
│   ├── minor-20181227010225.json
│   └── major-20181228010225.json
├── 1.1.0.json
├── 1.1.1.json
└── 1.1.2.json
```

The release process takes everything in the `next-release` directory and aggregates them all together in a single JSON file for that release (e.g., `1.12.0.json`). This JSON file is a list of all the individual JSON files from `next-release`.

## Install

```shell
pip install semversioner
```

## Usage

You can use the `--help` option on any command to see the available options:

```shell
semversioner --help
```

### Adding changesets

In your local environment, you can use the CLI to create the different changeset files that will be committed with your code. This ensures that every pull request or commit contains its own self-contained change description and version bump intention.

```shell
semversioner add-change --type patch --description "Fix security vulnerability with authentication."
```

Allowed `--type` values are: `major`, `minor`, `patch`.

You can also add custom attributes to the changeset file that will be available later in your release template. Use the `--attributes` flag in `key=value` format (you can pass it multiple times):

```shell
semversioner add-change --type patch \
    --description "My custom changelog message with attributes." \
    --attributes pr_id=322 \
    --attributes issue_id=123
```

### Checking working directory status

You can check the status of your working directory to see the current version, the computed next version, and any unreleased changes:

```shell
semversioner status
```

Example output:

```text
Version: 1.0.0
Next version: 1.1.0
Unreleased changes:
	minor:	Added new authentication feature
(use "semversioner release" to release the next version)
```

### Enforcing changesets in CI/CD (Check)

In your CI/CD pipeline, it's often useful to enforce that a PR includes a changeset before merging. You can use the `check` command to verify that there are unreleased changes in the `.semversioner/next-release/` directory.

```shell
semversioner check
```

If no changes are found, the command exits with a non-zero status code (`-1`) and prints an error message.

### Releasing a new version

When you are ready to create a release (usually in your CI/CD tool on the main branch), you run the `release` command. This automatically computes the new version number based on the unreleased changes, generates a new version JSON file, and clears the `next-release` directory.

```shell
semversioner release
```

### Generating the Changelog

As part of your release workflow, you can generate the changelog file with all aggregated changes.

```shell
semversioner changelog > CHANGELOG.md
```

#### Customizing the changelog template

You can customize the changelog by creating a template and passing it as a parameter to the command. For example:

```shell
semversioner changelog --template .semversioner/config/template.j2
```

The template uses [Jinja2](https://jinja.palletsprojects.com/en/3.1.x/), a templating language for Python. A basic example:

```jinja2
# Changelog
{% for release in releases %}

## {{ release.version }}

{% for change in release.changes %}
- {{ change.type }}: {{ change.description }}
{% endfor %}
{% endfor %}
```

If you included custom attributes (e.g., `pr_id`, `issue_id`) using the `add-change` command, you can reference them in your template. You also have access to `current_version`:

```jinja2
# Changelog
Note: version releases in the 0.x.y range may introduce breaking changes.

# Current version: {{ current_version }}

{% for release in releases %}

## {{ release.version }}{{ ' (' + release.created_at.strftime('%Y-%m-%d') + ')' if release.created_at }}

{% for change in release.changes %}
- {{ change.type }}: {{ change.description }}{{ ' (#' + change.attributes.pr_id + ')' if change.attributes }}{{ ' (J' + change.attributes.issue_id + ')' if change.attributes }}
{% endfor %}
{% endfor %}
```

#### Filtering the changelog

You can filter the changelog by only showing changes for a specific version:

```shell
semversioner changelog --version "1.0.0"
```

Alternatively, you can filter changes for the last released version:

```shell
semversioner changelog --version $(semversioner current-version)
```

### Getting the current version

You can retrieve the currently released version of your project:

```shell
semversioner current-version
```

### Getting the next version

As part of the CI/CD workflow, sometimes you want to release dev, rc, or other pre-release packages. For this purpose, the `next-version` command can be issued to compute the upcoming version based on the current changeset. This will not modify any files on disk.

```shell
semversioner next-version
```

## Global Options

- `--path`: Specify a custom base path for your project. Defaults to the current directory. Example: `semversioner --path /path/to/project release`

## License

Copyright (c) 2026 Raul Gomis.
MIT licensed, see [LICENSE](LICENSE) file.

---
Made with ♥ by [Raul Gomis](https://twitter.com/rgomis).
