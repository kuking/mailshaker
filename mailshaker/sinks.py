import string
import time
import os
from urllib.parse import urlparse
import imaplib

from .auth import *

class Sink:

    def start(self):
        """ before using the sink, it should be started """
        raise NotImplementedError()

    def close(self):
        """ Closes resources, connections, etc. after usage """
        raise NotImplementedError()

    def store(self, tag, msg):
        """ Stores a message in this sink, tag has been set by the tap selector,
            it should returns a Bool stating if it was stored (otherwise it won't be removed from origin tap). """
        raise NotImplementedError()



class Imap4Sink(Sink):

    url = 'imap4+ssl://pop.example.com'
    credentials = NakedUserPass('anonymous', 'guest@example.com')
    auto_create_folders = True
    avoid_duplicating_messages = True

    _conn = None

    def start(self):
        url = urlparse(self.url)
        if url.scheme.upper() == "IMAP4+SSL":
            self._conn = imaplib.IMAP4_SSL(url.hostname, url.port if url.port==None else 993)
            self.credential.do_login(self._conn)
        else:
            raise NotImplementedError("I don't know how to connect to protocol: %s",url.scheme)

    def close(self):
        if self._conn is not None:
            self._conn.logout()

    def tag_to_imap_folder(self, tag):
        """ User should implemented the logic to convert a TAP tag into an Imap folder """
        raise NotImplementedError()

    def store(self, tag, msg):
        imap_folder = self.tag_to_imap_folder(tag)
        if imap_folder is None:
            # log cant go from tag->imap folder
            return False

        if not self._assert_and_select_imap_folder(imap_folder):
            return False

        if self.avoid_duplicating_messages:
            if msg['MESSAGE-ID'] == None:
                print("hm, message without message-id, spamish")
            else:
                search = self._conn.search(None, 'HEADER', 'MESSAGE-ID', '"' + msg['MESSAGE-ID'] + '"')
                if len(search[1][0]) > 0:
                    # log dupe
                    return False

        try:
            self._conn.append(imap_folder, imaplib.ParseFlags(b""), time.localtime(), msg.as_bytes())
            return True
        except UnicodeEncodeError as e:
            print("Sort of invalid message here, swallowing it:", e)
            return False
        except e:
            raise e


    def _assert_and_select_imap_folder(self, imap_folder):

        select_folder_result = self._conn.select(imap_folder)
        if select_folder_result[0] == "OK": return True

        if not self.auto_create_folders:
            print ("Imap's folder '%s' does not exist; not consuming message -- "%imap_folder)
            print ("You might consider configure this further i.e. tag_to_imap_folder or auto_create_folders")
            return False

        # attempts to create folder
        create_folder_result =  self._conn.create(imap_folder)
        if not create_folder_result[0] == "OK":
            print ("Tried to create an imap folder but something went wrong, not consuming the message; result: %s"%create_folder_result)
            return False

        select_folder_result = self._conn.select(imap_folder)
        if not select_folder_result[0] == "OK":
            print ("I couldn't select recently created folder %s, not consuming message."%imap_folder)
            return False

        return True



class FolderSink(Sink):

    folder = './'
    extension = 'eml'

    _effective_path = ''
    _next_file_no = 1

    def __init__(self, folder):
        self.folder = folder

    def start(self):
        self._effective_path = os.path.normpath(self.folder)
        if not os.path.exists(self.folder):
            os.makedirs(self._effective_path)
        files = os.listdir(self._effective_path)
        without_extensions = [ x[0:x.find('.')] for x in files ]
        only_numbers = [ (int)(x) for x in filter(lambda x:x.isdigit(), without_extensions)]
        if len(only_numbers) > 0:
            self._next_file_no = max(only_numbers)+1

    def close(self):
        pass

    def store(self, tag, msg):
        path = os.path.join(self._effective_path, "%i.%s"%(self._next_file_no, self.extension))
        f = open(path, 'w')
        f.write(msg.as_string())
        f.close()
        self._next_file_no += 1
        return True


