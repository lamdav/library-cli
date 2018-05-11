# library_cli
A CSSE433 assignment in which I had to implement several basic features
expected of a simple library management system in various NoSQL databases.
These was done to quickly pickup on the pros and cons of each NoSQL database.

## NoSQL Databases Explored
- Redis
- MongoDB
- Neo4j

My submitted solutions are all tagged with their respective database name.

## Dependencies
The specific Python client for each of the mentioned NoSQL database and
`Click` for CLI parsing.

## Install
Assumes Python and pip are of Python 3.
```shell
git clone git@github.com:lamdaV/library-cli.git library-cli
cd library-cli
pip install -e .
```

## Features
Construct a book library app with a rudimentary interface (Command line
interface works for me) using a high-level language (Python for example) that
supports the following features.

1.  Add book (Title, Author, ISBN, #of Pages) to library. Please note that a
    book may have multiple authors
2.  Delete book from library
3.  Edit book information
4.  Search by title, author, or ISBN
5.  Sort by title, author, # of pages or ISBN
6.  Add Borrower's (Name, Username, Phone) to library
7.  Delete Borrowers from library
8.  Edit Borrower information
9.  Search by name, username
10. Allow Borrowers to checkout books (Can only checkout if a book is
    available) and return books.
11. Track number of books checked out by a given user & Track which user has
    checked out a book

There were several other features specific to the database backing this CLI
such as building a simple book recommendation with `Neo4j`.

## Note To Future Rose Students
This has been submitted to Rose-Hulman as an assignment. As such, Rose-Hulman
has records of this and it is highly discouraged from submitting this repo
as is.

If you are looking for a skeleton of a CLI to implement see `library_cli/api`
and `library_cli/command`.
