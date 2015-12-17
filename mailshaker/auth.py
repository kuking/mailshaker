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
    """
        This class resolves multiple ways of storing passwords:

            plaintext
            =========
               just initialize if with a password, but you can't have a password that starts with gpg2:// or aes256cbc:// etc...
               but if you need to, you can be explicit by starting with: plain://-and-the-password-here-

            gpg2://
            =======
              gpg2 -e -a   < to encrypt
              gpg2 -d      < to decrypt

            aes256cbc://
            ============
              openssl aes-256-cbc -a -out <your-file>     < to encrypt, remember to press enter, then ctrl-d to finish the file input
              openssl aes-256-cbc -d -a -in <your-file>   < to verify

    """
    def __init__(self, passwd_token, cache=False):
        self._passwd_token = passwd_token
        self._cached_passwd = None
        self._should_cache = cache

    def resolve(self):
        if self._should_cache and self._cached_passwd is not None:
            return self._cached_passwd

        if self._passwd_token[:7] == 'gpg2://':
            passwd = self._exec_taking_output_via_pipe("gpg2 -q --yes -o %%s -d %s"%self._passwd_token[7:])
        elif self._passwd_token[:12] == 'aes256cbc://':
            passwd = self._exec_taking_output_via_pipe("openssl aes-256-cbc -d -out %%s -a -in %s"%self._passwd_token[12:])
        elif self._passwd_token[:8] == 'plain://':
            passwd = self._passwd_token[8:]
        else:
            passwd = self._passwd_token

        if self._should_cache and self._cached_passwd is None:
            self._cached_passwd = passwd

        return passwd

    def _exec_taking_output_via_pipe(self, cmd):
        tmpdir = tempfile.mkdtemp()
        fifoname = os.path.join(tmpdir, 'fifo')
        try:
            os.mkfifo(fifoname)
            t = threading.Thread(target=self._read_from_pipe, args = (fifoname,))
            t.start()
            os.system(cmd%fifoname)
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

