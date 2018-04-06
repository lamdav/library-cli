import pathlib
import sys

import click

cwd = pathlib.Path().cwd()
sys.path.append(cwd.as_posix())

from config import Config

config = click.make_pass_decorator(Config, ensure=True)


@click.group()
@config
def cli(config: Config):
    pass


@cli.command()
@click.argument('title')
@click.argument('author')
@click.argument('isbn')
@click.argument('pages', type=int)
@click.argument('quantity', type=int, default=1)
@config
def add_book(config: Config, title: str, author: str, isbn: str, pages: int, quantity: int):
    """
    Add a book to the library.
    """
    _warn('NOT IMPLEMENTED')


@cli.command()
@click.argument('name')
@click.argument('username')
@click.argument('phone', type=int)
@config
def add_user(config: Config, name: str, username: str, phone: int):
    """
    Add a user
    """
    _warn('NOT IMPLEMENTED')


@cli.command()
@click.argument('entity', type=click.Choice(['user', 'book']))
@click.argument('identifier')
@config
def remove(config: Config, entity: str, identifier: str):
    """
    Remove a book from the library.
    """
    _warn('NOT IMPLEMENTED')


@cli.command()
@click.argument('isbn')
@click.argument('field', type=click.Choice(['title', 'author', 'pages', 'quantity']))
@click.argument('value')
@config
def edit_book(config: Config, isbn: str, field: str, value: str):
    """
    Edit a book from the library.
    """
    _warn('NOT IMPLEMENTED')


@cli.command()
@click.argument('username')
@click.argument('field', type=click.Choice(['name', 'phone']))
@click.argument('value')
@config
def edit_user(config: Config, username: str, field: str, value: str):
    """
    Edit a user from the library.
    """
    _warn('NOT IMPLEMENTED')


@cli.command()
@click.argument('entity', type=click.Choice(['book', 'user']))
@click.argument('key_type', type=click.Choice(['title', 'author', 'isbn', 'name', 'username', 'phone']))
@click.argument('keyword')
@config
def search(config: Config, entity: str, key_type: str, keyword: str):
    """
    Search for entity.
    """
    _warn('NOT IMPLEMENTED')


@cli.command()
@click.argument('sort_by', type=click.Choice(['title', 'author', 'isbn', 'pages']))
@config
def sort_books_by(config: Config, sort_by: str):
    """
    Sort books.
    """
    _warn('NOT IMPLEMENTED')


@cli.command()
@click.argument('username')
@click.argument('isbn')
@config
def checkout(config: Config, username: str, isbn: str):
    """
    Checkout a book with given isbn for the user with username
    """
    _warn('NOT IMPLEMENTED')


@cli.command()
@click.argument('username')
@click.argument('isbn')
@config
def checkin(config: Config, username: str, isbn: str):
    """
    Return a checked out book with the given isbn
    for the user with the given username.
    """
    _warn('NOT IMPLEMENTED')


@cli.command()
@click.argument('username')
@config
def stat(config: Config, username: str):
    """
    Statistic on the user.
    """
    _warn('NOT IMPLEMENTED')


@cli.command()
@click.argument('isbn')
@config
def who_checkedout(config: Config, isbn: str):
    """
    See who has checked out a book given isbn
    """
    _warn('NOT IMPLEMENTED')


@cli.command()
@click.argument('arguments', nargs=-1, required=False)
def echo(arguments: tuple):
    """
    Echo arguments back.
    """
    click.secho(' '.join(arguments), fg='yellow')


def _success(format_string: str, *args):
    """
    Helper method to stylistically print success level logs.
    """
    __display(format_string.format(*args), 'green')


def _info(format_string: str, *args):
    """
    Helper method to stylistically print info level logs.
    """
    __display(format_string.format(*args), 'blue')


def _warn(format_string: str, *args):
    """
    Helper method to stylistycally print warning level logs.
    """
    __display(format_string.format(*args), 'yellow')


def _error(format_string: str, *args):
    """
    Helper method to stylistically print error level logs.
    """
    __display(format_string.format(*args), 'red')


def __display(message: str, color: str):
    """
    Display message with color
    """
    click.secho(message, fg=color)


if __name__ == '__main__':
    cli()
