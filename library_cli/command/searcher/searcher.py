from typing import List

import click

from ...context_extractor import extract_api
from ...entity_displayer import display_entities

BOOK_SEARCHABLE_FIELDS = ['title', 'authors', 'isbn']
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
    display_entities(books, api.error, api.success)


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
    display_entities(users, api.error, api.success)
