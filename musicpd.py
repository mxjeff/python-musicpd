# python-musicpd: Python MPD client library
# Copyright (C) 2008-2010  J. Alexander Treuman <jat@spatialrift.net>
# Copyright (C) 2012-2018  Kaliko Jack <kaliko@azylum.org>
#
# python-musicpd is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# python-musicpd is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with python-musicpd.  If not, see <http://www.gnu.org/licenses/>.

# pylint: disable=missing-docstring

import socket
import os

from functools import wraps


HELLO_PREFIX = "OK MPD "
ERROR_PREFIX = "ACK "
SUCCESS = "OK"
NEXT = "list_OK"
VERSION = '0.4.3'


def iterator_wrapper(func):
    """Decorator handling iterate option"""
    @wraps(func)
    def decorated_function(instance, *args, **kwargs):
        generator = func(instance, *args, **kwargs)
        if not instance.iterate:
            return list(generator)
        instance._iterating = True
        def iterator(gen):
            try:
                for item in gen:
                    yield item
            finally:
                instance._iterating = False
        return iterator(generator)
    return decorated_function


class MPDError(Exception):
    pass

class ConnectionError(MPDError):
    pass

class ProtocolError(MPDError):
    pass

class CommandError(MPDError):
    pass

class CommandListError(MPDError):
    pass

class PendingCommandError(MPDError):
    pass

class IteratingError(MPDError):
    pass

class Range:

    def __init__(self, tpl):
        self.tpl = tpl
        self._check()

    def __str__(self):
        if len(self.tpl) == 0:
            return ':'
        if len(self.tpl) == 1:
            return '{0}:'.format(self.tpl[0])
        return '{0[0]}:{0[1]}'.format(self.tpl)

    def __repr__(self):
        return 'Range({0})'.format(self.tpl)

    def _check(self):
        if not isinstance(self.tpl, tuple):
            raise CommandError('Wrong type, provide a tuple')
        if len(self.tpl) not in [0, 1, 2]:
            raise CommandError('length not in [0, 1, 2]')
        for index in self.tpl:
            try:
                index = int(index)
            except (TypeError, ValueError):
                raise CommandError('Not a tuple of int')

class _NotConnected:
    def __getattr__(self, attr):
        return self._dummy

    def _dummy(*args):
        raise ConnectionError("Not connected")

