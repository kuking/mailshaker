# MailShaker
Moves emails around between pops, imaps, and file systems. Because it is quicker than learning procmail.

## How it works?
It is a bit like 'map-reduce' (ok, I'm overstretching it a bit).

taps -> sends emails to -> sinks

You can have multiple taps, and multiple sinks.
A tap will assign one 'tag' to each email it sources, i.e. "My favourite Mailing list", "uncle", "default", etc.
Each sink will receive each message with its corresponding tag and decide to store or ignore it.

```python
from mailshaker import *

class MyPopTap (Pop3Tap):
    url = 'pop3+ssl://pop.mail.yahoo.com:995/'
    credential = CryptedUserPass('username', 'gpg2:yahoo-pass.key.asc')
    
    def select_and_tag(self, msg):
        if msg['List-Id'] == '<my.favourite@list.com>': return "FavList"
        return "Default"
        
class MyImapSink(Imap4Sink):
    url = 'imap4+ssl://mail.example.com:993'
    credential = NakedUserPass('username', 'password')
    
    def tag_to_imap_folder(self, tag):
      if tag == "FavList": return "Lists.My_Favourite_List"
      return "INBOX"

MailShaker('My First Shake', [MyPopTap()], [MyImapSink]).shake()
```
