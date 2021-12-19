import sys

import requests

from config import BASE_URL, AUTH_ENDPOINT


class User(object):
    """
    User object that contain his header
    """
    # need to fill Authoritazion with current token provide by api
    base_header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 " +
                      "(KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36",
        "Authorization": ""
    }

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self._header = None

    def get_header(self):
        if self._header is None:
            self._header = dict(self.base_header)
            self._header["Authorization"] = self.get_token()
        return self._header

    def get_token(self):
        """
        Request auth endpoint and return user token
        """
        url = BASE_URL + AUTH_ENDPOINT
        # use json paramenter because for any reason they send user and pass in plain text :'(  
        r = requests.post(url, json={'username': self.username, 'password': self.password})
        if r.status_code == 200:
            print("You are in!")
            return 'Bearer ' + r.json()['data']['access']

        # except should happend when user and pass are incorrect 
        print("Error login,  check user and password")
        print("Error {}".format(r.json()))
        sys.exit(2)

    def refresh_header(self):
        """
        Refresh jwt because it expired and returned
        """
        self._header = None
        return self.get_header()
