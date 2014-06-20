#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test suite highly borrowed^Wsteal from python-mpd2 [0] project.

[0] https://github.com/Mic92/python-mpd2
"""


import itertools
import sys
import types
import unittest
import warnings

import musicpd

try:
    import unittest.mock as mock
except ImportError:
    try:
        import mock
    except ImportError:
        print("Please install mock from PyPI to run tests!")
        sys.exit(1)

# show deprecation warnings
warnings.simplefilter('default')


TEST_MPD_HOST, TEST_MPD_PORT = ('example.com', 10000)


class TestMPDClient(unittest.TestCase):

    longMessage = True
    # last sync: musicpd 0.4.0
    commands = {
            # Status Commands
            "clearerror":         "nothing",
            "currentsong":        "object",
            "idle":               "list",
            "noidle":             None,
            "status":             "object",
            "stats":              "object",
            # Playback Option Commands
            "consume":            "nothing",
            "crossfade":          "nothing",
            "mixrampdb":          "nothing",
            "mixrampdelay":       "nothing",
            "random":             "nothing",
            "repeat":             "nothing",
            "setvol":             "nothing",
            "single":             "nothing",
            "replay_gain_mode":   "nothing",
            "replay_gain_status": "item",
            "volume":             "nothing",
            # Playback Control Commands
            "next":               "nothing",
            "pause":              "nothing",
            "play":               "nothing",
            "playid":             "nothing",
            "previous":           "nothing",
            "seek":               "nothing",
            "seekid":             "nothing",
            "seekcur":            "nothing",
            "stop":               "nothing",
            # Playlist Commands
            "add":                "nothing",
            "addid":              "item",
            "clear":              "nothing",
            "delete":             "nothing",
            "deleteid":           "nothing",
            "move":               "nothing",
            "moveid":             "nothing",
            "playlist":           "playlist",
            "playlistfind":       "songs",
            "playlistid":         "songs",
            "playlistinfo":       "songs",
            "playlistsearch":     "songs",
            "plchanges":          "songs",
            "plchangesposid":     "changes",
            "shuffle":            "nothing",
            "swap":               "nothing",
            "swapid":             "nothing",
            # Stored Playlist Commands
            "listplaylist":       "list",
            "listplaylistinfo":   "songs",
            "listplaylists":      "playlists",
            "load":               "nothing",
            "playlistadd":        "nothing",
            "playlistclear":      "nothing",
            "playlistdelete":     "nothing",
            "playlistmove":       "nothing",
            "rename":             "nothing",
            "rm":                 "nothing",
            "save":               "nothing",
            # Database Commands
            "count":              "object",
            "find":               "songs",
            "findadd":            "nothing",
            "list":               "list",
            "listall":            "database",
            "listallinfo":        "database",
            "lsinfo":             "database",
            "search":             "songs",
            "searchadd":          "nothing",
            "searchaddpl":        "nothing",
            "update":             "item",
            "rescan":             "item",
            "readcomments":       "object",
            # Sticker Commands
            "sticker get":        "item",
            "sticker set":        "nothing",
            "sticker delete":     "nothing",
            "sticker list":       "list",
            "sticker find":       "songs",
            # Connection Commands
            "close":              None,
            "kill":               None,
            "password":           "nothing",
            "ping":               "nothing",
            # Audio Output Commands
            "disableoutput":      "nothing",
            "enableoutput":       "nothing",
            "toggleoutput":       "nothing",
            "outputs":            "outputs",
            # Reflection Commands
            "commands":           "list",
            "notcommands":        "list",
            "tagtypes":           "list",
            "urlhandlers":        "list",
            "decoders":           "plugins",
            # Client to Client
            "subscribe":          "nothing",
            "unsubscribe":        "nothing",
            "channels":           "list",
            "readmessages":       "messages",
            "sendmessage":        "nothing",
        }

    def setUp(self):
        self.socket_patch = mock.patch("musicpd.socket")
        self.socket_mock = self.socket_patch.start()
        self.socket_mock.getaddrinfo.return_value = [range(5)]

        self.socket_mock.socket.side_effect = (
            lambda *a, **kw:
            # Create a new socket.socket() mock with default attributes,
            # each time we are calling it back (otherwise, it keeps set
            # attributes across calls).
            # That's probably what we want, since reconnecting is like
            # reinitializing the entire connection, and so, the mock.
            mock.MagicMock(name="socket.socket"))

        self.client = musicpd.MPDClient()
        self.client.connect(TEST_MPD_HOST, TEST_MPD_PORT)
        self.client._sock.reset_mock()
        self.MPDWillReturn("ACK don't forget to setup your mock\n")

    def tearDown(self):
        self.socket_patch.stop()

    def MPDWillReturn(self, *lines):
        # Return what the caller wants first, then do as if the socket was
        # disconnected.
        self.client._rfile.readline.side_effect = itertools.chain(
            lines, itertools.repeat(''))

    def assertMPDReceived(self, *lines):
        self.client._wfile.write.assert_called_with(*lines)

    def test_metaclass_commands(self):
        for cmd, ret in TestMPDClient.commands.items():
            self.assertTrue(hasattr(self.client, cmd), msg='fails for{}'.format(cmd))
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

    def test_fetch_songs(self):
        self.MPDWillReturn("file: my-song.ogg\n", "Pos: 0\n", "Id: 66\n", "OK\n")
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
        self.MPDWillReturn("volume: 50\n", "OK\n")
        result = self.client.send_status()
        self.assertEqual(None, result)
        self.assertMPDReceived('status\n')

        status = self.client.fetch_status()
        self.assertEqual(1, self.client._wfile.write.call_count)
        self.assertEqual({'volume': '50'}, status)

    def test_iterating(self):
        self.MPDWillReturn("file: my-song.ogg\n", "Pos: 0\n", "Id: 66\n", "OK\n")
        self.client.iterate = True
        playlist = self.client.playlistinfo()
        self.assertMPDReceived('playlistinfo\n')
        self.assertIsInstance(playlist, types.GeneratorType)
        for song in playlist:
            self.assertIsInstance(song, dict)
            self.assertEqual('my-song.ogg', song['file'])
            self.assertEqual('0', song['pos'])
            self.assertEqual('66', song['id'])

    def test_noidle(self):
        self.MPDWillReturn('OK\n') # nothing changed after idle-ing
        self.client.send_idle()
        self.MPDWillReturn('OK\n') # nothing changed after noidle
        self.assertEqual(self.client.noidle(), [])
        self.assertMPDReceived('noidle\n')
        self.MPDWillReturn("volume: 50\n", "OK\n")
        self.client.status()
        self.assertMPDReceived('status\n')

    def test_noidle_while_idle_started_sending(self):
        self.MPDWillReturn('OK\n') # nothing changed after idle
        self.client.send_idle()
        self.MPDWillReturn('CHANGED: player\n', 'OK\n')  # noidle response
        self.assertEqual(self.client.noidle(), ['player'])
        self.MPDWillReturn("volume: 50\n", "OK\n")
        status = self.client.status()
        self.assertMPDReceived('status\n')
        self.assertEqual({'volume': '50'}, status)

    def test_throw_when_calling_noidle_withoutidling(self):
        self.assertRaises(musicpd.CommandError, self.client.noidle)
        self.client.send_status()
        self.assertRaises(musicpd.CommandError, self.client.noidle)

    def test_client_to_client(self):
        # client to client is at this time in beta!

        self.MPDWillReturn('OK\n')
        self.assertIsNone(self.client.subscribe("monty"))
        self.assertMPDReceived('subscribe "monty"\n')

        self.MPDWillReturn('channel: monty\n', 'OK\n')
        channels = self.client.channels()
        self.assertMPDReceived('channels\n')
        self.assertEqual(["monty"], channels)

        self.MPDWillReturn('OK\n')
        self.assertIsNone(self.client.sendmessage("monty", "SPAM"))
        self.assertMPDReceived('sendmessage "monty" "SPAM"\n')

        self.MPDWillReturn('channel: monty\n', 'message: SPAM\n', 'OK\n')
        msg = self.client.readmessages()
        self.assertMPDReceived('readmessages\n')
        self.assertEqual(msg, [{"channel":"monty", "message": "SPAM"}])

        self.MPDWillReturn('OK\n')
        self.assertIsNone(self.client.unsubscribe("monty"))
        self.assertMPDReceived('unsubscribe "monty"\n')

        self.MPDWillReturn('OK\n')
        channels = self.client.channels()
        self.assertMPDReceived('channels\n')
        self.assertEqual([], channels)

    def test_ranges_in_command_args(self):
        self.MPDWillReturn("OK\n")
        self.client.playlistinfo((10,))
        self.assertMPDReceived('playlistinfo 10:\n')

        self.MPDWillReturn("OK\n")
        self.client.playlistinfo(("10",))
        self.assertMPDReceived('playlistinfo 10:\n')

        self.MPDWillReturn("OK\n")
        self.client.playlistinfo((10, 12))
        self.assertMPDReceived('playlistinfo 10:12\n')

        for arg in [(10, "t"), (10, 1, 1)]:
            self.MPDWillReturn("OK\n")
            with self.assertRaises(musicpd.CommandError):
                self.client.playlistinfo(arg)

    def test_numbers_as_command_args(self):
        self.MPDWillReturn("OK\n")
        self.client.find("file", 1)
        self.assertMPDReceived('find "file" "1"\n')

    def test_commands_without_callbacks(self):
        self.MPDWillReturn("\n")
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
        self.MPDWillReturn("ACK [50@0] {sticker} no such sticker\n")
        self.assertRaises(musicpd.CommandError,
                          self.client.sticker_get, 'song', 'baz', 'foo')

    def test_parse_sticker_list(self):
        self.MPDWillReturn("sticker: foo=bar\n", "sticker: lom=bok\n", "OK\n")
        res = self.client.sticker_list('song', 'baz')
        self.assertEqual(['foo=bar', 'lom=bok'], res)

        # Even with only one sticker, we get a dict
        self.MPDWillReturn("sticker: foo=bar\n", "OK\n")
        res = self.client.sticker_list('song', 'baz')
        self.assertEqual(['foo=bar'], res)


if __name__ == '__main__':
    unittest.main()
