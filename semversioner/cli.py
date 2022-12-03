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
    $ semversioner next-version
"""

import os
import sys
from typing import Optional, TextIO

import click

from semversioner import __version__
from semversioner.core import Semversioner
from semversioner.models import (MissingChangesetException, Release, ReleaseStatus)

ROOTDIR = os.getcwd()


@click.group()
@click.option('--path', default=ROOTDIR, help="Base path. Default to current directory.", type=click.Path(exists=True))
@click.version_option(version=str(__version__.__version__))
@click.pass_context
def cli(ctx: click.Context, path: str) -> None:
    ctx.obj = {
        'releaser': Semversioner(path=path)
    }


@cli.command('release', help="Release a new version.")
@click.pass_context
def cli_release(ctx: click.Context) -> None:
    releaser: Semversioner = ctx.obj['releaser']
    if releaser.is_deprecated():
        click.secho("WARN", bg='yellow', fg='black', nl=False)
        click.secho(" deprecated ", fg='magenta', nl=False)
        click.echo("Semversioner now uses '.semversioner' directory instead of '.changes'. Please, rename it to remove this message.")
    try:
        result: Release = releaser.release()
        click.echo(message="Successfully created new release: " + result.version)
    except MissingChangesetException:
        click.secho("Error: No changes to release. Skipping release process.", fg='red')


@cli.command('changelog', help="Print the changelog.")
@click.option('--version', default=None, help="Filter the changelog by version.")
@click.option('--template', default=None, help="Path to a custom changelog template.", type=click.File('r'))
@click.pass_context
def cli_changelog(ctx: click.Context, version: Optional[str], template: TextIO) -> None:
    releaser: Semversioner = ctx.obj['releaser']
    if template:
        changelog = releaser.generate_changelog(version=version, template=template.read())
    else:
        changelog = releaser.generate_changelog(version=version)
    click.echo(message=changelog, nl=False)


@cli.command('add-change', help="Create a new changeset file.")
@click.pass_context
@click.option('--type', '-t', type=click.Choice(['major', 'minor', 'patch']), required=True)
@click.option('--description', '-d', required=True)
def cli_add_change(ctx: click.Context, type: str, description: str) -> None:
    releaser: Semversioner = ctx.obj['releaser']
    path: str = releaser.add_change(type, description)
    click.echo(message="Successfully created file " + path)


@cli.command('current-version', help="Show the current version.")
@click.pass_context
def cli_current_version(ctx: click.Context) -> None:
    releaser: Semversioner = ctx.obj['releaser']
    version = releaser.get_last_version()
    click.echo(message=version)


@cli.command('next-version', help="Show computed next version.")
@click.pass_context
def cli_next_version(ctx: click.Context) -> None:
    releaser: Semversioner = ctx.obj['releaser']
    version = releaser.get_next_version()
    if version is None:
        click.secho(message="Error: No changes found. No next version available.", fg='red')
        sys.exit(-1)

    click.echo(message=version, nl=False)


@cli.command('status', help="Show the status of the working directory.")
@click.pass_context
def status(ctx: click.Context) -> None:
    releaser: Semversioner = ctx.obj['releaser']
    status: ReleaseStatus = releaser.get_status()
    click.echo(message=f"Version: {status.version}")
    if len(status.unreleased_changes) > 0:
        click.echo(message=f"Next version: {status.next_version}")
        click.echo(message="Unreleased changes:")
        for change in status.unreleased_changes:
            click.secho(message=f"\t{change.type}:\t{change.description}", fg="red")
        click.echo(message="(use \"semversioner release\" to release the next version)")
    else:
        click.echo(message="No changes to release (use \"semversioner add-change\")")


@cli.command('check', help="Verifies changeset files exist.")
@click.pass_context
def cli_check(ctx: click.Context) -> None:
    releaser: Semversioner = ctx.obj['releaser']
    if not releaser.check():
        click.secho("Error: No changes to release.", fg='red')
        sys.exit(-1)
    else:
        click.echo('OK')


def main() -> None:
    # pylint: disable=no-value-for-parameter
    cli()


if __name__ == '__main__':
    main()
