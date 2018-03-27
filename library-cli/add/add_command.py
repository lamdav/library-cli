import click

# from .config import Config

class Config(object):
    def __init__(self):
        pass
config = click.make_pass_decorator(Config, ensure=True)

@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Print all logs')
@config
def add(config, verbose):
    _setup_config(config, verbose)


def _setup_config(config, verbose):
    config.verbose = verbose
    config.redis = Redis(charset='utf-8', decode_responses=True)
    config.key_type_to_book_set_map = {
        'title': 'title:book',
        'author': 'author:book',
        'isbn': 'isbn:book'
    }


@add.command()
@click.argument('title')
@click.argument('author')
@click.argument('isbn')
@click.argument('pages')
@config
def book(config, title, author, isbn, pages):
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
