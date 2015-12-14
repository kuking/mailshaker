import pytest
from unittest.mock import MagicMock
from unittest.mock import patch

import imaplib
import poplib
from mailshaker import *

def given_imap_mock():
    mock = imaplib.IMAP4_SSL()
    mock.login = MagicMock(return_value=['OK'])
    return mock

def given_a_nakeduserpass():
    return NakedUserPass('user##', 'pass##')

@patch('imaplib.IMAP4_SSL')
def test_nakeduserpass_login_into_imap4ssl(imap4ssl):
    imap4ssl.login = MagicMock(return_value=['OK'])
    imap4ssl.__class__.__name__ = "IMAP4_SSL"
    under_test = given_a_nakeduserpass()

    under_test.do_login(imap4ssl)

    imap4ssl.login.assert_called_with('user##', 'pass##')

@patch('poplib.POP3_SSL')
def test_nakeduserpass_login_into_pop3ssl(pop3ssl):
    pop3ssl.user = MagicMock()
    pop3ssl.pass_ = MagicMock(return_value='OK')
    pop3ssl.__class__.__name__ = "POP3_SSL"
    under_test = given_a_nakeduserpass()

    under_test.do_login(pop3ssl)

    pop3ssl.user.assert_called_with('user##')
    pop3ssl.pass_.assert_called_with('pass##')

def test_nakeduserpass_unknown_client():
    under_test = given_a_nakeduserpass()
    try:
        under_test.do_login("this is not a client object")
        fail("this should have raised NotImplementedError")
    except NotImplementedError as e:
        assert e.args[0] == "I don't know how to log-in into client: str"

