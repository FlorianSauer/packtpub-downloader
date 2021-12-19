import argparse
import os.path
import sys
from enum import Enum

from tqdm import tqdm

from api import Api
from user import User


class FileTypeNames(Enum):
    pdf = 'pdf'
    mobi = 'mobi'
    epub = 'epub'
    code = 'zip'


class PacktpubBooksGrabber(object):
    parser = argparse.ArgumentParser()
    parser.add_argument('-e', '--email', required=True)
    parser.add_argument('-p', '--password', required=True)
    parser.add_argument('-d', '--directory', default='.')
    parser.add_argument('-t', '--types', default='pdf,mobi,epub,code')
    parser.add_argument('-s', '--separate', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-q', '--quiet', action='store_true')

    def __init__(self):
        self.namespace = None

    def setup(self):
        self.namespace = self.parser.parse_args(sys.argv[1:])
        if self.namespace.verbose and self.namespace.quiet:
            self.parser.error("Verbose and quiet cannot be used together.")
        self.namespace.directory = os.path.abspath(os.path.expanduser(self.namespace.directory))
        self.namespace.types = self.namespace.types.split(',')

    def run(self):
        if not os.path.exists(self.namespace.directory):
            os.makedirs(self.namespace.directory, exist_ok=True)

        # create user with his properly header
        user = User(self.namespace.email, self.namespace.password)

        books = Api.get_all_books(user, limit=25, verbose=self.namespace.verbose, quiet=self.namespace.quiet)

        books_progress_bar = tqdm(books, disable=self.namespace.quiet)

        for book in books_progress_bar:
            book_name = book.product_name.replace(' ', '_').replace('.', '_').replace(':', '_')
            for requested_file_type in self.namespace.types:
                if self.namespace.separate:
                    target_dir = os.path.join(self.namespace.directory, book_name)
                else:
                    target_dir = self.namespace.directory

                filename = os.path.join(target_dir,
                                        book_name + '.' + FileTypeNames[requested_file_type].value)

                if not os.path.exists(filename):
                    # requested file type for book does not exist yet, check if it is available at all
                    Api.get_file_types_for_book(user, book, self.namespace.verbose, books_progress_bar)
                    if requested_file_type not in book.file_types:
                        books_progress_bar.write("File Type {} is not available for book {}".format(
                            requested_file_type, book.product_name))
                        continue
                    else:
                        os.makedirs(target_dir, exist_ok=True)
                        Api.download_book(user, book, requested_file_type, filename, self.namespace.verbose,
                                          books_progress_bar)
                else:
                    books_progress_bar.write("Book {} already exists as {}".format(
                        book.product_name, requested_file_type))


if __name__ == "__main__":
    app = PacktpubBooksGrabber()
    app.setup()
    app.run()
