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
        if msg['List-Id'] == '<my.favourite@list.com>': return "Lists.My_Favourite_List"
        return "INBOX"


class MyImapSink(Imap4Sink):
    url = 'imap4+ssl://mail.example.com:993'
    credential = NakedUserPass('username', 'password')


MailShaker('My First Shake', [MyPopTap()], [MyImapSink()]).shake()
```

It can be easily made it more complex, i.e. by having another level of logic in the Sink via ```tag_to_imap_folder``` method.
This example will also remove emails from the pop server once it has been stored in the imap server. It will also store
all the received emails in sequential files under ```/tmp/sink``` (Maildir format).

```python
from mailshaker import *

class MyPopTap (Pop3Tap):
    url = 'pop3+ssl://pop.mail.yahoo.com:995/'
    credential = CryptedUserPass('username', 'gpg2:yahoo-pass.key.asc')
    do_move = True
    
    def select_and_tag(self, msg):
        if msg['List-Id'] == '<my.favourite@list.com>': return "FavList"
        return "Default"


class MyImapSink(Imap4Sink):
    rl = 'imap4+ssl://mail.example.com:993'
    credential = NakedUserPass('username', 'password')
    
    def tag_to_imap_folder(self, tag):
      if tag == "FavList": return "Lists.My_Favourite_List"
      return "INBOX"

# The following class be inlined in the MailShaker constructor with anonymous class.
class MyFolderSink(FolderSink):
    folder = '/tmp/sink'

MailShaker('My Second Shake', [MyPopTap()], [MyImapSink(), MyFolderSink()] ).shake()
```

or even simpler, the tag is the imap4 folder (for simplicity if it suits you):


## Status
This is far from a complete and full documented open source project.
Still, it can be useful for some people, I do use it on daily basis.
But to be honest, it does very much what I need and not much more.
i.e. there are is not an SMTP sink or a IMAP4 tap (if you have some spare time...).

## Why MailShaker?


