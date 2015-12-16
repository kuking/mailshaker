# -*- Encoding: UTF-8 -*-
"""
    MailShaker library
"""

import logging

from .auth import *
from .taps import *
from .sinks import *

logging.basicConfig(level=logging.DEBUG)

class MailShaker:
    """ Base class for Shaking mails, should specialise and configure. """

    name = ''
    taps = []
    sinks = []

    def __init__(self, name = 'Default Shaking config Name', taps = [], sinks = []):
        self.shake_name = name
        self.taps = taps
        self.sinks = sinks

    def shake(self):
        if not self.taps:
            sys.exit("I'm sorry you should provide at least a Tap")
        if not self.sinks:
            sys.exit("I'm sorry you should provide at least a Sink")

        logging.info("Starting '%s' .."%self.name)

        for tap in self.taps:
            tap.start()
        for sink in self.sinks:
            sink.start()

        for tap in self.taps:
            for (tag, msg_id, msg) in tap.selected_messages():

                stored = False
                for sink in self.sinks:
                    stored |= sink.store(tag, msg)

                if stored:
                    logging.info("%s msg_id %s with tag %s has been stored", tap.name, msg_id, tag)
                else:
                    logging.info("%s msg_id %s with tag %s has been ignored by all sinks :(", tap.name, msg_id, tag)

                if tap.do_move:
                    logging.info("%s msg_id %s deleting at source as it has been stored by at least one tap"%(tap.name, msg_id))
                    tap.delete(msg_id)

        logging.info("All messages processed, clossing taps and sinks ...")

        for tap in self.taps:
            tap.close()
        for sink in self.sinks:
            sink.close()

        logging.info("Finished successfully")





