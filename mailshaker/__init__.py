# -*- Encoding: UTF-8 -*-
"""
    MailShaker library
"""

from .auth import *
from .taps import *
from .sinks import *

class MailShaker:
    """ Base class for Shaking mails, should specialise and configure. """

    shake_name = ''
    taps = []
    sinks = []

    def __init__(self, shake_name = 'Default Shaking config Name', taps = [], sinks = []):
        self.shake_name = shake_name
        self.taps = taps
        self.sinks = sinks

    def shake(self):
        if not self.taps:
            sys.exit("I'm sorry you should provide at least a Tap")
        if not self.sinks:
            sys.exit("I'm sorry you should provide at least a Sink")

        print ("Starting '%s' .."%self.shake_name)
        print (" o - Tap is discarding the message")
        print (" O - All sinks discarded the message")
        print (" D - Delete at tap")
        print (" S - Message stored")

        for tap in self.taps:
            tap.start()
        for sink in self.sinks:
            sink.start()

        for tap in self.taps:
            for (tag, msg_id, msg) in tap.selected_messages():

                stored = False
                for sink in self.sinks:
                    stored |= sink.store(tag, msg)
                sys.stdout.write('S' if stored else 'O')
                sys.stdout.flush()

                if tap.do_move:
                    tap.delete(msg_id)
                    sys.stdout.write('D')
                    sys.stdout.flush()

        print()

        for tap in self.taps:
            tap.close()
        for sink in self.sinks:
            sink.close()





