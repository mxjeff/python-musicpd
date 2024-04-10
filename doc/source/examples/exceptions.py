"""client class dealing with all Exceptions
"""
import logging

import musicpd


# Wrap Exception decorator
def wrapext(func):
    """Decorator to wrap errors in musicpd.MPDError"""
    errors=(OSError, TimeoutError)
    into = musicpd.MPDError
    def w_func(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except errors as err:
            strerr = str(err)
            if hasattr(err, 'strerror'):
                if err.strerror:
                    strerr = err.strerror
            raise into(strerr) from err
    return w_func


class MyClient(musicpd.MPDClient):
    """Plain client inheriting from MPDClient"""

    def __init__(self):
        # Set logging to debug level
        logging.basicConfig(level=logging.DEBUG,
                format='%(levelname)-8s %(module)-10s %(message)s')
        self.log = logging.getLogger(__name__)
        super().__init__()

    @wrapext
    def __getattr__(self, cmd):
        """Wrapper around MPDClient calls for abstract overriding"""
        self.log.debug('cmd: %s', cmd)
        return super().__getattr__(cmd)


if __name__ == '__main__':
    cli = MyClient()
    # You can overrides host here or in init
    #cli.host = 'example.org'
    # Connect MPD server
    try:
        cli.connect()
        cli.currentsong()
        cli.stats()
    except musicpd.MPDError as error:
        cli.log.fatal(error)
    finally:
        cli.log.info('Disconnecting')
        try:
            # Tries to close the socket anyway
            cli.disconnect()
        except OSError:
            pass
