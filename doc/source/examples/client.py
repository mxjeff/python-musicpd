"""Plain client class
"""
import logging
import select
import sys

import musicpd


class MyClient(musicpd.MPDClient):
    """Plain client inheriting from MPDClient"""

    def __init__(self):
        # Set logging to debug level
        logging.basicConfig(level=logging.DEBUG,
                            format='%(levelname)-8s %(module)-8s %(message)s')
        self.log = logging.getLogger(__name__)
        super().__init__()
        # Set host/port/password after init to overrides defaults
        # self.host = 'example.org'
        # self.port = 4242
        # self.pwd = 'secret'

    def connect(self):
        """Overriding explicitly MPDClient.connect()"""
        try:
            super().connect(host=self.host, port=self.port)
            if hasattr(self, 'pwd') and self.pwd:
                self.password(self.pwd)
        except musicpd.ConnectionError as err:
            # Catch socket error
            self.log.error('Failed to connect: %s', err)
            sys.exit(42)

    def _wait_for_changes(self, callback):
        select_timeout = 10  # second
        while True:
            self.send_idle()  # use send_ API to avoid blocking on read
            _read, _, _ = select.select([self], [], [], select_timeout)
            if _read:  # tries to read response
                ret = self.fetch_idle()
                # do something
                callback(ret)
            else:  # cancels idle
                self.noidle()

    def callback(self, *args):
        """Method launch on MPD event, cf. monitor method"""
        self.log.info('%s', args)

    def monitor(self):
        """Continuously monitor MPD activity.
        Launch callback method on event.
        """
        try:
            self._wait_for_changes(self.callback)
        except (OSError, musicpd.MPDError) as err:
            self.log.error('%s: Something went wrong: %s',
                           type(err).__name__, err)

if __name__ == '__main__':
    cli = MyClient()
    # You can overrides host here or in init
    #cli.host = 'example.org'
    # Connect MPD server
    try:
        cli.connect()
    except musicpd.ConnectionError as err:
        cli.log.error(err)

    # Monitor MPD changes, blocking/timeout idle approach
    try:
        cli.socket_timeout =  20 # seconds
        ret = cli.idle()
        cli.log.info('Leaving idle, got: %s', ret)
    except TimeoutError as err:
        cli.log.info('Nothing occured the last %ss', cli.socket_timeout)

    # Reset connection
    try:
        cli.socket_timeout = None
        cli.disconnect()
        cli.connect()
    except musicpd.ConnectionError as err:
        cli.log.error(err)

    # Monitor MPD changes, non blocking idle approach
    try:
        cli.monitor()
    except KeyboardInterrupt as err:
        cli.log.info(type(err).__name__)
        cli.send_noidle()
        cli.disconnect()

