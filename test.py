#!/usr/bin/env python3
# coding: utf-8
# SPDX-FileCopyrightText: 2012-2021  kaliko <kaliko@azylum.org>
# SPDX-License-Identifier: LGPL-3.0-or-later
# pylint: disable=missing-docstring
"""
Test suite highly borrowed^Wsteal from python-mpd2 [0] project.

[0] https://github.com/Mic92/python-mpd2
"""


import itertools
import os
import types
import unittest
import unittest.mock as mock
import warnings

import musicpd


# show deprecation warnings
warnings.simplefilter('default')


TEST_MPD_HOST, TEST_MPD_PORT = ('example.com', 10000)


class testEnvVar(unittest.TestCase):

    def test_envvar(self):
        # mock "os.path.exists" here to ensure there are no socket in
        # XDG_RUNTIME_DIR/mpd or /run/mpd since with test defaults fallbacks
        # when :
        #   * neither MPD_HOST nor XDG_RUNTIME_DIR are not set
        #   * /run/mpd does not expose a socket
        with mock.patch('os.path.exists', return_value=False):
            os.environ.pop('MPD_HOST', None)
            os.environ.pop('MPD_PORT', None)
            client = musicpd.MPDClient()
            self.assertEqual(client.host, 'localhost')
            self.assertEqual(client.port, '6600')

            os.environ.pop('MPD_HOST', None)
            os.environ['MPD_PORT'] = '6666'
            client = musicpd.MPDClient()
            self.assertEqual(client.pwd, None)
            self.assertEqual(client.host, 'localhost')
            self.assertEqual(client.port, '6666')

        # Test password extraction
        os.environ['MPD_HOST'] = 'pa55w04d@example.org'
        client = musicpd.MPDClient()
        self.assertEqual(client.pwd, 'pa55w04d')
        self.assertEqual(client.host, 'example.org')

        # Test host alone
        os.environ['MPD_HOST'] = 'example.org'
        client = musicpd.MPDClient()
        self.assertFalse(client.pwd)
        self.assertEqual(client.host, 'example.org')

        # Test password extraction (no host)
        os.environ['MPD_HOST'] = 'pa55w04d@'
        with mock.patch('os.path.exists', return_value=False):
            client = musicpd.MPDClient()
        self.assertEqual(client.pwd, 'pa55w04d')
        self.assertEqual(client.host, 'localhost')

        # Test badly formatted MPD_HOST
        os.environ['MPD_HOST'] = '@'
        with mock.patch('os.path.exists', return_value=False):
            client = musicpd.MPDClient()
        self.assertEqual(client.pwd, None)
        self.assertEqual(client.host, 'localhost')

        # Test unix socket extraction
        os.environ['MPD_HOST'] = 'pa55w04d@/unix/sock'
        client = musicpd.MPDClient()
        self.assertEqual(client.host, '/unix/sock')

        # Test plain abstract socket extraction
        os.environ['MPD_HOST'] = '@abstract'
        client = musicpd.MPDClient()
        self.assertEqual(client.host, '@abstract')

        # Test password and abstract socket extraction
        os.environ['MPD_HOST'] = 'pass@@abstract'
        client = musicpd.MPDClient()
        self.assertEqual(client.pwd, 'pass')
        self.assertEqual(client.host, '@abstract')

        # Test unix socket fallback
        os.environ.pop('MPD_HOST', None)
        os.environ.pop('MPD_PORT', None)
        os.environ.pop('XDG_RUNTIME_DIR', None)
        with mock.patch('os.path.exists', return_value=True):
            client = musicpd.MPDClient()
            self.assertEqual(client.host, '/run/mpd/socket')
            os.environ['XDG_RUNTIME_DIR'] = '/run/user/1000'
            client = musicpd.MPDClient()
            self.assertEqual(client.host, '/run/user/1000/mpd/socket')

        os.environ.pop('MPD_HOST', None)
        os.environ.pop('MPD_PORT', None)
        os.environ['XDG_RUNTIME_DIR'] = '/run/user/1000/'
        with mock.patch('os.path.exists', return_value=True):
            client = musicpd.MPDClient()
            self.assertEqual(client.host, '/run/user/1000/mpd/socket')

        # Test MPD_TIMEOUT
        os.environ.pop('MPD_TIMEOUT', None)
        client = musicpd.MPDClient()
        self.assertEqual(client.mpd_timeout, musicpd.CONNECTION_TIMEOUT)
        os.environ['MPD_TIMEOUT'] = 'garbage'
        client = musicpd.MPDClient()
        self.assertEqual(client.mpd_timeout,
                         musicpd.CONNECTION_TIMEOUT,
                         'Garbage is silently ignore to use default value')
        os.environ['MPD_TIMEOUT'] = '42'
        client = musicpd.MPDClient()
        self.assertEqual(client.mpd_timeout, 42)


