#!/usr/bin/python3
"""python3 ./doc/extract_supported_commands.py > ./doc/source/_commands.rst
"""
import pathlib
import re
import sys
sys.path.insert(0,pathlib.Path('.').absolute().as_posix())
import musicpd

START = 'self._commands = {'
END = '}'
LATEST_PROTOCOL = 'https://mpd.readthedocs.io/en/latest/protocol.html'
TYPE_MAPPING = {
        'fetch_nothing': 'None',
        'fetch_object': 'dict',
        'fetch_list': 'list',
        'fetch_item': 'str',
        'fetch_playlist': 'list',
        'fetch_songs': 'list[dict]',
        'fetch_changes': 'list[dict]',
        'fetch_composite': 'dict',
        'fetch_playlists': 'dict',
        'fetch_database': 'list[dict]',
        'fetch_mounts': 'list[dict]',
        'fetch_neighbors': 'list[dict]',
        'fetch_outputs': 'list[dict]',
        'fetch_plugins': 'list[dict]',
        'fetch_messages': 'list[dict]',
}


def find_start(fd):
    line = fd.readline()
    while START not in line:
        line = fd.readline()
        if not line:
            break
    if not line:
        print('Reach end of file!', file=sys.stderr)
        sys.exit(1)


def main():
    with open('musicpd.py', 'r', encoding='utf-8') as fd:
        # fast forward to find self._commands
        find_start(fd)
        cmd_patt = '"(?P<command>.*)":'
        cmd_patt = r'"(?P<command>.*?)": +self\._(?P<obj>.+?),'
        tit_patt = '# (?P<title>[^#]+?) ?# ?(?P<anchor>.+?)$'
        cmd_regex = re.compile(cmd_patt)
        tit_regex = re.compile(tit_patt)
        print(f'Below the commands list last updated for v{musicpd.VERSION}.')
        # Now extract supported commands
        line = 'foo'
        while line and END not in line:
            line = fd.readline()
            cmd = cmd_regex.search(line)
            tit = tit_regex.search(line)
            if tit:
                print(f'\n{tit[1]}')
                print('^'*len(tit[1]))
                print(f'\nProtocol documentation: `{tit[1]} <{LATEST_PROTOCOL}#{tit[2]}>`_\n')
            if cmd:
                print(f'* **{cmd[1]}** -> {TYPE_MAPPING.get(cmd[2], "ukn")}')


if __name__ == '__main__':
    main()
