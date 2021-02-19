# python-musicpd: Python MPD client library
# Copyright (C) 2012-2021  kaliko <kaliko@azylum.org>
# Copyright (C) 2019       Naglis Jonaitis <naglis@mailbox.org>
# Copyright (C) 2019       Bart Van Loon <bbb@bbbart.be>
# Copyright (C) 2008-2010  J. Alexander Treuman <jat@spatialrift.net>
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
VERSION = '0.6.0'
#: seconds before a tcp connection attempt times out (overriden by MPD_TIMEOUT env. var.)
CONNECTION_TIMEOUT = 30



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
    accordingly. Regarding ``MPD_HOST`` format to expose password refer
    MPD client manual :manpage:`mpc (1)`.

    Then :py:obj:`musicpd.MPDClient.connect` will use ``host`` and ``port`` as defaults if not provided as args.

    Cf. :py:obj:`musicpd.MPDClient.connect` for details.

    >>> from os import environ
    >>> environ['MPD_HOST'] = 'pass@mpdhost'
    >>> cli = musicpd.MPDClient()
    >>> cli.pwd == environ['MPD_HOST'].split('@')[0]
    True
    >>> cli.host == environ['MPD_HOST'].split('@')[1]
    True
    >>> cli.connect() # will use host/port as set in MPD_HOST/MPD_PORT

    :ivar str host: host used with the current connection
    :ivar str,int port: port used with the current connection
    :ivar str pwd: password detected in ``MPD_HOST`` environment variable

    .. warning:: Instance attribute host/port/pwd

      While :py:attr:`musicpd.MPDClient().host` and
      :py:attr:`musicpd.MPDClient().port` keep track of current connection
      host and port, :py:attr:`musicpd.MPDClient().pwd` is set once with
      password extracted from environment variable.
      Calling :py:meth:`musicpd.MPDClient().password()` with a new password
      won't update :py:attr:`musicpd.MPDClient().pwd` value.

      Moreover, :py:attr:`musicpd.MPDClient().pwd` is only an helper attribute
      exposing password extracted from ``MPD_HOST`` environment variable, it
      will not be used as default value for the :py:meth:`password` method
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
            "getvol":             self._fetch_object,
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
            # Queue Commands
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
            "albumart":           self._fetch_composite,
            "count":              self._fetch_object,
            "getfingerprint":     self._fetch_object,
            "find":               self._fetch_songs,
            "findadd":            self._fetch_nothing,
            "list":               self._fetch_list,
            "listall":            self._fetch_database,
            "listallinfo":        self._fetch_database,
            "listfiles":          self._fetch_database,
            "lsinfo":             self._fetch_database,
            "readcomments":       self._fetch_object,
            "readpicture":        self._fetch_composite,
            "search":             self._fetch_songs,
            "searchadd":          self._fetch_nothing,
            "searchaddpl":        self._fetch_nothing,
            "update":             self._fetch_item,
            "rescan":             self._fetch_item,
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
            "binarylimit":        self._fetch_nothing,
            "tagtypes":           self._fetch_list,
            "tagtypes disable":   self._fetch_nothing,
            "tagtypes enable":    self._fetch_nothing,
            "tagtypes clear":     self._fetch_nothing,
            "tagtypes all":       self._fetch_nothing,
            # Partition Commands
            "partition":          self._fetch_nothing,
            "listpartitions":     self._fetch_list,
            "newpartition":       self._fetch_nothing,
            "delpartition":       self._fetch_nothing,
            "moveoutput":         self._fetch_nothing,
            # Audio Output Commands
            "disableoutput":      self._fetch_nothing,
            "enableoutput":       self._fetch_nothing,
            "toggleoutput":       self._fetch_nothing,
            "outputs":            self._fetch_outputs,
            "outputset":          self._fetch_nothing,
            # Reflection Commands
            "config":             self._fetch_object,
            "commands":           self._fetch_list,
            "notcommands":        self._fetch_list,
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
        self.port = os.getenv('MPD_PORT', '6600')
        if os.getenv('MPD_HOST'):
            # If password is set: MPD_HOST=pass@host
            if '@' in os.getenv('MPD_HOST'):
                mpd_host_env = os.getenv('MPD_HOST').split('@', 1)
                if mpd_host_env[0]:
                    # A password is actually set
                    self.pwd = mpd_host_env[0]
                    if mpd_host_env[1]:
                        self.host = mpd_host_env[1]
                elif mpd_host_env[1]:
                    # No password set but leading @ is an abstract socket
                    self.host = '@'+mpd_host_env[1]
            else:
                # MPD_HOST is a plain host
                self.host = os.getenv('MPD_HOST')
        else:
            # Is socket there
            xdg_runtime_dir = os.getenv('XDG_RUNTIME_DIR', '/run')
            rundir = os.path.join(xdg_runtime_dir, 'mpd/socket')
            if os.path.exists(rundir):
                self.host = rundir
        self.mpd_timeout = os.getenv('MPD_TIMEOUT')
        if self.mpd_timeout and self.mpd_timeout.isdigit():
            self.mpd_timeout = int(self.mpd_timeout)
        else:  # Use 30s default even is MPD_TIMEOUT carries gargage
            self.mpd_timeout = CONNECTION_TIMEOUT

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
            raise PendingCommandError(
                "Cannot execute '%s' with pending commands" % command)
        retval = self._commands[command]
        if self._command_list is not None:
            if not callable(retval):
                raise CommandListError(
                    "'%s' not allowed in command list" % command)
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

    def _read_binary(self, amount):
        chunk = bytearray()
        while amount > 0:
            result = self._rbfile.read(amount)
            if len(result) == 0:
                self.disconnect()
                raise ConnectionError("Connection lost while reading binary content")
            chunk.extend(result)
            amount -= len(result)
        return bytes(chunk)

    def _read_line(self, binary=False):
        if binary:
            line = self._rbfile.readline().decode('utf-8')
        else:
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

    def _read_pair(self, separator, binary=False):
        line = self._read_line(binary=binary)
        if line is None:
            return
        pair = line.split(separator, 1)
        if len(pair) < 2:
            raise ProtocolError("Could not parse pair: '%s'" % line)
        return pair

    def _read_pairs(self, separator=": ", binary=False):
        pair = self._read_pair(separator, binary=binary)
        while pair:
            yield pair
            pair = self._read_pair(separator, binary=binary)

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

    def _fetch_composite(self):
        obj = {}
        for key, value in self._read_pairs(binary=True):
            key = key.lower()
            obj[key] = value
            if key == 'binary':
                break
        if not obj:
            # If the song file was recognized, but there is no picture, the
            # response is successful, but is otherwise empty.
            return obj
        amount = int(obj['binary'])
        try:
            obj['data'] = self._read_binary(amount)
        except IOError as err:
            raise ConnectionError('Error reading binary content: %s' % err)
        if len(obj['data']) != amount:  # can we ever get there?
            raise ConnectionError('Error reading binary content: '
                      'Expects %sB, got %s' % (amount, len(obj['data'])))
        # Fetches trailing new line
        self._read_line(binary=True)
        # Fetches SUCCESS code
        self._read_line(binary=True)
        return obj

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
        self._rbfile = _NotConnected()
        self._wfile = _NotConnected()

    def _connect_unix(self, path):
        if not hasattr(socket, "AF_UNIX"):
            raise ConnectionError(
                "Unix domain sockets not supported on this platform")
        # abstract socket
        if path.startswith('@'):
            path = '\0'+path[1:]
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
                sock.settimeout(self.mpd_timeout)
                sock.connect(sa)
                sock.settimeout(None)
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
            raise CommandError(
                'cannot send noidle if send_idle was not called')
        del self._pending[0]
        self._write_command("noidle")
        return self._fetch_list()

    def connect(self, host=None, port=None):
        """Connects the MPD server

        :param str host: hostname, IP or FQDN (defaults to `localhost` or socket, see below for details)
        :param port: port number (defaults to 6600)
        :type port: str or int

        The connect method honors MPD_HOST/MPD_PORT environment variables.

        The underlying tcp socket also honors MPD_TIMEOUT environment variable
        and defaults to :py:obj:`musicpd.CONNECTION_TIMEOUT`.

        .. note:: Default host/port

          If host evaluate to :py:obj:`False`
           * use ``MPD_HOST`` environment variable if set, extract password if present,
           * else looks for a existing file in ``${XDG_RUNTIME_DIR:-/run/}/mpd/socket``
           * else set host to ``localhost``

          If port evaluate to :py:obj:`False`
           * if ``MPD_PORT`` environment variable is set, use it for port
           * else use ``6600``
        """
        if not host:
            host = self.host
        else:
            self.host = host
        if not port:
            port = self.port
        else:
            self.port = port
        if self._sock is not None:
            raise ConnectionError("Already connected")
        if host[0] in ['/', '@']:
            self._sock = self._connect_unix(host)
        else:
            self._sock = self._connect_tcp(host, port)
        self._rfile = self._sock.makefile("r", encoding='utf-8', errors='surrogateescape')
        self._rbfile = self._sock.makefile("rb")
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
        if hasattr(self._rbfile, 'close'):
            self._rbfile.close()
        if hasattr(self._wfile, 'close'):
            self._wfile.close()
        if hasattr(self._sock, 'close'):
            self._sock.close()
        self._reset()

    def fileno(self):
        """Return the socket’s file descriptor (a small integer).
        This is useful with :py:obj:`select.select`.
        """
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
