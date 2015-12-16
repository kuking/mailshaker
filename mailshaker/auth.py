import poplib
import imaplib

import logging
import threading
import tempfile
import os

class NakedUserPass:
    """ Basic username and password authentication, provides no protection of password of any sort. """
    def __init__(self, user, pass_):
        self._user = user
        self._pass_ = pass_

    def do_login(self, client):
        # issubclass ^ __class__ is needed for MagicMock
        if client.__class__.__name__ == "POP3_SSL":
            logging.info("Authenticating POP3_SSL client with username %s"%self._user)
            client.user(self._user)
            ret = client.pass_(self._pass_)
        elif client.__class__.__name__ == "IMAP4_SSL":
            logging.info("Authenticating IMAP4_SSL client with username %s"%self._user)
            ret = client.login(self._user, self._pass_)
        else:
            raise NotImplementedError("I don't know how to log-in into client: %s"%client.__class__.__name__)

class CryptedUserPass:
    """ username and password authentication, but the password can be stored in an encrypted medium.
        i.e. gpg2:filename, given your gpg-agent configuration the password to unlock the password key can be kept
        within the agent during your session """
    def __init__(self, user, pass_):
        self._user = user
        self._pass_ = pass_
        self._effective_pass_ = ''

    def _read_from_pipe(self, fifoname):
        fifo = open(fifoname, 'r')
        self._effective_pass_ = fifo.read().strip()
        fifo.close()

    def _resolve_password(self):
        if self._pass_[:5] == "gpg2:":
            tmpdir = tempfile.mkdtemp()
            fifoname = os.path.join(tmpdir, 'fifo')
            try:
                os.mkfifo(fifoname)
                t = threading.Thread(target=self._read_from_pipe, args = (fifoname,))
                t.start()
                os.system("gpg2 --yes -o %s -d %s"%(fifoname, self._pass_[5:]))
                t.join()
                os.remove(fifoname)
                os.rmdir(tmpdir)
            except OSError as e:
                logging.fatal("Faile very badly trying to obtain the password in a secure way")
                raise e
        else:
            self._effective_pass_ = self._pass_


    def do_login(self, client):
        self._resolve_password()
        try:
            NakedUserPass(self._user, self._effective_pass_).do_login(client)
            self._effective_pass_ = ''
        except BaseException as e:
            self._effective_pass_ = ''
            raise e

