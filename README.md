# Semversioner
The easiest way to manage [semantic versioning](https://semver.org/) in your project and generate CHANGELOG.md file automatically. 

Semversioner will provide the tooling to automate semver release process for libraries, docker images, etc. 

This project was inspired by the way AWS manages their versioning for [AWS-cli](https://github.com/aws/aws-cli/).

## Semantic Versioning
The [semantic versioning](https://semver.org/) spec involves several possible variations, but to simplify, in _Semversioner_ we are using the three-part version number:

`<major>.<minor>.<patch>`

Constructed with the following guidelines:
- Breaking backward compatibility or major features bumps the major (and resets the minor and patch).
- New additions without breaking backward compatibility bumps the minor (and resets the patch).
- Bug fixes and misc changes bumps the patch.

An example would be 1.0.0

## How it works

At any given time, the ``.semversioner/`` directory looks like:

    .semversioner
    └── next-release
        ├── minor-20181227010225.json
        └── major-20181228010225.json
    ├── 1.1.0.json
    ├── 1.1.1.json
    ├── 1.1.2.json

The release process takes everything in ``next-release`` and aggregates them all together in a single JSON file for that release (e.g ``1.12.0.json``).  This
JSON file is a list of all the individual JSON files from ``next-release``.

## Install

```shell
$ pip install semversioner
```

## Usage

### Bumping the version

In your local environment your will use the CLI to create the different changeset files that will be committed with your code. For example:
```shell
$ semversioner add-change --type patch --description "Fix security vulnerability with authentication."
```

Then, in your CI/CD tool you will need to release (generating automatically version number) and creating the the changelog file. 
```shell
$ semversioner release
```

### Generating Changelog

As a part of your CI/CD workflow, you will be able to generate the Changelog file with all changes.

```shell
$ semversioner changelog > CHANGELOG.md
```

## License
Copyright (c) 2020 Raul Gomis.
MIT licensed, see [LICENSE](LICENSE) file.

---
Made with ♥ by `Raul Gomis <https://twitter.com/rgomis>`.
