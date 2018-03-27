import click
import sys

from config import Config
from redis import Redis

config = click.make_pass_decorator(Config, ensure=True)


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Print all logs')
@config
def cli(config, verbose):
    config.verbose = verbose
    config.redis = Redis(charset='utf-8', decode_responses=True)
    config.key_type_to_book_set_map = {
        'title': 'title:book',
        'author': 'author:book',
        'isbn': 'isbn:book'
    }


@cli.command()
@click.argument('title')
@click.argument('author')
@click.argument('isbn')
@click.argument('pages')
@config
def add_book(config, title, author, isbn, pages):
    """
    Add a book to the library.
    """
    redis = config.redis

    def create_entry():
        # Create a basic book entity.
        ID_COUNTER = 'book_id_counter'
        current_book_id = redis.incr(ID_COUNTER)
        book_entry_key = 'book:{}'.format(current_book_id)
        _info('Storing {} {} {} {} as {}', title,
              author, isbn, pages, book_entry_key)
        redis.hset(book_entry_key, 'title', title)
        redis.hset(book_entry_key, 'author', author)
        redis.hset(book_entry_key, 'isbn', isbn)
        redis.hset(book_entry_key, 'pages', pages)
        _success('Created book entry')
        return book_entry_key

    def add_book_entry_to_tracking_set(tracking_set_key, tracking, book_entry_key):
        tracking_set_counter = '{}_counter'.format(tracking_set_key)
        if redis.hexists(tracking_set_key, tracking):
            book_set_key = redis.hget(tracking_set_key, tracking)
        else:
            _info('{} missing {} entry. Creating entry',
                  tracking_set_key, tracking)
            book_set_id = redis.incr(tracking_set_counter)
            book_set_key = '{}:{}'.format(tracking_set_key, book_set_id)
            redis.hset(tracking_set_key, tracking, book_set_key)
        click.echo(book_set_key)
        redis.sadd(book_set_key, book_entry_key)
        _success('Added book entry to {} set', tracking_set_key)

    # To search by title, we keep a mapping of title -> book_set_id
    # Book set id are a set of book_ids that share this title.
    book_entry_key = create_entry()
    TITLE_TO_BOOK = 'title:book'
    add_book_entry_to_tracking_set(TITLE_TO_BOOK, title, book_entry_key)
    AUTHOR_TO_BOOK = 'author:book'
    add_book_entry_to_tracking_set(AUTHOR_TO_BOOK, author, book_entry_key)
    ISBN_TO_BOOK = 'isbn:book'
    add_book_entry_to_tracking_set(ISBN_TO_BOOK, isbn, book_entry_key)


@cli.command()
@click.argument('title')
@click.argument('author')
@click.argument('isbn')
@click.argument('pages')
@config
def remove_book(config, title, author, isbn, pages):
    """
    Remove a book from the library.
    """
    _warn('NOT IMPLEMENTED')


@cli.command()
@config
def edit_book(config):
    """
    Edit a book from the library.
    """
    _warn('NOT IMPLEMENTED')


@cli.command()
@click.argument('keyword')
@click.argument('key_type', type=click.Choice(['title', 'author', 'isbn']))
@config
def search_book(config: Config, keyword: str, key_type: str):
    """
    Search for books.
    """
    redis = config.redis
    key_type_to_book_set_map = config.key_type_to_book_set_map

    # Get proper key to map to search.
    TYPE_TO_BOOK = key_type_to_book_set_map.get(key_type, None)
    if TYPE_TO_BOOK is None:
        _error('Unsupported key_type {}', key_type)
        sys.exit(1)

    # Get book_set_key
    if redis.hexists(TYPE_TO_BOOK, keyword):
        book_set_key = redis.hget(TYPE_TO_BOOK, keyword)
    else:
        _warn('book with {} {} does not exist in library', key_type, keyword)
        sys.exit(1)

    # Get book_entry_keys associated with this title.
    book_entry_keys = redis.smembers(book_set_key)
    books = []
    for book_entry_key in book_entry_keys:
        books.append(redis.hgetall(book_entry_key))

    # Print it out nicely.
    for index, book in enumerate(books):
        title = book.get('title')
        author = book.get('author')
        isbn = book.get('isbn')
        pages = book.get('pages')
        _info('{}: title={} author={} isbn={} pages={}',
              index, title, author, isbn, pages)
    sys.exit(0)


@cli.command()
@click.argument('sort_by', type=click.Choice(['title', 'author', 'isbn', 'pages']))
@config
def sort_books_by(config: Config, sort_by: str):
    """
    Sort books.
    """
    _warn('NOT IMPLEMENTED')


@cli.command()
@click.argument('arguments', nargs=-1, required=False)
@config
def echo(config: Config, arguments: tuple):
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
    click.secho(message, fg=color)


if __name__ == '__main__':
    cli()