class MPDClient:
    """MPDClient instance will look for ``MPD_HOST``/``MPD_PORT``/``XDG_RUNTIME_DIR`` environment
    variables and set instance attribute ``host``, ``port`` and ``pwd``
    accordingly.

    Then :py:obj:`musicpd.MPDClient.connect` will use ``host`` and ``port`` as defaults if not provided as args.

    Cf. :py:obj:`musicpd.MPDClient.connect` for details.

    >>> from os inport environ
    >>> environ['MPD_HOST'] = 'pass@mpdhost'
    >>> cli = musicpd.MPDClient()
    >>> cli.pwd == environ['MPD_HOST'].split('@')[0]
    True
    >>> cli.host == environ['MPD_HOST'].split('@')[1]
    True
    >>> # cli.connect() will use host/port as set in MPD_HOST/MPD_PORT
    """

    def __init__(self):
        self.iterate = False
        self._reset()
        self._commands = {
            # Status Commands
            "clearerror":         self._fetch_nothing,
            "currentsong":        self._fetch_object,
            "idle":               self._fetch_list,
            #"noidle":             None,
            "status":             self._fetch_object,
            "stats":              self._fetch_object,
            # Playback Option Commands
            "consume":            self._fetch_nothing,
            "crossfade":          self._fetch_nothing,
            "mixrampdb":          self._fetch_nothing,
            "mixrampdelay":       self._fetch_nothing,
            "random":             self._fetch_nothing,
            "repeat":             self._fetch_nothing,
            "setvol":             self._fetch_nothing,
            "single":             self._fetch_nothing,
            "replay_gain_mode":   self._fetch_nothing,
            "replay_gain_status": self._fetch_item,
            "volume":             self._fetch_nothing,
            # Playback Control Commands
            "next":               self._fetch_nothing,
            "pause":              self._fetch_nothing,
            "play":               self._fetch_nothing,
            "playid":             self._fetch_nothing,
            "previous":           self._fetch_nothing,
            "seek":               self._fetch_nothing,
            "seekid":             self._fetch_nothing,
            "seekcur":            self._fetch_nothing,
            "stop":               self._fetch_nothing,
            # Playlist Commands
            "add":                self._fetch_nothing,
            "addid":              self._fetch_item,
            "clear":              self._fetch_nothing,
            "delete":             self._fetch_nothing,
            "deleteid":           self._fetch_nothing,
            "move":               self._fetch_nothing,
            "moveid":             self._fetch_nothing,
            "playlist":           self._fetch_playlist,
            "playlistfind":       self._fetch_songs,
            "playlistid":         self._fetch_songs,
            "playlistinfo":       self._fetch_songs,
            "playlistsearch":     self._fetch_songs,
            "plchanges":          self._fetch_songs,
            "plchangesposid":     self._fetch_changes,
            "prio":               self._fetch_nothing,
            "prioid":             self._fetch_nothing,
            "rangeid":            self._fetch_nothing,
            "shuffle":            self._fetch_nothing,
            "swap":               self._fetch_nothing,
            "swapid":             self._fetch_nothing,
            "addtagid":           self._fetch_nothing,
            "cleartagid":         self._fetch_nothing,
            # Stored Playlist Commands
            "listplaylist":       self._fetch_list,
            "listplaylistinfo":   self._fetch_songs,
            "listplaylists":      self._fetch_playlists,
            "load":               self._fetch_nothing,
            "playlistadd":        self._fetch_nothing,
            "playlistclear":      self._fetch_nothing,
            "playlistdelete":     self._fetch_nothing,
            "playlistmove":       self._fetch_nothing,
            "rename":             self._fetch_nothing,
            "rm":                 self._fetch_nothing,
            "save":               self._fetch_nothing,
            # Database Commands
            "count":              self._fetch_object,
            "find":               self._fetch_songs,
            "findadd":            self._fetch_nothing,
            "list":               self._fetch_list,
            "listall":            self._fetch_database,
            "listallinfo":        self._fetch_database,
            "lsinfo":             self._fetch_database,
            "search":             self._fetch_songs,
            "searchadd":          self._fetch_nothing,
            "searchaddpl":        self._fetch_nothing,
            "update":             self._fetch_item,
            "rescan":             self._fetch_item,
            "readcomments":       self._fetch_object,
            # Mounts and neighbors
            "mount":              self._fetch_nothing,
            "unmount":            self._fetch_nothing,
            "listmounts":         self._fetch_mounts,
            "listneighbors":      self._fetch_neighbors,
            # Sticker Commands
            "sticker get":        self._fetch_item,
            "sticker set":        self._fetch_nothing,
            "sticker delete":     self._fetch_nothing,
            "sticker list":       self._fetch_list,
            "sticker find":       self._fetch_songs,
            # Connection Commands
            "close":              None,
            "kill":               None,
            "password":           self._fetch_nothing,
            "ping":               self._fetch_nothing,
            # Audio Output Commands
            "disableoutput":      self._fetch_nothing,
            "enableoutput":       self._fetch_nothing,
            "toggleoutput":       self._fetch_nothing,
            "outputs":            self._fetch_outputs,
            # Reflection Commands
            "config":             self._fetch_object,
            "commands":           self._fetch_list,
            "notcommands":        self._fetch_list,
            "tagtypes":           self._fetch_list,
            "urlhandlers":        self._fetch_list,
            "decoders":           self._fetch_plugins,
            # Client to Client
            "subscribe":          self._fetch_nothing,
            "unsubscribe":        self._fetch_nothing,
            "channels":           self._fetch_list,
            "readmessages":       self._fetch_messages,
            "sendmessage":        self._fetch_nothing,
        }
        self._get_envvars()

    def _get_envvars(self):
        """
        Retrieve MPD env. var. to overrides "localhost:6600"
            Use MPD_HOST/MPD_PORT if set
            else use MPD_HOST=${XDG_RUNTIME_DIR:-/run/}/mpd/socket if file exists
        """
        self.host = 'localhost'
        self.pwd = None
        self.port = os.environ.get('MPD_PORT', '6600')
        mpd_host_env = os.environ.get('MPD_HOST')
        if mpd_host_env:
            # If password is set:
            # mpd_host_env = ['pass', 'host'] because MPD_HOST=pass@host
            mpd_host_env = mpd_host_env.split('@')
            mpd_host_env.reverse()
            self.host = mpd_host_env[0]
            if len(mpd_host_env) > 1 and mpd_host_env[1]:
                self.pwd = mpd_host_env[1]
        else:
            # Is socket there
            xdg_runtime_dir = os.environ.get('XDG_RUNTIME_DIR', '/run')
            rundir = os.path.join(xdg_runtime_dir, 'mpd/socket')
            if os.path.exists(rundir):
                self.host = rundir

    def __getattr__(self, attr):
        if attr == 'send_noidle':  # have send_noidle to cancel idle as well as noidle
            return self.noidle()
        if attr.startswith("send_"):
            command = attr.replace("send_", "", 1)
            wrapper = self._send
        elif attr.startswith("fetch_"):
            command = attr.replace("fetch_", "", 1)
            wrapper = self._fetch
        else:
            command = attr
            wrapper = self._execute
        if command not in self._commands:
            command = command.replace("_", " ")
            if command not in self._commands:
                raise AttributeError("'%s' object has no attribute '%s'" %
                                     (self.__class__.__name__, attr))
        return lambda *args: wrapper(command, args)

    def _send(self, command, args):
        if self._command_list is not None:
            raise CommandListError("Cannot use send_%s in a command list" %
                                   command.replace(" ", "_"))
        self._write_command(command, args)
        retval = self._commands[command]
        if retval is not None:
            self._pending.append(command)

    def _fetch(self, command, args=None):
        if self._command_list is not None:
            raise CommandListError("Cannot use fetch_%s in a command list" %
                                   command.replace(" ", "_"))
        if self._iterating:
            raise IteratingError("Cannot use fetch_%s while iterating" %
                                 command.replace(" ", "_"))
        if not self._pending:
            raise PendingCommandError("No pending commands to fetch")
        if self._pending[0] != command:
            raise PendingCommandError("'%s' is not the currently "
                                      "pending command" % command)
        del self._pending[0]
        retval = self._commands[command]
        if callable(retval):
            return retval()
        return retval

    def _execute(self, command, args):
        if self._iterating:
            raise IteratingError("Cannot execute '%s' while iterating" %
                                 command)
        if self._pending:
            raise PendingCommandError("Cannot execute '%s' with "
                                      "pending commands" % command)
        retval = self._commands[command]
        if self._command_list is not None:
            if not callable(retval):
                raise CommandListError("'%s' not allowed in command list" %
                                        command)
            self._write_command(command, args)
            self._command_list.append(retval)
        else:
            self._write_command(command, args)
            if callable(retval):
                return retval()
            return retval

    def _write_line(self, line):
        self._wfile.write("%s\n" % line)
        self._wfile.flush()

    def _write_command(self, command, args=None):
        if args is None:
            args = []
        parts = [command]
        for arg in args:
            if isinstance(arg, tuple):
                parts.append('{0!s}'.format(Range(arg)))
            else:
                parts.append('"%s"' % escape(str(arg)))
        self._write_line(" ".join(parts))

    def _read_line(self):
        line = self._rfile.readline()
        if not line.endswith("\n"):
            self.disconnect()
            raise ConnectionError("Connection lost while reading line")
        line = line.rstrip("\n")
        if line.startswith(ERROR_PREFIX):
            error = line[len(ERROR_PREFIX):].strip()
            raise CommandError(error)
        if self._command_list is not None:
            if line == NEXT:
                return
            if line == SUCCESS:
                raise ProtocolError("Got unexpected '%s'" % SUCCESS)
        elif line == SUCCESS:
            return
        return line

    def _read_pair(self, separator):
        line = self._read_line()
        if line is None:
            return
        pair = line.split(separator, 1)
        if len(pair) < 2:
            raise ProtocolError("Could not parse pair: '%s'" % line)
        return pair

    def _read_pairs(self, separator=": "):
        pair = self._read_pair(separator)
        while pair:
            yield pair
            pair = self._read_pair(separator)

    def _read_list(self):
        seen = None
        for key, value in self._read_pairs():
            if key != seen:
                if seen is not None:
                    raise ProtocolError("Expected key '%s', got '%s'" %
                                        (seen, key))
                seen = key
            yield value

    def _read_playlist(self):
        for _, value in self._read_pairs(":"):
            yield value

    def _read_objects(self, delimiters=None):
        obj = {}
        if delimiters is None:
            delimiters = []
        for key, value in self._read_pairs():
            key = key.lower()
            if obj:
                if key in delimiters:
                    yield obj
                    obj = {}
                elif key in obj:
                    if not isinstance(obj[key], list):
                        obj[key] = [obj[key], value]
                    else:
                        obj[key].append(value)
                    continue
            obj[key] = value
        if obj:
            yield obj

    def _read_command_list(self):
        try:
            for retval in self._command_list:
                yield retval()
        finally:
            self._command_list = None
        self._fetch_nothing()

    def _fetch_nothing(self):
        line = self._read_line()
        if line is not None:
            raise ProtocolError("Got unexpected return value: '%s'" % line)

    def _fetch_item(self):
        pairs = list(self._read_pairs())
        if len(pairs) != 1:
            return
        return pairs[0][1]

    @iterator_wrapper
    def _fetch_list(self):
        return self._read_list()

    @iterator_wrapper
    def _fetch_playlist(self):
        return self._read_playlist()

    def _fetch_object(self):
        objs = list(self._read_objects())
        if not objs:
            return {}
        return objs[0]

    @iterator_wrapper
    def _fetch_objects(self, delimiters):
        return self._read_objects(delimiters)

    def _fetch_changes(self):
        return self._fetch_objects(["cpos"])

    def _fetch_songs(self):
        return self._fetch_objects(["file"])

    def _fetch_playlists(self):
        return self._fetch_objects(["playlist"])

    def _fetch_database(self):
        return self._fetch_objects(["file", "directory", "playlist"])

    def _fetch_outputs(self):
        return self._fetch_objects(["outputid"])

    def _fetch_plugins(self):
        return self._fetch_objects(["plugin"])

    def _fetch_messages(self):
        return self._fetch_objects(["channel"])

    def _fetch_mounts(self):
        return self._fetch_objects(["mount"])

    def _fetch_neighbors(self):
        return self._fetch_objects(["neighbor"])

    @iterator_wrapper
    def _fetch_command_list(self):
        return self._read_command_list()

    def _hello(self):
        line = self._rfile.readline()
        if not line.endswith("\n"):
            raise ConnectionError("Connection lost while reading MPD hello")
        line = line.rstrip("\n")
        if not line.startswith(HELLO_PREFIX):
            raise ProtocolError("Got invalid MPD hello: '%s'" % line)
        self.mpd_version = line[len(HELLO_PREFIX):].strip()

    def _reset(self):
        self.mpd_version = None
        self._iterating = False
        self._pending = []
        self._command_list = None
        self._sock = None
        self._rfile = _NotConnected()
        self._wfile = _NotConnected()

    def _connect_unix(self, path):
        if not hasattr(socket, "AF_UNIX"):
            raise ConnectionError("Unix domain sockets not supported "
                                  "on this platform")
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(path)
        return sock

    def _connect_tcp(self, host, port):
        try:
            flags = socket.AI_ADDRCONFIG
        except AttributeError:
            flags = 0
        err = None
        for res in socket.getaddrinfo(host, port, socket.AF_UNSPEC,
                                      socket.SOCK_STREAM, socket.IPPROTO_TCP,
                                      flags):
            af, socktype, proto, _, sa = res
            sock = None
            try:
                sock = socket.socket(af, socktype, proto)
                sock.connect(sa)
                return sock
            except socket.error as socket_err:
                err = socket_err
                if sock is not None:
                    sock.close()
        if err is not None:
            raise ConnectionError(str(err))
        else:
            raise ConnectionError("getaddrinfo returns an empty list")

    def noidle(self):
        # noidle's special case
        if not self._pending or self._pending[0] != 'idle':
            raise CommandError('cannot send noidle if send_idle was not called')
        del self._pending[0]
        self._write_command("noidle")
        return self._fetch_list()

    def connect(self, host=None, port=None):
        """Connects the MPD server

        :param str host: hostname, IP or FQDN (defaults to `localhost` or socket, see below for details)
        :param str port: port number (defaults to 6600)

        The connect method honors MPD_HOST/MPD_PORT environment variables.

        .. note:: Default host/port

          If host evaluate to :py:obj:`False`
           * use ``MPD_HOST`` env. var. if set, extract password if present,
           * else looks for a existing file in ``${XDG_RUNTIME_DIR:-/run/}/mpd/socket``
           * else set host to ``localhost``

          If port evaluate to :py:obj:`False`
           * if ``MPD_PORT`` env. var. is set, use it for port
           * else use ``6600``
        """
        if not host:
            host = self.host
        if not port:
            port = self.port
        if self._sock is not None:
            raise ConnectionError("Already connected")
        if host.startswith("/"):
            self._sock = self._connect_unix(host)
        else:
            self._sock = self._connect_tcp(host, port)
        self._rfile = self._sock.makefile("r", encoding='utf-8')
        self._wfile = self._sock.makefile("w", encoding='utf-8')
        try:
            self._hello()
        except:
            self.disconnect()
            raise

    def disconnect(self):
        """Closes the MPD connection.
        The client closes the actual socket, it does not use the
        'close' request from MPD protocol (as suggested in documentation).
        """
        if hasattr(self._rfile, 'close'):
            self._rfile.close()
        if hasattr(self._wfile, 'close'):
            self._wfile.close()
        if hasattr(self._sock, 'close'):
            self._sock.close()
        self._reset()

    def fileno(self):
        if self._sock is None:
            raise ConnectionError("Not connected")
        return self._sock.fileno()

    def command_list_ok_begin(self):
        if self._command_list is not None:
            raise CommandListError("Already in command list")
        if self._iterating:
            raise IteratingError("Cannot begin command list while iterating")
        if self._pending:
            raise PendingCommandError("Cannot begin command list "
                                      "with pending commands")
        self._write_command("command_list_ok_begin")
        self._command_list = []

    def command_list_end(self):
        if self._command_list is None:
            raise CommandListError("Not in command list")
        if self._iterating:
            raise IteratingError("Already iterating over a command list")
        self._write_command("command_list_end")
        return self._fetch_command_list()


def escape(text):
    return text.replace("\\", "\\\\").replace('"', '\\"')

# vim: set expandtab shiftwidth=4 softtabstop=4 textwidth=79:
