import logging

import musicpd

# Set logging to debug level
# it should log messages showing where defaults come from
logging.basicConfig(level=logging.DEBUG, format='%(levelname)-8s %(message)s')
log = logging.getLogger()

client = musicpd.MPDClient()
# use MPD_HOST/MPD_PORT env var if set else
# test ${XDG_RUNTIME_DIR}/mpd/socket for existence
# fallback to localhost:6600
# connect support host/port argument as well
client.connect()

status = client.status()
if status.get('state') == 'play':
    current_song_id = status.get('songid')
    current_song = client.playlistid(current_song_id)[0]
    log.info(f'Playing   : {current_song.get("file")}')
    next_song_id = status.get('nextsongid', None)
    if next_song_id:
        next_song = client.playlistid(next_song_id)[0]
        log.info(f'Next song : {next_song.get("file")}')
else:
    log.info('Not playing')

client.disconnect()
