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
        'title': 'title:book_set',
        'author': 'author:book_set',
        'isbn': 'isbn:book_set'
    }


@cli.command()
@click.argument('title')
@click.argument('author')
@click.argument('isbn')
@click.argument('pages', type=int)
@config
def add_book(config, title, author, isbn, pages):
    """
    Add a book to the library.
    """
    redis = config.redis
    key_type_to_book_set_map = config.key_type_to_book_set_map

    def create_entry():
        # Create a basic book entity.
        ID_COUNTER = 'book_id_counter'
        current_book_id = redis.incr(ID_COUNTER)
        book_id = 'book:{}'.format(current_book_id)
        _info('Storing id={} title={} author={} isbn={} pages={}', book_id, title, author, isbn, pages)
        redis.hset(book_id, 'title', title)
        redis.hset(book_id, 'author', author)
        redis.hset(book_id, 'isbn', isbn)
        redis.hset(book_id, 'pages', pages)
        _success('Created book entry')
        return book_id

    def add_book_entry_to_tracking_set(tracking_set_key, tracking_set_type, tracking, book_id):
        _info('Checking for existence of hset={} key={}', tracking_set_key, tracking)
        if redis.hexists(tracking_set_key, tracking):
            _info('Found hset={} key={}', tracking_set_key, tracking)
            book_set_key = redis.hget(tracking_set_key, tracking)
        else:
            BOOK_SET_ID_COUNTER = '{}:book_set_id_counter'.format(tracking_set_key)
            book_set_id = redis.incr(BOOK_SET_ID_COUNTER)
            book_set_key = '{}:{}:book_set{}'.format(tracking_set_type, tracking, book_set_id)
            _info('Creating hset={} key={} value={}', tracking_set_key, tracking, book_set_key)
            redis.hset(tracking_set_key, tracking, book_set_key)
        redis.sadd(book_set_key, book_id)
        _success('Added set={} key={}', book_set_key, book_id)

    # Add only if the isbn is not already in the library.
    if _in_library(redis, isbn, key_type_to_book_set_map):
        sys.exit(1)

    # Process:
    # 1. Create book entry.
    # 2. Link each title:book_set, author:book_set, isbn:book_set with a new set or existing set
    # 2a. If existing, then search will pair these up. Ex: same titles.
    # 2b. If not, it is a brand new entry.
    # 2c. Only isbn should remain unique. (verified above)
    # 3. Add book_id to sets.
    # (field:book_set) -> book_set_id -> book_set_id -> book
    book_id = create_entry()
    book_dict = {
        'title': title,
        'author': author,
        'isbn': isbn,
        'pages': pages
    }
    for book_set_type, book_set_key in key_type_to_book_set_map.items():
        add_book_entry_to_tracking_set(book_set_key, book_set_type, book_dict.get(book_set_type), book_id)


@cli.command()
@click.argument('isbn')
@config
def remove_book(config, isbn):
    """
    Remove a book from the library.
    """
    redis = config.redis
    key_type_to_book_set_map = config.key_type_to_book_set_map
    isbn_to_book_set_key = key_type_to_book_set_map.get('isbn', 'isbn:book_set')

    # Remove books that are in the library.
    if not _in_library(redis, isbn, key_type_to_book_set_map):
        sys.exit(1)

    # Get book_set (will have cardinaity=1)
    isbn_book_set = redis.hget(isbn_to_book_set_key, isbn)
    book_set = redis.smembers(isbn_book_set)

    for book_id in book_set:
        # Clean up the field:book_sets and book_sets.
        for field_type, field_to_book_set_key in key_type_to_book_set_map.items():
            # Get the value of the book (i.e. title, author, etc.)
            field_value = redis.hget(book_id, field_type)

            # Remove entry from set of book_id
            field_book_set_id = redis.hget(field_to_book_set_key, field_value)
            _info('removing set={} key={}', field_book_set_id, book_id)
            redis.srem(field_book_set_id, book_id)

            # If it is empty after removal, remove book_set from field:book_sets.
            # This means there are no other fields with say title 'hello'.
            if redis.scard(field_book_set_id) == 0:
                _info('deleting set={}', field_book_set_id)
                redis.delete(field_book_set_id)
                _info('removing hset={} key={}', field_to_book_set_key, field_value)
                redis.hdel(field_to_book_set_key, field_value)

        _info('deleting book_id={}', book_id)
        redis.delete(book_id)


@cli.command()
@config
def edit_book(config):
    """
    Edit a book from the library.
    """
    _warn('NOT IMPLEMENTED')


@cli.command()
@click.argument('key_type', type=click.Choice(['title', 'author', 'isbn']))
@click.argument('keyword')
@config
def search_book(config: Config,  key_type: str, keyword: str):
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
    _info('Using key={} to get book_set_key', TYPE_TO_BOOK)
    if redis.hexists(TYPE_TO_BOOK, keyword):
        book_set_key = redis.hget(TYPE_TO_BOOK, keyword)
    else:
        _warn('book with {} {} does not exist in library', key_type, keyword)
        sys.exit(1)
    _info('Got book_set_key {}', book_set_key)

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
        _success('{}: title={} author={} isbn={} pages={}', index, title, author, isbn, pages)
    sys.exit(0)


@cli.command()
@click.argument('sort_by', type=click.Choice(['title', 'author', 'isbn', 'pages']))
@config
def sort_books_by(config: Config, sort_by: str):
    """
    Sort books.
    """
    _warn('NOT IMPLEMENTED')


def _in_library(redis: Redis, isbn: str, key_type_to_book_set_map: dict):
    # Use uniqueness of isbn numbers to determine existence in
    isbn_to_book_set_key = key_type_to_book_set_map.get('isbn', 'isbn:book_set')
    if redis.hexists(isbn_to_book_set_key, isbn):
        _warn('A book with isbn {} already exists', isbn)
        return True
    return False


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
