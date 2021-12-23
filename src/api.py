from datetime import datetime
from typing import Tuple, List, Any, Optional

import requests
from tqdm import tqdm

from config import BASE_URL, PRODUCTS_ENDPOINT, TIMESTAMP_FORMAT, URL_BOOK_TYPES_ENDPOINT, URL_BOOK_ENDPOINT
from user import User


class Book(object):
    # {'id': 'f634bcd8-0e16-4dc9-b17f-f1572dacd371',
    #  'userId': 'fa92d338-ab10-44a1-ba18-00ee55dca20b',
    #  'productId': '9781788837996',
    #  'productName': 'Deep Learning Quick Reference',
    #  'releaseDate': '2018-03-09T12:50:00.000Z',
    #  'entitlementSource': 'free learning',
    #  'entitlementLink': '630d71c8-6e88-4b89-838a-dbd36a176159',
    #  'createdAt': '2021-12-18T00:19:40.773Z',
    #  'updatedAt': '2021-12-18T00:19:40.773Z'}

    def __init__(self, id, user_id, product_id, product_name, release_date, entitlement_source, entitlement_link,
                 created_at, updated_at):
        # type: (str, str, int, str, datetime, str, str, datetime, datetime) -> None
        self.id = id
        self.user_id = user_id
        self.product_id = product_id
        self.product_name = product_name
        self.release_date = release_date
        self.entitlement_source = entitlement_source
        self.entitlement_link = entitlement_link
        self.created_at = created_at
        self.updated_at = updated_at
        self._file_types = None

    def has_file_types(self):
        return self._file_types is not None

    @property
    def file_types(self):
        if self._file_types is None:
            raise RuntimeError("File Types not set yet!")
        return self._file_types

    def set_file_types(self, file_types):
        # type: (List[str]) -> None
        self._file_types = file_types

    @classmethod
    def from_json(cls, json_dict):
        return cls(
            id=json_dict['id'],
            user_id=json_dict['userId'],
            product_id=int(json_dict['productId']),
            product_name=json_dict['productName'],
            release_date=datetime.strptime(json_dict['releaseDate'], TIMESTAMP_FORMAT),
            entitlement_source=json_dict['entitlementSource'],
            entitlement_link=json_dict['entitlementLink'],
            created_at=datetime.strptime(json_dict['createdAt'], TIMESTAMP_FORMAT),
            updated_at=datetime.strptime(json_dict['updatedAt'], TIMESTAMP_FORMAT),
        )


class Api(object):
    @classmethod
    def get_total_book_count(cls, user):
        # type: (User) -> int
        url = BASE_URL + PRODUCTS_ENDPOINT.format(offset=0, limit=0)
        r = requests.get(url, headers=user.get_header())
        return r.json()['count']

    @classmethod
    def book_request(cls, user, offset=0, limit=10, verbose=False, printer=None):
        # type: (User, int, int, bool, Optional[tqdm]) -> Tuple[List[Book], Any]
        url = BASE_URL + PRODUCTS_ENDPOINT.format(offset=offset, limit=limit)

        if verbose and printer:
            printer.write("GET {}".format(url))
        elif verbose and not printer:
            print("GET {}".format(url))

        r = requests.get(url, headers=user.get_header())

        total_book_count = r.json().get('count', 0)
        books = [Book.from_json(book) for book in r.json().get('data', [])]

        return books, total_book_count

    @classmethod
    def get_all_books(cls, user, limit=10, verbose=False, quiet=False):
        # type: (User, int, bool, bool) -> List[Book]
        # bug caused by packtpub api
        # the second page/request would return all possessed books (minus the first x grabbed books)
        # Example: 1000 possessed ebooks
        # request 1: offset=0, limit=25 -> returns 25 books
        # request 2: offset=25, limit=25 -> returns 975 books
        # Solution:
        # get total number of possessed books with first request
        # loop until collected books match total number of possessed books
        offset = 0
        pages_range_iterator = tqdm(total=0, unit='Books',
                                    disable=quiet)

        collected_books, total_book_count = cls.book_request(user, offset=offset, limit=limit, verbose=verbose,
                                                             printer=pages_range_iterator)

        pages_range_iterator.total = total_book_count

        pages_range_iterator.update(len(collected_books))

        pages_range_iterator.write('You have {} books'.format(total_book_count))
        pages_range_iterator.write("Getting list of books...")

        while len(collected_books) < total_book_count:
            offset += limit
            books_list, _ = cls.book_request(user, offset=offset, limit=limit, verbose=verbose,
                                             printer=pages_range_iterator)
            pages_range_iterator.update(len(books_list))
            collected_books.extend(books_list)

        return collected_books

    @classmethod
    def get_file_types_for_book(cls, user, book, verbose, printer):
        # type: (User, Book, bool, tqdm) -> None
        url = BASE_URL + URL_BOOK_TYPES_ENDPOINT.format(book_id=book.product_id)

        if verbose:
            printer.write("GET {}".format(url))

        r = requests.get(url, headers=user.get_header())

        if (r.status_code == 200):  # success
            file_types = r.json()['data'][0].get('fileTypes', [])
            book.set_file_types(file_types)
        elif (r.status_code == 401):  # jwt expired
            user.refresh_header()  # refresh token
            return cls.get_file_types_for_book(user, book, verbose, printer)  # call recursive
        else:
            printer.write('ERROR (please copy and paste in the issue)')
            printer.write("HTTP Status Code: {}".format(r.status_code))
            printer.write(str(r.json()))
            book.set_file_types([])
            return

    @classmethod
    def _get_url_for_book(cls, user, book, book_format, verbose, printer):
        # type: (User, Book, str, bool, tqdm) -> str
        url = BASE_URL + URL_BOOK_ENDPOINT.format(book_id=book.product_id, format=format)
        if verbose:
            printer.write("GET {}".format(url))
        r = requests.get(url, headers=user.get_header())

        if r.status_code == 200:  # success
            return r.json().get('data', '')
        elif r.status_code == 401:  # jwt expired
            user.refresh_header()  # refresh token
            return cls._get_url_for_book(user, book, book_format, verbose, printer)  # call recursive
        else:
            printer.write('ERROR (please copy and paste in the issue)')
            printer.write("HTTP Status Code: {}".format(r.status_code))
            printer.write(str(r.json()))
            return ''

    @classmethod
    def download_book(cls, user, book, book_format, filename, verbose, printer):
        # type: (User, Book, str, str, bool, tqdm) -> None

        url = cls._get_url_for_book(user, book, book_format, verbose, printer)

        if not url:
            printer.write("Unable to download book {} as {}".format(book.product_name, book_format))
            return

        with open(filename, 'wb') as f:

            if verbose:
                printer.write("GET {}".format(url))
            r = requests.get(url, headers=user.get_header(), stream=True)

            if r.status_code == 200:  # success
                printer.write('Starting download for Book {} as {}'.format(book.product_name, book_format))
                file_size = r.headers.get('content-length')
                if file_size:
                    file_size = int(file_size)

                progress_bar = tqdm(total=file_size, unit='B', unit_scale=True, position=1)

                for chunk in r.iter_content(1024 * 16):
                    if chunk:
                        f.write(chunk)
                        progress_bar.update(len(chunk))
                printer.write('... done')
            elif r.status_code == 401:  # jwt expired
                user.refresh_header()  # refresh token
                return cls.download_book(user, book, book_format, filename)  # call recursive
            else:
                printer.write('ERROR (please copy and paste in the issue)')
                printer.write("HTTP Status Code: {}".format(r.status_code))
                printer.write(str(r.json()))
                return
