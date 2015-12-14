# MailShaker
Moves emails around between POP3s, IMAP4s, Maildirs, etc. <i>Why? Because it is quicker than learning procmail.</i>

It can modify email on the fly and apply complex logics; it is configured via a DSL facilitating customisation and complex logics.


## How it works?
It is a bit like 'map-reduce' (ok, I'm overstretching it a bit).

| Source  |  Shake                | Destination |
|---------|:---------------------:|------------:|
| taps    | -> sends emails to -> | sinks       |

You can have multiple taps, and multiple sinks.

A tap will set one 'tag' to each email it sources, i.e. "My favourite Mailing list", "uncle", "default", etc.
Each sink will receive each message with its corresponding tag and decide to store or ignore it. On the simpler case
the tag can be the destination folder, but in complex scenarios this enables complex business rules.

Typical configuration, downloads from a POP3 server, stores into multiple IMAP4 folders dependning on a mailing list:

```python
from mailshaker import *

class MyPopTap (Pop3Tap):
    url = 'pop3+ssl://pop.mail.yahoo.com:995/'
    credential = CryptedUserPass('username', 'gpg2:yahoo-pass.key.asc')

    def select_and_tag(self, msg):
        if msg['List-Id'] == '<my.favourite@list.com>': return 'Lists.My_Favourite_List'
        return 'INBOX'


class MyImapSink(Imap4Sink):
    url = 'imap4+ssl://mail.example.com:993'
    credential = NakedUserPass('username', 'password')


MailShaker('My First Shake', [MyPopTap()], [MyImapSink()]).shake()
```

It can be configured to behave in more complex ways, i.e. by having another level of logic in the imap Sink via
```tag_to_imap_folder``` method.
This example will download emails from two different pop3 accounts. One receiving standard inbox emails and a mailing
list and a second account likely to receive spam, so tagging all the emails coming from it as 'Spammy';
it will remove all the sucessfully stored messages from the pop accounts ```do_move = True```. Finally, it will store
an extra copy of every email under ```/tmp/sink``` (Maildir format).

```python
from mailshaker import *

class MyPopTap (Pop3Tap):
    url = 'pop3+ssl://pop.mail.yahoo.com:995/'
    credential = CryptedUserPass('username', 'gpg2:yahoo-pass.key.asc')
    do_move = True
    
    def select_and_tag(self, msg):
        if msg['List-Id'] == '<my.favourite@list.com>': return "FavList"
        return "Default"


class MySpammyPop (Pop3Tap):
    url = 'pop3+ssl://pop.example.com:995/'
    credential = CryptedUserPass('user', 'gpg2:example-pass.key.asc')
    do_move = True

    def select_and_tag(self, msg):
        return 'Spammy'


class MyImapSink(Imap4Sink):
    rl = 'imap4+ssl://mail.example.com:993'
    credential = NakedUserPass('username', 'password')
    
    def tag_to_imap_folder(self, tag):
      if tag == 'FavList': return 'Lists.My_Favourite_List'
      if tag == 'Spammy': return 'Likely_Spam'
      return 'INBOX'


# The following class be inlined in the MailShaker constructor with anonymous class.
class MyFolderSink(FolderSink):
    folder = '/tmp/sink'


MailShaker('My Second Shake', [MyPopTap()], [MyImapSink(), MyFolderSink()] ).shake()
```

or even simpler, the tag is the imap4 folder (for simplicity if it suits you):


## Status
This is far from being finish and full documented open source project. Still, it can be useful for some people,
I do use it on daily basis. But to certain extend, it does very much what I need. i.e. there are is no SMTP sink or an
IMAP4 tap (if you have some spare time...).