class TestMPDClient(unittest.TestCase):

    longMessage = True
    # last sync: musicpd 0.6.0 unreleased / Fri Feb 19 15:34:53 CET 2021
    commands = {
            # Status Commands
            'clearerror':         'nothing',
            'currentsong':        'object',
            'idle':               'list',
            'noidle':             None,
            'status':             'object',
            'stats':              'object',
            # Playback Option Commands
            'consume':            'nothing',
            'crossfade':          'nothing',
            'mixrampdb':          'nothing',
            'mixrampdelay':       'nothing',
            'random':             'nothing',
            'repeat':             'nothing',
            'setvol':             'nothing',
            'getvol':             'object',
            'single':             'nothing',
            'replay_gain_mode':   'nothing',
            'replay_gain_status': 'item',
            'volume':             'nothing',
            # Playback Control Commands
            'next':               'nothing',
            'pause':              'nothing',
            'play':               'nothing',
            'playid':             'nothing',
            'previous':           'nothing',
            'seek':               'nothing',
            'seekid':             'nothing',
            'seekcur':            'nothing',
            'stop':               'nothing',
            # Queue Commands
            'add':                'nothing',
            'addid':              'item',
            'clear':              'nothing',
            'delete':             'nothing',
            'deleteid':           'nothing',
            'move':               'nothing',
            'moveid':             'nothing',
            'playlist':           'playlist',
            'playlistfind':       'songs',
            'playlistid':         'songs',
            'playlistinfo':       'songs',
            'playlistsearch':     'songs',
            'plchanges':          'songs',
            'plchangesposid':     'changes',
            'prio':               'nothing',
            'prioid':             'nothing',
            'rangeid':            'nothing',
            'shuffle':            'nothing',
            'swap':               'nothing',
            'swapid':             'nothing',
            'addtagid':           'nothing',
            'cleartagid':         'nothing',
            # Stored Playlist Commands
            'listplaylist':       'list',
            'listplaylistinfo':   'songs',
            'listplaylists':      'playlists',
            'load':               'nothing',
            'playlistadd':        'nothing',
            'playlistclear':      'nothing',
            'playlistdelete':     'nothing',
            'playlistmove':       'nothing',
            'rename':             'nothing',
            'rm':                 'nothing',
            'save':               'nothing',
            # Database Commands
            'albumart':           'composite',
            'count':              'object',
            'getfingerprint':     'object',
            'find':               'songs',
            'findadd':            'nothing',
            'list':               'list',
            'listall':            'database',
            'listallinfo':        'database',
            'listfiles':          'database',
            'lsinfo':             'database',
            'readcomments':       'object',
            'readpicture':        'composite',
            'search':             'songs',
            'searchadd':          'nothing',
            'searchaddpl':        'nothing',
            'update':             'item',
            'rescan':             'item',
            # Mounts and neighbors
            'mount':              'nothing',
            'unmount':            'nothing',
            'listmounts':         'mounts',
            'listneighbors':      'neighbors',
            # Sticker Commands
            'sticker get':        'item',
            'sticker set':        'nothing',
            'sticker delete':     'nothing',
            'sticker list':       'list',
            'sticker find':       'songs',
            # Connection Commands
            'close':              None,
            'kill':               None,
            'password':           'nothing',
            'ping':               'nothing',
            'binarylimit':        'nothing',
            'tagtypes':           'list',
            'tagtypes disable':   'nothing',
            'tagtypes enable':    'nothing',
            'tagtypes clear':     'nothing',
            'tagtypes all':       'nothing',
            # Partition Commands
            'partition':          'nothing',
            'listpartitions':     'list',
            'newpartition':       'nothing',
            'delpartition':       'nothing',
            'moveoutput':         'nothing',
            # Audio Output Commands
            'disableoutput':      'nothing',
            'enableoutput':       'nothing',
            'toggleoutput':       'nothing',
            'outputs':            'outputs',
            'outputset':          'nothing',
            # Reflection Commands
            'config':             'object',
            'commands':           'list',
            'notcommands':        'list',
            'urlhandlers':        'list',
            'decoders':           'plugins',
            # Client to Client
            'subscribe':          'nothing',
            'unsubscribe':        'nothing',
            'channels':           'list',
            'readmessages':       'messages',
            'sendmessage':        'nothing',
        }

    def setUp(self):
        self.socket_patch = mock.patch('musicpd.socket')
        self.socket_mock = self.socket_patch.start()
        self.socket_mock.getaddrinfo.return_value = [range(5)]

        self.socket_mock.socket.side_effect = (
            lambda *a, **kw:
            # Create a new socket.socket() mock with default attributes,
            # each time we are calling it back (otherwise, it keeps set
            # attributes across calls).
            # That's probably what we want, since reconnecting is like
            # reinitializing the entire connection, and so, the mock.
            mock.MagicMock(name='socket.socket'))

        self.client = musicpd.MPDClient()
        self.client.connect(TEST_MPD_HOST, TEST_MPD_PORT)
        self.client._sock.reset_mock()
        self.MPDWillReturn('ACK don\'t forget to setup your mock\n')

    def tearDown(self):
        self.socket_patch.stop()

    def MPDWillReturn(self, *lines):
        # Return what the caller wants first, then do as if the socket was
        # disconnected.
        self.client._rfile.readline.side_effect = itertools.chain(
            lines, itertools.repeat(''))

    def MPDWillReturnBinary(self, lines):
        data = bytearray(b''.join(lines))

        def read(amount):
            val = bytearray()
            while amount > 0:
                amount -= 1
                # _ = data.pop(0)
                # print(hex(_))
                val.append(data.pop(0))
            return val

        def readline():
            val = bytearray()
            while not val.endswith(b'\x0a'):
                val.append(data.pop(0))
            return val
        self.client._rbfile.readline.side_effect = readline
        self.client._rbfile.read.side_effect = read

    def assertMPDReceived(self, *lines):
        self.client._wfile.write.assert_called_with(*lines)

    def test_metaclass_commands(self):
        """Controls client has at least commands as last synchronized in
        TestMPDClient.commands"""
        for cmd, ret in TestMPDClient.commands.items():
            self.assertTrue(hasattr(self.client, cmd), msg='cmd "{}" not available!'.format(cmd))
            if ' ' in cmd:
                self.assertTrue(hasattr(self.client, cmd.replace(' ', '_')))

    def test_fetch_nothing(self):
        self.MPDWillReturn('OK\n')
        self.assertIsNone(self.client.ping())
        self.assertMPDReceived('ping\n')

    def test_fetch_list(self):
        self.MPDWillReturn('OK\n')
        self.assertIsInstance(self.client.list('album'), list)
        self.assertMPDReceived('list "album"\n')

    def test_fetch_item(self):
        self.MPDWillReturn('updating_db: 42\n', 'OK\n')
        self.assertIsNotNone(self.client.update())

    def test_fetch_object(self):
        # XXX: _read_objects() doesn't wait for the final OK
        self.MPDWillReturn('volume: 63\n', 'OK\n')
        status = self.client.status()
        self.assertMPDReceived('status\n')
        self.assertIsInstance(status, dict)

        # XXX: _read_objects() doesn't wait for the final OK
        self.MPDWillReturn('OK\n')
        stats = self.client.stats()
        self.assertMPDReceived('stats\n')
        self.assertIsInstance(stats, dict)

        output = ['outputid: 0\n',
                  'outputname: default detected output\n',
                  'plugin: sndio\n',
                  'outputenabled: 1\n']
        self.MPDWillReturn(*output, 'OK\n')
        outputs = self.client.outputs()
        self.assertMPDReceived('outputs\n')
        self.assertIsInstance(outputs, list)
        self.assertEqual([{'outputid': '0', 'outputname': 'default detected output', 'plugin': 'sndio', 'outputenabled': '1'}], outputs)

    def test_fetch_songs(self):
        self.MPDWillReturn('file: my-song.ogg\n', 'Pos: 0\n', 'Id: 66\n', 'OK\n')
        playlist = self.client.playlistinfo()

        self.assertMPDReceived('playlistinfo\n')
        self.assertIsInstance(playlist, list)
        self.assertEqual(1, len(playlist))
        e = playlist[0]
        self.assertIsInstance(e, dict)
        self.assertEqual('my-song.ogg', e['file'])
        self.assertEqual('0', e['pos'])
        self.assertEqual('66', e['id'])

    def test_send_and_fetch(self):
        self.MPDWillReturn('volume: 50\n', 'OK\n')
        result = self.client.send_status()
        self.assertEqual(None, result)
        self.assertMPDReceived('status\n')

        status = self.client.fetch_status()
        self.assertEqual(1, self.client._wfile.write.call_count)
        self.assertEqual({'volume': '50'}, status)

    def test_iterating(self):
        self.MPDWillReturn('file: my-song.ogg\n', 'Pos: 0\n', 'Id: 66\n',
                           'file: my-song.ogg\n', 'Pos: 0\n', 'Id: 66\n', 'OK\n')
        self.client.iterate = True
        playlist = self.client.playlistinfo()
        self.assertMPDReceived('playlistinfo\n')
        self.assertIsInstance(playlist, types.GeneratorType)
        self.assertTrue(self.client._iterating)
        for song in playlist:
            self.assertRaises(musicpd.IteratingError, self.client.status)
            self.assertIsInstance(song, dict)
            self.assertEqual('my-song.ogg', song['file'])
            self.assertEqual('0', song['pos'])
            self.assertEqual('66', song['id'])
        self.assertFalse(self.client._iterating)

    def test_noidle(self):
        self.MPDWillReturn('OK\n') # nothing changed after idle-ing
        self.client.send_idle()
        self.MPDWillReturn('OK\n') # nothing changed after noidle
        self.assertEqual(self.client.noidle(), [])
        self.assertMPDReceived('noidle\n')
        self.MPDWillReturn('volume: 50\n', 'OK\n')
        self.client.status()
        self.assertMPDReceived('status\n')

    def test_noidle_while_idle_started_sending(self):
        self.MPDWillReturn('OK\n') # nothing changed after idle
        self.client.send_idle()
        self.MPDWillReturn('CHANGED: player\n', 'OK\n')  # noidle response
        self.assertEqual(self.client.noidle(), ['player'])
        self.MPDWillReturn('volume: 50\n', 'OK\n')
        status = self.client.status()
        self.assertMPDReceived('status\n')
        self.assertEqual({'volume': '50'}, status)

    def test_throw_when_calling_noidle_withoutidling(self):
        self.assertRaises(musicpd.CommandError, self.client.noidle)
        self.client.send_status()
        self.assertRaises(musicpd.CommandError, self.client.noidle)

    def test_send_noidle_calls_noidle(self):
        self.MPDWillReturn('OK\n') # nothing changed after idle
        self.client.send_idle()
        self.client.send_noidle()
        self.assertMPDReceived('noidle\n')

    def test_client_to_client(self):
        self.MPDWillReturn('OK\n')
        self.assertIsNone(self.client.subscribe("monty"))
        self.assertMPDReceived('subscribe "monty"\n')

        self.MPDWillReturn('channel: monty\n', 'OK\n')
        channels = self.client.channels()
        self.assertMPDReceived('channels\n')
        self.assertEqual(['monty'], channels)

        self.MPDWillReturn('OK\n')
        self.assertIsNone(self.client.sendmessage('monty', 'SPAM'))
        self.assertMPDReceived('sendmessage "monty" "SPAM"\n')

        self.MPDWillReturn('channel: monty\n', 'message: SPAM\n', 'OK\n')
        msg = self.client.readmessages()
        self.assertMPDReceived('readmessages\n')
        self.assertEqual(msg, [{'channel': 'monty', 'message': 'SPAM'}])

        self.MPDWillReturn('OK\n')
        self.assertIsNone(self.client.unsubscribe('monty'))
        self.assertMPDReceived('unsubscribe "monty"\n')

        self.MPDWillReturn('OK\n')
        channels = self.client.channels()
        self.assertMPDReceived('channels\n')
        self.assertEqual([], channels)

    def test_ranges_in_command_args(self):
        self.MPDWillReturn('OK\n')
        self.client.playlistinfo((10,))
        self.assertMPDReceived('playlistinfo 10:\n')

        self.MPDWillReturn('OK\n')
        self.client.playlistinfo(('10',))
        self.assertMPDReceived('playlistinfo 10:\n')

        self.MPDWillReturn('OK\n')
        self.client.playlistinfo((10, 12))
        self.assertMPDReceived('playlistinfo 10:12\n')

        self.MPDWillReturn('OK\n')
        self.client.rangeid(())
        self.assertMPDReceived('rangeid :\n')

        for arg in [(10, 't'), (10, 1, 1), (None,1)]:
            self.MPDWillReturn('OK\n')
            with self.assertRaises(musicpd.CommandError):
                self.client.playlistinfo(arg)

    def test_numbers_as_command_args(self):
        self.MPDWillReturn('OK\n')
        self.client.find('file', 1)
        self.assertMPDReceived('find "file" "1"\n')

    def test_commands_without_callbacks(self):
        self.MPDWillReturn('\n')
        self.client.close()
        self.assertMPDReceived('close\n')

        # XXX: what are we testing here?
        self.client._reset()
        self.client.connect(TEST_MPD_HOST, TEST_MPD_PORT)

    def test_connection_lost(self):
        # Simulate a connection lost: the socket returns empty strings
        self.MPDWillReturn('')

        with self.assertRaises(musicpd.ConnectionError):
            self.client.status()

        # consistent behaviour
        # solves <https://github.com/Mic92/python-mpd2/issues/11> (also present
        # in python-mpd)
        with self.assertRaises(musicpd.ConnectionError):
            self.client.status()

        self.assertIs(self.client._sock, None)

    def test_parse_sticker_get_no_sticker(self):
        self.MPDWillReturn('ACK [50@0] {sticker} no such sticker\n')
        self.assertRaises(musicpd.CommandError,
                          self.client.sticker_get, 'song', 'baz', 'foo')

    def test_parse_sticker_list(self):
        self.MPDWillReturn('sticker: foo=bar\n', 'sticker: lom=bok\n', 'OK\n')
        res = self.client.sticker_list('song', 'baz')
        self.assertEqual(['foo=bar', 'lom=bok'], res)

        # Even with only one sticker, we get a dict
        self.MPDWillReturn('sticker: foo=bar\n', 'OK\n')
        res = self.client.sticker_list('song', 'baz')
        self.assertEqual(['foo=bar'], res)

    def test_albumart(self):
        # here is a 34 bytes long data
        data = bytes('\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01'
                     '\x00\x01\x00\x00\xff\xdb\x00C\x00\x05\x03\x04',
                     encoding='utf8')
        read_lines = [b'size: 42\nbinary: 34\n', data, b'\nOK\n']
        self.MPDWillReturnBinary(read_lines)
        # Reading albumart / offset 0 should return the data
        res = self.client.albumart('muse/Raised Fist/2002-Dedication/', 0)
        self.assertEqual(res.get('data'), data)

    def test_reading_binary(self):
        # readpicture when there are no picture returns empty object
        self.MPDWillReturnBinary([b'OK\n'])
        res = self.client.readpicture('muse/Raised Fist/2002-Dedication/', 0)
        self.assertEqual(res, {})

    def test_command_list(self):
        self.MPDWillReturn('updating_db: 42\n',
                           f'{musicpd.NEXT}\n',
                           'repeat: 0\n',
                           'random: 0\n',
                           f'{musicpd.NEXT}\n',
                           f'{musicpd.NEXT}\n',
                           'OK\n')
        self.client.command_list_ok_begin()
        self.client.update()
        self.client.status()
        self.client.repeat(1)
        self.client.command_list_end()
        self.assertMPDReceived('command_list_end\n')

    def test_two_word_commands(self):
        self.MPDWillReturn('OK\n')
        self.client.tagtypes_clear()
        self.assertMPDReceived('tagtypes clear\n')
        self.MPDWillReturn('OK\n')
        with self.assertRaises(AttributeError):
            self.client.foo_bar()

