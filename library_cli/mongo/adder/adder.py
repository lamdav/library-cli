from typing import List

import click

from ...api.book import Book
from ...api.user import User
from ...context_extractor import extract_api


@click.group()
@click.pass_context
def add(context: click.Context):
    """
    Library Add Commands.
    """
    api = extract_api(context)
    api.log_tag('ADD')


@add.command()
@click.option('--title', '-t', help='Book Title', required=True)
@click.option('--author', '-a', help='Book Author(s)', required=True, multiple=True)
@click.option('--isbn', '-i', help='Book ISBN', required=True)
@click.option('--pages', '-p', help='Book Pages', type=int, required=True)
@click.option('--quantity', '-q', help='Quantity to Add (default: 1)', type=int, default=1)
@click.pass_context
def book(context: click.Context, title: str, author: List[str], isbn: str, pages: int, quantity: int):
    """
    Add a book to the library.
    """
    api = extract_api(context)
    book = Book(title, author, isbn, pages, quantity)
    exit(0) if api.add_book(book) else exit(1)


@add.command()
@click.option('--name', '-n', help='User\'s Name', required=True)
@click.option('--username', '-u', help='User\'s Username', required=True)
@click.option('--phone', '-p', help='User\'s Phone Number', type=int, required=True)
@click.pass_context
def user(context: click.Context, name: str, username: str, phone: int):
    """
    Add a user to the library.
    """
    api = extract_api(context)
    user = User(name, username, phone)
    exit(0) if api.add_user(user) else exit(1)
