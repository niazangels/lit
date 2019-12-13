import argparse
import collections
import configparser
import hashlib
import os
import abc
import re
import sys
import zlib
from pathlib import Path

# You don't just call `lit`. You call `lit <command>`
argparse = argparse.ArgumentParser(description="Content tracker")
argsubparsers = argparse.add_subparsers(title="Commands", dest="command")
argsubparsers.required = True

argsp = argsubparsers.add_parser("init", help="Initialize a new repository")
argsp.add_argument(
    "path",
    metavar="directory",
    nargs="?",
    default=Path("."),
    help="Where to create the repository",
)


def main(argv=sys.argv[1:]):
    args = argparse.parse_args(argv)
    legal_commands = {
        "init": cmd_init,
        # "add": cmd_add,
        # "cat-file": cmd_cat_file,
        # "checkout": cmd_checkout,
        # "commit": cmd_commit,
        # "hash-object": cmd_hash_object,
        # "log": cmd_log,
        # "ls-tree": cmd_ls_tree,
        # "merge": cmd_merge,
        # "rebase": cmd_rebase,
        # "rev-parse": cmd_rev_parse,
        # "rm": cmd_rm,
        # "show-ref": cmd_show_ref,
        # "tag": cmd_tag,
    }
    if args.command in legal_commands:
        fn = legal_commands.get(args.command, cmd_not_found)
        fn(args)


class GitRepository:
    """
        A git repo
    """

    worktree = None
    gitdir = None
    conf = None

    def __init__(self, path, force=False):
        self.worktree = path
        self.gitdir = path / ".git"

        if not force and not self.gitdir.is_dir():
            raise Exception(f"{path} is not a Git repository")

        self.conf = configparser.ConfigParser()
        cf = repo_file(self, "config")

        if cf and cf.exists():
            self.conf.read([cf])
        elif not force:
            raise Exception("Configuration file is missing")

        if not force:
            vers = int(self.conf.get("core", "repositoryformatversion"))
            if vers != 0:
                raise Exception(f"Unsupported repositoryformatversion ({vers}) in {cf}")


def repo_path(repo, *path):
    """
        Returns the absolute path
    """
    return Path.joinpath(repo.gitdir, *path)


def repo_dir(repo, *path, mkdir=False):
    """
        Same as repo_path, but makes dir if it doesn't exist
        Returns the path of the dir if it exists or was created
        Else returns None 
    """
    path = repo_path(repo, *path)

    if Path.exists(path):
        if not Path.is_dir(path):
            raise Exception(f"{path} is not a directory")
        return path

    if mkdir:
        Path.mkdir(path, parents=True)
        return path


def repo_file(repo, *path, mkdir=False):
    """
        Performs a repo_create upto the parent folder for a file
        Returns repo_path for the path given file
    """
    if repo_dir(repo, *path[:-1], mkdir=mkdir):
        return repo_path(repo, *path)


def repo_create(path):
    """
        Create a new repository
    """

    def repo_default_config():
        conf = configparser.ConfigParser()

        conf.add_section("core")
        conf.set("core", "repositoryformatversion", "0")
        conf.set("core", "filemode", "false")
        conf.set("core", "bare", "false")
        return conf

    repo = GitRepository(path, force=True)
    if repo.worktree.exists():
        if not repo.worktree.is_dir():
            raise Exception(f"{repo.worktree} is not a directory")
        if any((_ for _ in Path.iterdir(repo.worktree))):
            raise Exception(f"{repo.worktree} is not empty")
    else:
        Path.mkdir(repo.worktree, parents=True)

    assert repo_dir(repo, "branches", mkdir=True)
    assert repo_dir(repo, "objects", mkdir=True)
    assert repo_dir(repo, "refs", "tags", mkdir=True)
    assert repo_dir(repo, "refs", "heads", mkdir=True)

    # .git/description
    file_desc = repo_file(repo, "description")
    with open(file_desc, "w") as f:
        f.write("This is an unnamed repository. Edit this file to name it.")

    # .git/HEAD
    file_head = repo_file(repo, "HEAD")
    with open(file_head, "w") as f:
        f.write("ref: refs/heads/master\n")

    # .git/config
    file_config = repo_file(repo, "config")
    with open(file_config, "w") as f:
        config = repo_default_config()
        config.write(f)
    return repo


def repo_find(path=".", required=True):
    path = Path(path).resolve()

    if (path / ".git").is_dir():
        return GitRepository(path)

    parent = path / ".."

    if parent == path:
        # We're at the root level now
        # >>> Path("/") / ".."
        # Path("/")
        if required:
            raise Exception("🤷‍♂️ Could not find a git repository")
        return None
    return repo_find(parent, required)


class GitObject(metaclass=abc.ABCMeta):
    repo = None  # @niazangels: But why?

    def __init__(self, repo, data=None):
        self.repo = repo
        if data != None:
            self.deserialize(data)

    @abc.abstractmethod
    def serialize(self):
        """
            Read object's contents from self.data and convert it to 
            a meaningful representation
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def deserialize(self, data):
        raise NotImplementedError()


def cmd_init(args):
    repo_create(args.path)


def cmd_not_found(args):
    print("🤷‍♂️ No such command!")