class testConnection(unittest.TestCase):

    def test_exposing_fileno(self):
        with mock.patch('musicpd.socket') as socket_mock:
            sock = mock.MagicMock(name='socket')
            socket_mock.socket.return_value = sock
            cli = musicpd.MPDClient()
            cli.connect()
            cli.fileno()
            cli._sock.fileno.assert_called_with()

    def test_connect_abstract(self):
        os.environ['MPD_HOST'] = '@abstract'
        with mock.patch('musicpd.socket') as socket_mock:
            sock = mock.MagicMock(name='socket')
            socket_mock.socket.return_value = sock
            cli = musicpd.MPDClient()
            cli.connect()
            sock.connect.assert_called_with('\0abstract')

    def test_connect_unix(self):
        os.environ['MPD_HOST'] = '/run/mpd/socket'
        with mock.patch('musicpd.socket') as socket_mock:
            sock = mock.MagicMock(name='socket')
            socket_mock.socket.return_value = sock
            cli = musicpd.MPDClient()
            cli.connect()
            sock.connect.assert_called_with('/run/mpd/socket')


class testException(unittest.TestCase):

    def test_CommandError_on_newline(self):
        os.environ['MPD_HOST'] = '/run/mpd/socket'
        with mock.patch('musicpd.socket') as socket_mock:
            sock = mock.MagicMock(name='socket')
            socket_mock.socket.return_value = sock
            cli = musicpd.MPDClient()
            cli.connect()
            with self.assertRaises(musicpd.CommandError):
                cli.find('(album == "foo\nbar")')

