import os
import sys
import codecs
import poplib
poplib._MAXLINE=20480
from urllib.parse import urlparse
import email
import email.parser
import logging

from .auth import *

class Tap:
    """ A base class for taps, defines basic methods """

    name = 'A tap name'

    """ If the message is acepted by a sink/mailbox (or multiple), it will delete the message from the tap/source if
        do_move is True """
    do_move = False

    def start(self):
        """ before using the tap, it should be started """
        raise NotImplementedError()

    def close(self):
        """ Closes resources, connections, etc. after usage """
        raise NotImplementedError()

    def all_messages(self):
        """ Return an iterator of (msg_id, msg) providing all the messages in this tap. Subclasses need to either
            implemented this method, or the more specific selected_messages (with perhaps some extra optimisations).
            msg_id is a reference valid only within the tap, i.e. for a POP3 it will be the current session message
            number, for a folder tap, it will be the file containing the message. """
        raise NotImplementedError()

    def selected_messages(self):
        """ Returns an iterator of ("TAG", msg_id, msg), implementation can be overrided for performance. """
        for (msg_id, msg) in self.all_messages():
            tag = self.select_and_tag(msg)
            if tag is not None:
                logging.info("%s selecting %s"%(self.name, msg_id))
                yield (tag, msg_id, msg)
            else:
                logging.info("%s ignoring %s"%(self.name, msg_id))

    def select_and_tag(self, msg):
        """ Returns a str representing the tag associated to this message, or None if it should be discarded. """
        raise NotImplementedError()

    def delete(self, msg_id):
        """ Deletes the message. """
        raise NotImplementedError()


class FolderTap(Tap):

    _effective_path = '.'
    _recursive = False
    _try_latin1 = False

    def __init__(self, folder, name='a folder tap', recursive=False, try_latin1=False):
        self._effective_path = os.path.normpath(folder)
        self.name = name
        self._recursive = recursive
        self._try_latin1 = try_latin1

    def start(self):
        if self._recursive:
            self._all_files = [os.path.join(dp, f) for dp, dn, fn in os.walk(self._effective_path) for f in fn]
        else:
            self._all_files = [os.path.join(self._effective_path, f) for f in os.listdir(self._effective_path)]

    def close(self):
        pass

    def all_messages(self):
        parser = email.parser.Parser()
        for path in self._all_files:
            try:
                f = codecs.open(path, 'r')
                msg = parser.parse(f)
                f.close()
                yield (path, msg)
            except IsADirectoryError:
                pass
            except UnicodeDecodeError as e:
                if not self._try_latin1:
                    logging.error("Couldn't decode %s - error: %s"%(path, e))
                else:
                    logging.info("HACK! failed with UTF-8, trying with latin-1...")
                    try:
                        f = codecs.open(path, 'r', encoding='latin-1')
                        msg = parser.parse(f)
                        f.close()
                        yield(path, msg)
                    except UnicodeDecodeError as ee:
                        logging.error("Couldn't decode %s, even after trying with latin-1 Hack, Unicode: %s"%(path, ee))

    def select_and_tag(self, msg):
        return "Default"

    def delete(self, msg_id):
        logging.info("%s removing %s"%(self.name, msg_id))
        os.remove(msg_id)


class Pop3Tap(Tap):

    url = 'pop3+ssl://pop.example.com'
    credential = NakedUserPass('anonymous', 'guest@example.com')

    _conn = None

    def start(self):
        url = urlparse(self.url)
        if url.scheme.upper() == "POP3+SSL":
            self._conn = poplib.POP3_SSL(url.hostname, url.port if url.port==None else 995)
            self.credential.do_login(self._conn)
        else:
            raise NotImplementedError("I don't know how to connect to protocol: %s",url.scheme)

    def close(self):
        if self._conn is not None:
            self._conn.quit()

    def all_messages(self):
        i = 1
        max = len(self._conn.list()[1]) + 1
        while i < max:
            (response, lines, octets) = self._conn.retr(i)
            parser = email.parser.BytesFeedParser()
            for line in lines:
                parser.feed(line)
                parser.feed(b'\n')
            yield (i, parser.close())
            i += 1

    def delete(self, msg_id):
        logging.info("%s removing %s"%(self.name, msg_id))
        self._conn.dele(msg_id)


