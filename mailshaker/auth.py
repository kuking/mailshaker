import poplib
import imaplib

import logging
import threading
import tempfile
import os

class UserPass:
    """ Basic username and password authentication, password can be encrypted as per PasswordResolver """
    def __init__(self, user, pass_, cache=False):
        self._user = user
        self._pass_ = PasswordResolver(pass_, cache=cache)

    def do_login(self, client):
        # issubclass ^ __class__ is needed for MagicMock
        if client.__class__.__name__ == "POP3_SSL":
            logging.info("Authenticating POP3_SSL client with username %s"%self._user)
            client.user(self._user)
            ret = client.pass_(self._pass_.resolve())
        elif client.__class__.__name__ == "IMAP4_SSL":
            logging.info("Authenticating IMAP4_SSL client with username %s"%self._user)
            ret = client.login(self._user, self._pass_.resolve())
        else:
            raise NotImplementedError("I don't know how to log-in into client: %s"%client.__class__.__name__)

class PasswordResolver:

    def __init__(self, passwd_token, cache=False):
        self._passwd_token = passwd_token
        self._cached_passwd = None
        self._should_cache = cache

    def resolve(self):
        if self._should_cache and self._cached_passwd is not None:
            return self._cached_passwd

        if self._passwd_token[:7] == "gpg2://":
            passwd = self._gpg2(self._passwd_token[7:])
        else:
            passwd = self._passwd_token

        if self._should_cache and self._cached_passwd is None:
            self._cached_passwd = passwd

        return passwd

    def _gpg2(self, gpg2_password_filename):
        tmpdir = tempfile.mkdtemp()
        fifoname = os.path.join(tmpdir, 'fifo')
        try:
            os.mkfifo(fifoname)
            t = threading.Thread(target=self._read_from_pipe, args = (fifoname,))
            t.start()
            os.system("gpg2 -q --yes -o %s -d %s"%(fifoname, gpg2_password_filename))
            t.join()
            os.remove(fifoname)
            os.rmdir(tmpdir)
        except OSError as e:
            logging.fatal("Faile very badly trying to obtain the password in a secure way")
            raise e
        else:
            return self._piped_content

    def _read_from_pipe(self, fifoname):
        fifo = open(fifoname, 'r')
        self._piped_content = fifo.read().strip()
        fifo.close()