class testContextManager(unittest.TestCase):

    def test_enter_exit(self):
        os.environ['MPD_HOST'] = '@abstract'
        with mock.patch('musicpd.socket') as socket_mock:
            sock = mock.MagicMock(name='socket')
            socket_mock.socket.return_value = sock
            cli = musicpd.MPDClient()
            with cli as c:
                sock.connect.assert_called_with('\0abstract')
                sock.close.assert_not_called()
            sock.close.assert_called()

class testRange(unittest.TestCase):

    def test_range(self):
        tests = [
                ((),          ':'),
                ((None,None), ':'),
                (('',''),     ':'),
                (('',),       ':'),
                ((42,42),     '42:42'),
                ((42,),       '42:'),
                (('42',),     '42:'),
                (('42',None), '42:'),
                (('42',''),   '42:'),
        ]
        for tpl, result in tests:
            self.assertEqual(str(musicpd.Range(tpl)), result)
        with self.assertRaises(musicpd.CommandError):
            #CommandError: Integer expected to start the range: (None, 42)
            musicpd.Range((None,'42'))
        with self.assertRaises(musicpd.CommandError):
            # CommandError: Not an integer: "foo"
            musicpd.Range(('foo',))
        with self.assertRaises(musicpd.CommandError):
            # CommandError: Wrong range: 42 > 41
            musicpd.Range(('42',41))
        with self.assertRaises(musicpd.CommandError):
            # CommandError: Wrong range: 42 > 41
            musicpd.Range(('42','42','42'))


if __name__ == '__main__':
    unittest.main()
