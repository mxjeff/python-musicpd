# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2012-2024  kaliko <kaliko@azylum.org>
# SPDX-FileCopyrightText: 2021       Wonko der Verständige <wonko@hanstool.org>
# SPDX-FileCopyrightText: 2019       Naglis Jonaitis <naglis@mailbox.org>
# SPDX-FileCopyrightText: 2019       Bart Van Loon <bbb@bbbart.be>
# SPDX-FileCopyrightText: 2008-2010  J. Alexander Treuman <jat@spatialrift.net>
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Python Music Player Daemon client library"""


import logging
import os
import socket

from functools import wraps

HELLO_PREFIX = "OK MPD "
ERROR_PREFIX = "ACK "
SUCCESS = "OK"
NEXT = "list_OK"
#: Module version
VERSION = '0.9.1'
#: Seconds before a connection attempt times out
#: (overriden by :envvar:`MPD_TIMEOUT` env. var.)
CONNECTION_TIMEOUT = 30
#: Socket timeout in second > 0 (Default is :py:obj:`None` for no timeout)
SOCKET_TIMEOUT = None

log = logging.getLogger(__name__)


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
    """Main musicpd Exception"""


class ConnectionError(MPDError):
    """Fatal Connection Error, cannot recover from it."""


class ProtocolError(MPDError):
    """Fatal Protocol Error, cannot recover from it"""


class CommandError(MPDError):
    """Malformed command, socket should be fine, can reuse it"""


class CommandListError(MPDError):
    """"""


class PendingCommandError(MPDError):
    """"""


class IteratingError(MPDError):
    """"""


class Range:

    def __init__(self, tpl):
        self.tpl = tpl
        self.lower = ''
        self.upper = ''
        self._check()

    def __str__(self):
        return f'{self.lower}:{self.upper}'

    def __repr__(self):
        return f'Range({self.tpl})'

    def _check_element(self, item):
        if item is None or item == '':
            return ''
        try:
            return str(int(item))
        except (TypeError, ValueError) as err:
            raise CommandError(f'Not an integer: "{item}"') from err
        return item

    def _check(self):
        if not isinstance(self.tpl, tuple):
            raise CommandError('Wrong type, provide a tuple')
        if len(self.tpl) == 0:
            return
        if len(self.tpl) == 1:
            self.lower = self._check_element(self.tpl[0])
            return
        if len(self.tpl) != 2:
            raise CommandError('Range wrong size (0, 1 or 2 allowed)')
        self.lower = self._check_element(self.tpl[0])
        self.upper = self._check_element(self.tpl[1])
        if self.lower == '' and self.upper != '':
            raise CommandError(f'Integer expected to start the range: {self.tpl}')
        if self.upper.isdigit() and self.lower.isdigit():
            if int(self.lower) > int(self.upper):
                raise CommandError(f'Wrong range: {self.lower} > {self.upper}')


class _NotConnected:

    def __getattr__(self, attr):
        return self._dummy

    def _dummy(self, *args):
        raise ConnectionError("Not connected")


class MPDClient:
    """MPDClient instance will look for :envvar:`MPD_HOST`/:envvar:`MPD_PORT`/:envvar:`XDG_RUNTIME_DIR` environment
    variables and set instance attribute :py:attr:`host`, :py:attr:`port` and :py:obj:`pwd`
    accordingly.

    Then :py:obj:`musicpd.MPDClient.connect` will use :py:obj:`host` and
    :py:obj:`port` as defaults if not provided as args.

    Regarding :envvar:`MPD_HOST` format to expose password refer this module
    documentation or MPD client manual :manpage:`mpc (1)`.

    >>> from os import environ
    >>> environ['MPD_HOST'] = 'pass@mpdhost'
    >>> cli = musicpd.MPDClient()
    >>> cli.pwd == environ['MPD_HOST'].split('@')[0]
    True
    >>> cli.host == environ['MPD_HOST'].split('@')[1]
    True
    >>> cli.connect() # will use host/port as set in MPD_HOST/MPD_PORT

    .. note::

      default host:
       * use :envvar:`MPD_HOST` environment variable if set, extract password if present,
       * else use :envvar:`XDG_RUNTIME_DIR` to looks for an existing file in ``${XDG_RUNTIME_DIR:-/run/}/mpd/socket``
       * else set host to ``localhost``

      default port:
       * use :envvar:`MPD_PORT` environment variable is set
       * else use ``6600``

    .. warning:: **Instance attribute host/port/pwd**

      While :py:attr:`musicpd.MPDClient.host` and
      :py:attr:`musicpd.MPDClient.port` keep track of current connection
      host and port, :py:attr:`musicpd.MPDClient.pwd` is set once with
      password extracted from environment variable.
      Calling MPS's password method with a new password
      won't update :py:attr:`musicpd.MPDClient.pwd` value.

      Moreover, :py:attr:`musicpd.MPDClient.pwd` is only an helper attribute
      exposing password extracted from :envvar:`MPD_HOST` environment variable, it
      will not be used as default value for the MPD's password command.
    """

    def __init__(self):
        self.iterate = False
        #: Socket timeout value in seconds
        self._socket_timeout = SOCKET_TIMEOUT
        #: Current connection timeout value, defaults to
        #: :py:obj:`CONNECTION_TIMEOUT` or env. var. ``MPD_TIMEOUT`` if provided
        self.mpd_timeout = None
        self.mpd_version = ''
        """Protocol version as exposed by the server as a :py:obj:`str`

        .. note:: This is the version of the protocol spoken, not the real version of the daemon."""
        self._reset()
        self._commands = {
            # Querying MPD’s status # querying-mpd-s-status
            "clearerror":         self._fetch_nothing,
            "currentsong":        self._fetch_object,
            "idle":               self._fetch_list,
            #"noidle":             None,
            "status":             self._fetch_object,
            "stats":              self._fetch_object,
            # Playback Option # playback-options
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
            # Controlling playback # controlling-playback
            "next":               self._fetch_nothing,
            "pause":              self._fetch_nothing,
            "play":               self._fetch_nothing,
            "playid":             self._fetch_nothing,
            "previous":           self._fetch_nothing,
            "seek":               self._fetch_nothing,
            "seekid":             self._fetch_nothing,
            "seekcur":            self._fetch_nothing,
            "stop":               self._fetch_nothing,
            # The Queue # the-queue
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
            # Stored playlists # stored-playlists
            "listplaylist":       self._fetch_list,
            "listplaylistinfo":   self._fetch_songs,
            "listplaylists":      self._fetch_playlists,
            "load":               self._fetch_nothing,
            "playlistadd":        self._fetch_nothing,
            "playlistclear":      self._fetch_nothing,
            "playlistdelete":     self._fetch_nothing,
            "playlistlength":     self._fetch_object,
            "playlistmove":       self._fetch_nothing,
            "rename":             self._fetch_nothing,
            "rm":                 self._fetch_nothing,
            "save":               self._fetch_nothing,
            # The music database # the-music-database
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
            "searchcount":        self._fetch_object,
            "update":             self._fetch_item,
            "rescan":             self._fetch_item,
            # Mounts and neighbors # mounts-and-neighbors
            "mount":              self._fetch_nothing,
            "unmount":            self._fetch_nothing,
            "listmounts":         self._fetch_mounts,
            "listneighbors":      self._fetch_neighbors,
            # Stickers # stickers
            "sticker get":        self._fetch_item,
            "sticker set":        self._fetch_nothing,
            "sticker delete":     self._fetch_nothing,
            "sticker list":       self._fetch_list,
            "sticker find":       self._fetch_songs,
            "stickernames":       self._fetch_list,
            # Connection settings # connection-settings
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
            # Partition Commands # partition-commands
            "partition":          self._fetch_nothing,
            "listpartitions":     self._fetch_list,
            "newpartition":       self._fetch_nothing,
            "delpartition":       self._fetch_nothing,
            "moveoutput":         self._fetch_nothing,
            # Audio output devices # audio-output-devices
            "disableoutput":      self._fetch_nothing,
            "enableoutput":       self._fetch_nothing,
            "toggleoutput":       self._fetch_nothing,
            "outputs":            self._fetch_outputs,
            "outputset":          self._fetch_nothing,
            # Reflection # reflection
            "config":             self._fetch_object,
            "commands":           self._fetch_list,
            "notcommands":        self._fetch_list,
            "urlhandlers":        self._fetch_list,
            "decoders":           self._fetch_plugins,
            # Client to Client # client-to-client
            "subscribe":          self._fetch_nothing,
            "unsubscribe":        self._fetch_nothing,
            "channels":           self._fetch_list,
            "readmessages":       self._fetch_messages,
            "sendmessage":        self._fetch_nothing,
        }
        #: host used with the current connection (:py:obj:`str`)
        self.host = None
        #: password detected in :envvar:`MPD_HOST` environment variable (:py:obj:`str`)
        self.pwd = None
        #: port used with the current connection (:py:obj:`int`, :py:obj:`str`)
        self.port = None
        self._get_envvars()

    def _get_envvars(self):
        """
        Retrieve MPD env. var. to overrides default "localhost:6600"
        """
        # Set some defaults
        self.host = 'localhost'
        self.port = os.getenv('MPD_PORT', '6600')
        _host = os.getenv('MPD_HOST', '')
        if _host:
            # If password is set: MPD_HOST=pass@host
            if '@' in _host:
                mpd_host_env = _host.split('@', 1)
                if mpd_host_env[0]:
                    # A password is actually set
                    log.debug('password detected in MPD_HOST, set client pwd attribute')
                    self.pwd = mpd_host_env[0]
                    if mpd_host_env[1]:
                        self.host = mpd_host_env[1]
                        log.debug('host detected in MPD_HOST: %s', self.host)
                elif mpd_host_env[1]:
                    # No password set but leading @ is an abstract socket
                    self.host = '@'+mpd_host_env[1]
                    log.debug('host detected in MPD_HOST: %s (abstract socket)', self.host)
            else:
                # MPD_HOST is a plain host
                self.host = _host
                log.debug('host detected in MPD_HOST: %s', self.host)
        else:
            # Is socket there
            xdg_runtime_dir = os.getenv('XDG_RUNTIME_DIR', '/run')
            rundir = os.path.join(xdg_runtime_dir, 'mpd/socket')
            if os.path.exists(rundir):
                self.host = rundir
                log.debug('host detected in ${XDG_RUNTIME_DIR}/run: %s (unix socket)', self.host)
        _mpd_timeout = os.getenv('MPD_TIMEOUT', '')
        if _mpd_timeout.isdigit():
            self.mpd_timeout = int(_mpd_timeout)
            log.debug('timeout detected in MPD_TIMEOUT: %d', self.mpd_timeout)
        else:  # Use CONNECTION_TIMEOUT as default even if MPD_TIMEOUT carries gargage
            self.mpd_timeout = CONNECTION_TIMEOUT

    def __getattr__(self, attr):
        if attr == 'send_noidle':  # have send_noidle to cancel idle as well as noidle
            return self.noidle
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
                cls = self.__class__.__name__
                raise AttributeError(f"'{cls}' object has no attribute '{attr}'")
        return lambda *args: wrapper(command, args)

    def _send(self, command, args):
        if self._command_list is not None:
            raise CommandListError("Cannot use send_%s in a command list" %
                                   command.replace(" ", "_"))
        self._write_command(command, args)
        retval = self._commands[command]
        if retval is not None:
            self._pending.append(command)

    def _fetch(self, command, args=None):  # pylint: disable=unused-argument
        cmd_fmt = command.replace(" ", "_")
        if self._command_list is not None:
            raise CommandListError(f"Cannot use fetch_{cmd_fmt} in a command list")
        if self._iterating:
            raise IteratingError(f"Cannot use fetch_{cmd_fmt} while iterating")
        if not self._pending:
            raise PendingCommandError("No pending commands to fetch")
        if self._pending[0] != command:
            raise PendingCommandError(f"'{command}' is not the currently pending command")
        del self._pending[0]
        retval = self._commands[command]
        if callable(retval):
            return retval()
        return retval

    def _execute(self, command, args):  # pylint: disable=unused-argument
        if self._iterating:
            raise IteratingError(f"Cannot execute '{command}' while iterating")
        if self._pending:
            raise PendingCommandError(f"Cannot execute '{command}' with pending commands")
        retval = self._commands[command]
        if self._command_list is not None:
            if not callable(retval):
                raise CommandListError(f"'{command}' not allowed in command list")
            self._write_command(command, args)
            self._command_list.append(retval)
        else:
            self._write_command(command, args)
            if callable(retval):
                return retval()
            return retval
        return None

    def _write_line(self, line):
        self._wfile.write(f"{line!s}\n")
        self._wfile.flush()

    def _write_command(self, command, args=None):
        if args is None:
            args = []
        parts = [command]
        for arg in args:
            if isinstance(arg, tuple):
                parts.append(f'{Range(arg)!s}')
            else:
                parts.append(f'"{escape(str(arg))}"')
        if '\n' in ' '.join(parts):
            raise CommandError('new line found in the command!')
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
                return None
            if line == SUCCESS:
                raise ProtocolError(f"Got unexpected '{SUCCESS}'")
        elif line == SUCCESS:
            return None
        return line

    def _read_pair(self, separator, binary=False):
        line = self._read_line(binary=binary)
        if line is None:
            return None
        pair = line.split(separator, 1)
        if len(pair) < 2:
            raise ProtocolError(f"Could not parse pair: '{line}'")
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
                    raise ProtocolError(f"Expected key '{seen}', got '{key}'")
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
            raise ProtocolError(f"Got unexpected return value: '{line}'")

    def _fetch_item(self):
        pairs = list(self._read_pairs())
        if len(pairs) != 1:
            return None
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
            raise ConnectionError(f'Error reading binary content: {err}') from err
        data_bytes = len(obj['data'])
        if data_bytes != amount:  # can we ever get there?
            raise ConnectionError('Error reading binary content: '
                    f'Expects {amount}B, got {data_bytes}')
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
            raise ProtocolError(f"Got invalid MPD hello: '{line}'")
        self.mpd_version = line[len(HELLO_PREFIX):].strip()

    def _reset(self):
        self.mpd_version = ''
        self._iterating = False
        self._pending = []
        self._command_list = None
        self._sock = None
        self._rfile = _NotConnected()
        self._rbfile = _NotConnected()
        self._wfile = _NotConnected()

    def _connect_unix(self, path):
        if not hasattr(socket, "AF_UNIX"):
            raise ConnectionError("Unix domain sockets not supported on this platform")
        # abstract socket
        if path.startswith('@'):
            path = '\0'+path[1:]
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(self.mpd_timeout)
            sock.connect(path)
            sock.settimeout(self.socket_timeout)
        except socket.error as socket_err:
            raise ConnectionError(socket_err) from socket_err
        return sock

    def _connect_tcp(self, host, port):
        try:
            flags = socket.AI_ADDRCONFIG
        except AttributeError:
            flags = 0
        err = None
        try:
            gai = socket.getaddrinfo(host, port, socket.AF_UNSPEC,
                                     socket.SOCK_STREAM, socket.IPPROTO_TCP,
                                     flags)
        except socket.error as gaierr:
            raise ConnectionError(gaierr) from gaierr
        for res in gai:
            af, socktype, proto, _, sa = res
            sock = None
            try:
                log.debug('opening socket %s', sa)
                sock = socket.socket(af, socktype, proto)
                sock.settimeout(self.mpd_timeout)
                sock.connect(sa)
                sock.settimeout(self.socket_timeout)
                return sock
            except socket.error as socket_err:
                log.debug('opening socket %s failed: %s', sa, socket_err)
                err = socket_err
                if sock is not None:
                    sock.close()
        if err is not None:
            raise ConnectionError(err)
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

        :param str host: hostname, IP or FQDN (defaults to *localhost* or socket)
        :param port: port number (defaults to *6600*)
        :type port: str or int

        If host/port are :py:obj:`None` the socket uses :py:attr:`host`/:py:attr:`port`
        attributes as defaults. Cf. :py:obj:`MPDClient` for the logic behind default host/port.

        The underlying socket also honors :envvar:`MPD_TIMEOUT` environment variable
        and defaults to :py:obj:`musicpd.CONNECTION_TIMEOUT` (connect command only).

        If you want to have a timeout for each command once you got connected,
        set its value in :py:obj:`MPDClient.socket_timeout` (in second) or at
        module level in :py:obj:`musicpd.SOCKET_TIMEOUT`.
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
            log.debug('Connecting unix socket %s', host)
            self._sock = self._connect_unix(host)
        else:
            log.debug('Connecting tcp socket %s:%s (timeout: %ss)', host, port, self.mpd_timeout)
            self._sock = self._connect_tcp(host, port)
        self._rfile = self._sock.makefile("r", encoding='utf-8', errors='surrogateescape')
        self._rbfile = self._sock.makefile("rb")
        self._wfile = self._sock.makefile("w", encoding='utf-8')
        try:
            self._hello()
        except:
            self.disconnect()
            raise
        log.debug('Connected')

    @property
    def socket_timeout(self):
        """Socket timeout in second (defaults to :py:obj:`SOCKET_TIMEOUT`).
        Use :py:obj:`None` to disable socket timout.

        :setter: Set the socket timeout (integer > 0)
        :type: int or None
        """
        return self._socket_timeout

    @socket_timeout.setter
    def socket_timeout(self, timeout):
        if timeout is not None:
            if int(timeout) <= 0:
                raise ValueError('socket_timeout expects a non zero positive integer')
            self._socket_timeout = int(timeout)
        else:
            self._socket_timeout = timeout
        if getattr(self._sock, 'settimeout', False):
            self._sock.settimeout(self._socket_timeout)


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

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.disconnect()

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
            raise PendingCommandError("Cannot begin command list with pending commands")
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
