#!/usr/bin/env python3
from __future__ import annotations

from typing import List, Optional
from enum import Enum

import click
from click import BadParameter
from sh import pkill, kill
from pydantic.dataclasses import dataclass
from pydantic import BaseModel, validator


class SignalEnum(str, Enum):
    STOP: str = "TSTP"
    CONTINUE: str = "CONT"


# @dataclass
class Process(BaseModel):
    # Pattern?
    name: str
    pid_: Optional[int] = None

    @property
    def pid(self):
        if self.pid_ is not None:
            return self.pid_

        self.pid_ = getpid_(name)
        return self.pid_

    def pause(self):
        # pkill -TSPT self.name
        self.__kill(SignalEnum.STOP)
        return self

    def resume(self):
        # pkill -TSPT self.name
        self.__kill(SignalEnum.CONTINUE)
        return self

    def __kill(self, signal: SignalEnum):
        if self.pid_ is not None:
            kill(f"-{signal}", self.pid_, _ok_code=[0, 1])
        pkill(f"-{signal}", self.name, _ok_code=[0, 1])


# @dataclass
class Project(BaseModel):
    name: str
    processes: List[Process]

    @validator("processes", pre=True)
    def str_to_proc(proc):
        """ Return a obj if only name is given """
        if type(proc) == str:
            return {"name": proc}
        return proc

    def pause(self):
        for process in self.processes:
            process.pause()
        return self

    def resume(self):
        for process in self.processes:
            process.resume()
        return self


def getpid_(name: str):
    pass


def load_projects(projects: List[Dict]) -> List[Project]:
    return map(Project.parse_obj, projects)


# Make this json loads/dumps
# TODO: Look into tee for lazy evaluation but mutliple iteration
projects: List[Project] = load_projects(
    [{"name": "ec", "processes": ["dotnet", "docker", "npm", "node"]}]
)


def find_project(project_name: Optional[str]):
    """Return project with given name, first if None"""
    # TODO: Maybe use tee here? Look up later
    # If none pick last used project
    if project_name is None:
        return next(projects)

    try:
        # Look for the given project
        return next((p for p in projects if p.name == project_name))
    except StopIteration:
        raise BadParameter(
            message="Given project isn't defined",
            param=project_name,
            param_hint="project",
        )


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        # List projects if no command is given
        click.echo("Active projects:")
        for project in projects:
            click.echo(project.name)
    else:
        pass


@cli.command()
@click.argument("project", required=False)
def pause(project: Optional[str] = None):
    click.echo(f"Pausing work on {project or 'last project'}")
    find_project(project).pause()


@cli.command()
@click.argument("project", required=False)
def resume(project: Optional[str] = None):
    # If none pick last used project
    click.echo(f"Resuming work on {project or 'last project'}")
    find_project(project).resume()


if __name__ == "__main__":
    cli()
