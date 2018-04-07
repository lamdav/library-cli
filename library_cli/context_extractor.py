import click

from .api.library_api import LibraryAPI


def extract_api(context: click.Context) -> LibraryAPI:
    return context.obj.get('api')
