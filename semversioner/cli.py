#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Semversioner allows you to manage semantic versioning properly and simplifies changelog generation. 

This project was inspired by the way AWS manages their versioning for AWS-CLI: https://github.com/aws/aws-cli/

At any given time, the ``.semversioner/`` directory looks like:
    .semversioner
    |
    └── next-release
        ├── minor-20181227010225.json
        └── major-20181228010225.json
    ├── 1.1.0.json
    ├── 1.1.1.json
    ├── 1.1.2.json

This script takes everything in ``next-release`` and aggregates them all together in a single JSON file for that release (e.g ``1.12.0.json``).  This
JSON file is a list of all the individual JSON files from ``next-release``.

This is done to simplify changelog generation.

Usage
=====
::
    $ semversioner add-change --type major --description "This description will appear in the change log"
    $ semversioner release
    $ semversioner changelog > CHANGELOG.md
"""

import os
import click
from semversioner import __version__
from semversioner.core import Semversioner

ROOTDIR = os.getcwd()


@click.group()
@click.option('--path', default=ROOTDIR, help="Base path. Default to current directory.")
@click.version_option(version=str(__version__.__version__))
@click.pass_context
def cli(ctx, path):
    ctx.obj = {
        'releaser': Semversioner(path=path)
    }


@cli.command('release', help="Release a new version.")
@click.pass_context
def cli_release(ctx):
    releaser = ctx.obj['releaser']
    if releaser.is_deprecated():
        click.secho("WARN", bg='yellow', fg='black', nl=False)
        click.secho(" deprecated ", fg='magenta', nl=False)
        click.echo("Semversioner now uses '.semversioner' directory instead of '.changes'. Please, rename it to remove this message.")
    result = releaser.release()
    click.echo(message="Successfully created new release: " + result['new_version'])


@cli.command('changelog', help="Print the changelog.")
@click.pass_context
def cli_changelog(ctx):
    releaser = ctx.obj['releaser']
    changelog = releaser.generate_changelog()
    click.echo(message=changelog, nl=False)


@cli.command('add-change', help="Create a new changeset file.")
@click.pass_context
@click.option('--type', '-t', type=click.Choice(['major', 'minor', 'patch']), required=True)
@click.option('--description', '-d', required=True)
def cli_add_change(ctx, type, description):
    releaser = ctx.obj['releaser']
    result = releaser.add_change(type, description)
    click.echo(message="Successfully created file " + result['path'])


@cli.command('current-version', help="Show the current version.")
@click.pass_context
def cli_current_version(ctx):
    releaser = ctx.obj['releaser']
    version = releaser.get_version()
    click.echo(message=version)


def main():
    cli(obj={})


if __name__ == '__main__':
    main()
