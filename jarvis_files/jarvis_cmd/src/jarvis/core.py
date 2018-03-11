from contextlib import contextmanager
import subprocess as sp
import typing as T
import os
import shutil
import click
import jinja2
import venv


def exec_in_venv(env_path: T.Union[os.PathLike, str],
                 command: [str], check=True,
                 capture=False) -> sp.CompletedProcess:
    """
    Runs a command in the virtual environment given by env_path
    """
    click.secho('Activating venv...', dim=True)
    venv_bindir = os.path.join(env_path, 'bin')
    orig_path = os.environ['PATH']
    try:
        new_path = '{}:{}'.format(venv_bindir, orig_path)
        os.environ['PATH'] = new_path
        click.secho('exec {}'.format(command), dim=True)
        process = sp.run(
                command,
                check=check,
                stdout=sp.PIPE if capture else None,
                stderr=sp.PIPE if capture else None)
        return process
    finally:
        os.environ['PATH'] = orig_path


def shell(command: str, check=True, capture=False) -> sp.CompletedProcess:
    """
    Runs `command` in a shell.
    """
    click.secho('$ {}'.format(command), dim=True)
    process = sp.run(
            command,
            check=check,
            shell=True,
            stdout=sp.PIPE if capture else None,
            stderr=sp.PIPE if capture else None)
    return process


def cp(src: T.Union[os.PathLike, str], dest: T.Union[os.PathLike, str]):
    """
    Copies files from `src` -> `dest`
    """
    click.secho('$ cp "{}" "{}"'.format(src, dest), dim=True)
    if os.path.isdir(src):
        if os.path.exists(dest):
            shutil.rmtree(dest)
        shutil.copytree(src, dest)
    else:
        dest_path = dest
        if os.path.isdir(dest):
            dest_path = os.path.join(dest, os.path.basename(src))

        if os.path.exists(dest_path):
            os.unlink(dest_path)
        shutil.copy(src, dest_path)


def mv(src: T.Union[os.PathLike, str], dest: T.Union[os.PathLike, str]):
    """
    Moves a file from `src` -> `dest`
    """
    click.secho('$ mv "{}" "{}"'.format(src, dest), dim=True)
    if os.path.isdir(src):
        if os.path.exists(dest):
            shutil.rmtree(dest)
    else:
        dest_path = dest
        if os.path.isdir(dest):
            dest_path = os.path.join(dest, os.path.basename(src))

        if os.path.exists(dest_path):
            os.unlink(dest_path)
    shutil.move(src, dest)


def ln(src: T.Union[os.PathLike, str], dest: T.Union[os.PathLike, str]):
    """
    Make a symlink from `src` -> `dest`
    """
    click.secho('$ ln -s "{}" "{}"'.format(src, dest), dim=True)
    if os.path.exists(dest):
        return
    if os.path.exists(dest) and not os.path.islink(dest):
        os.unlink(dest)
    os.symlink(src, dest)


def rm(path_: T.Union[os.PathLike, str]):
    """
    Removes `path`
    """
    click.secho('$ rm "{}"'.format(path_), dim=True)
    if os.path.isdir(path_):
        shutil.rmtree(path_)
    else:
        os.unlink(path_)


def ensure_dir(path_: T.Union[os.PathLike, str]):
    """
    Ensures that `path` is a directory.
    """
    if not os.path.exists(path_):
        os.makedirs(path_)


@contextmanager
def cd(path_: T.Union[os.PathLike, str]):
    """
    Changes the current working directory.
    """
    click.secho('$ cd {}'.format(path_), dim=True)
    cwd = os.getcwd()
    os.chdir(path_)
    yield
    os.chdir(cwd)


@contextmanager
def quiet():
    """
    Suppress stdout and stderr.
    """
    null_fds = [
        os.open(os.devnull, os.O_RDWR),
        os.open(os.devnull, os.O_RDWR)
    ]

    stdout, stderr = os.dup(1), os.dup(2)
    null_fd1, null_fd2 = null_fds
    os.dup2(null_fd1, 1)
    os.dup2(null_fd2, 2)

    yield

    os.dup2(stdout, 1)
    os.dup2(stderr, 2)

    for fd in null_fds:
        os.close(fd)


class Workspace:
    def __init__(self, root_dir):
        self.root = root_dir
        self.build_root = os.path.join(os.path.expanduser('~'), '.mrover')
        self.product_env = os.path.join(self.build_root, 'build_env')
        self.jarvis_env = os.path.join(self.build_root, 'jarvis_env')
        self.hash_store = os.path.join(self.build_root, 'project_hashes')
        self.intermediate = os.path.join(self.build_root, 'scratch')

        self.templates = jinja2.Environment(loader=jinja2.FileSystemLoader(
            os.path.join(self.root, 'jarvis_files', 'templates')))

    def template(self, name, dest_file, **kwargs):
        tpl = self.templates.get_template(name)
        with open(dest_file, 'w') as f:
            f.write(tpl.render(**kwargs))

    def ensure_product_env(self):
        if not os.path.isdir(self.product_env):
            venv.create(self.product_env, symlinks=True, with_pip=True)

    def product_exec(self, command, **kwargs):
        try:
            exec_in_venv(self.product_env, command, **kwargs)
        except:
            pass

    def jarvis_exec(self, command, **kwargs):
        try:
            exec_in_venv(self.jarvis_env, command, **kwargs)
        except:
            pass

    def clean(self):
        try:
            rm(self.product_env)
            rm(self.hash_store)
        except:
            pass