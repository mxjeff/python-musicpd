import sys
import logging

import musicpd

# Set logging to debug level
logging.basicConfig(level=logging.DEBUG, format='%(levelname)-8s %(message)s')

client = musicpd.MPDClient()
try:
    client.connect(host='example.lan')
    client.password('secret')
    client.status()
except musicpd.MPDError as err:
    print(f'An error occured: {err}')
finally:
    client.disconnect()
