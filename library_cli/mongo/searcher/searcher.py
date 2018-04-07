from typing import List, Callable

import click

from ...context_extractor import extract_api

BOOK_SEARCHABLE_FIELDS = ['title', 'authors', 'isbn', 'name']
USER_SEARCHABLE_FIELDS = ['name', 'username', 'phone']


@click.group()
@click.pass_context
def search(context: click.Context):
    """
    Library Search Commands.
    """
    api = extract_api(context)
    api.log_tag('SEARCH')


@search.command()
@click.argument('field', type=click.Choice(BOOK_SEARCHABLE_FIELDS))
@click.argument('value', nargs=-1, required=True)
@click.pass_context
def book(context: click.Context, field: str, value: List[str]):
    """
    Search for Book.
    """
    api = extract_api(context)
    books = api.find_book(field, value)
    __display(books, api.error, api.success)


@search.command()
@click.argument('field', type=click.Choice(USER_SEARCHABLE_FIELDS))
@click.argument('value')
@click.pass_context
def user(context: click.Context, field: str, value: str):
    """
    Search for User.
    """
    api = extract_api(context)
    users = api.find_user(field, value)
    __display(users, api.error, api.success)


def __display(data, on_error: Callable, on_success: Callable):
    if not data:
        on_error('No matched found')
        exit(1)
    else:
        for index, datum in enumerate(data):
            on_success('{}: {}', index, datum)
        exit(0)
