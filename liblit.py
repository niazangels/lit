import argparse
import collections
import configparser
import hashlib
import os
import re
import sys
import zlib

# You don't just call `lit`. You call `lit <command>`
argparse = argparse.ArgumentParser(description="Content tracker")
argsubparsers = argparse.add_subparsers(title="Commands", dest="command")
argsubparsers.required = True


def main(argv=sys.argv[1:]):
    args = argparse.parse_args(argv)
    legal_commands = {
        "add": cmd_add,
        "cat-file": cmd_cat_file,
        "checkout": cmd_checkout,
        "commit": cmd_commit,
        "hash-object": cmd_hash_object,
        "init": cmd_init,
        "log": cmd_log,
        "ls-tree": cmd_ls_tree,
        "merge": cmd_merge,
        "rebase": cmd_rebase,
        "rev-parse": cmd_rev_parse,
        "rm": cmd_rm,
        "show-ref": cmd_show_ref,
        "tag": cmd_tag,
    }
    if args.command in legal_commands:
        fn = legal_commands[args.command]
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

