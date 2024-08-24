.. SPDX-FileCopyrightText: 2018-2023  kaliko <kaliko@azylum.org>
.. SPDX-License-Identifier: LGPL-3.0-or-later

Using the client library
=========================

Introduction
------------

The client library can be used as follows:

.. code-block:: python

    client = musicpd.MPDClient()       # create client object
    client.connect()                   # use MPD_HOST/MPD_PORT if set else
                                       #   test ${XDG_RUNTIME_DIR}/mpd/socket for existence
                                       #   fallback to localhost:6600
                                       # connect support host/port argument as well
    print(client.mpd_version)          # print the MPD protocol version
    client.setvol('42')                # sets the volume
    client.disconnect()                # disconnect from the server

The MPD command protocol exchanges line-based text records. The client emits a
command with optional arguments. In the example above the client sends a
`setvol` command with the string argument `42`.

MPD commands are exposed as :py:class:`musicpd.MPDClient` methods. Methods
**arguments are python strings**. Some commands are composed of more than one word
(ie "**tagtypes [disable|enable|all]**"), for these use a `snake case`_ style to
access the method. Then **"tagtypes enable"** command is called with
**"tagtypes_enable"**.

Remember MPD protocol is text based, then all MPD command arguments are UTF-8
strings. In the example above, an integer can be used as argument for the
`setvol` command, but it is then evaluated as a string when the command is
written to the socket. To avoid confusion use regular string instead of relying
on object string representation.

:py:class:`musicpd.MPDClient` methods returns different kinds of objects
depending on the command. Could be :py:obj:`None`, a single object as a
:py:obj:`str`, a :py:obj:`list`, a :py:obj:`dict` or a list of :py:obj:`dict`.
See :ref:`commands exposed in the module<commands>` for more about returned
type.

Then :py:class:`musicpd.MPDClient` **methods signatures** are not hard coded
within this module since the protocol is handled on the server side. Please
refer to the protocol and MPD commands in `MPD protocol documentation`_ to
learn how to call commands and what kind of arguments they expect.

Some examples are provided for the most common cases, see :ref:`examples`.

For a list of currently supported commands in this python module see
:ref:`commands`.

.. _environment_variables:

Environment variables
---------------------

:py:class:`musicpd.MPDClient` honors the following environment variables:

.. envvar:: MPD_HOST

   MPD host (:abbr:`FQDN (fully qualified domain name)`, IP, socket path or abstract socket) and password.

    | To define a **password** set :envvar:`MPD_HOST` to "*password@host*" (password only "*password@*")
    | For **abstract socket** use "@" as prefix : "*@socket*" and then with a password  "*pass@@socket*"
    | Regular **unix socket** are set with an absolute path: "*/run/mpd/socket*"

.. envvar:: MPD_PORT

   MPD port, relevant for TCP socket only

.. envvar:: MPD_TIMEOUT

   socket timeout when connecting to MPD and waiting for MPD’s response (in seconds)

.. envvar:: XDG_RUNTIME_DIR

   path to look for potential socket

.. _default_settings:

Default settings
----------------

Default host:
 * use :envvar:`MPD_HOST` environment variable if set, extract password if present,
 * else use :envvar:`XDG_RUNTIME_DIR` to looks for an existing file in ``${XDG_RUNTIME_DIR}/mpd/socket``, :envvar:`XDG_RUNTIME_DIR` defaults to ``/run`` if not set.
 * else set host to ``localhost``

Default port:
 * use :envvar:`MPD_PORT` environment variable if set
 * else use ``6600``

Default timeout:
 * use :envvar:`MPD_TIMEOUT` if set
 * else use :py:obj:`musicpd.CONNECTION_TIMEOUT`

Context manager
---------------

Calling MPDClient in a context manager :py:obj:`musicpd.MPDClient.connect` is
transparently called with :ref:`default setting<default_settings>` (use
:ref:`environment variables<environment_variables>` to override defaults).
Leaving the context manager :py:obj:`musicpd.MPDClient.disconnect` is called.

.. code-block:: python

    import os
    os.environ['MPD_HOST'] = 'mpdhost'
    with MPDClient() as c:
        c.status()
        c.next()

Command lists
-------------

Command lists are also supported using `command_list_ok_begin()` and
`command_list_end()` :

.. code-block:: python

    client.command_list_ok_begin()       # start a command list
    client.update()                      # insert the update command into the list
    client.status()                      # insert the status command into the list
    results = client.command_list_end()  # results will be a list with the results

Ranges
------

Some commands (e.g. delete) allow specifying a range in the form `"START:END"` (cf. `MPD protocol documentation`_ for more details).

Possible ranges are: `"START:END"`, `"START:"` and `":"` :

Instead of giving the plain string as `"START:END"`, you **can** provide a :py:obj:`tuple` as `(START,END)`. The module is then ensuring the format is correct and raises an :py:obj:`musicpd.CommandError` exception otherwise. Empty start or end can be specified as en empty string ``''`` or :py:obj:`None`.

.. code-block:: python

    # An intelligent clear
    # clears played track in the queue, currentsong included
    pos = client.currentsong().get('pos', 0)
    # the range object accepts str, no need to convert to int
    client.delete((0, pos))
    # missing end interpreted as highest value possible, pay attention still need a tuple.
    client.delete((pos,))  # purge queue from current to the end

A notable case is the *rangeid* command allowing an empty range specified
as a single colon as argument (i.e. sending just ``":"``):

.. code-block:: python

    # sending "rangeid :" to clear the range, play everything
    client.rangeid(())  # send an empty tuple

Empty start in range (i.e. ":END") are not possible and will raise a CommandError.

.. note:: Remember the use of a tuple is **optional**. Range can still be specified as a plain string ``"START:END"``.

Iterators
----------

Commands may also return iterators instead of lists if `iterate` is set to
`True`:

.. code-block:: python

    client.iterate = True
    for song in client.playlistinfo():
        print song['file']

Idle prefixed commands
----------------------

Each command have a *send\_<CMD>* and a *fetch\_<CMD>* variant, which allows to
send a MPD command and then fetch the result later (non-blocking call).
This is useful for the idle command:

.. code-block:: python

    >>> client.send_idle()
    # do something else or use function like select()
    # http://docs.python.org/howto/sockets.html#non-blocking-sockets
    # ex. select([client], [], [])
    >>> events = client.fetch_idle()

    # more complex use for example, with glib/gobject:
    >>> def callback(source, condition):
    >>>    changes = client.fetch_idle()
    >>>    print changes
    >>>    return False  # removes the IO watcher

    >>> client.send_idle()
    >>> gobject.io_add_watch(client, gobject.IO_IN, callback)
    >>> gobject.MainLoop().run()

See also use of :ref:`socket timeout<socket_timeout>` with idle command.

Fetching binary content (cover art)
-----------------------------------

Fetching album covers is possible with albumart, here is an example:

.. code-block:: python

    >>> cli = musicpd.MPDClient()
    >>> cli.connect()
    >>> track = "Steve Reich/1978-Music for 18 Musicians"
    >>> aart = cli.albumart(track, 0)
    >>> received = int(aart.get('binary'))
    >>> size = int(aart.get('size'))
    >>> with open('/tmp/cover', 'wb') as cover:
    >>>     # aart = {'size': 42, 'binary': 2051, data: bytes(...)}
    >>>     cover.write(aart.get('data'))
    >>>     while received < size:
    >>>         aart = cli.albumart(track, received)
    >>>         cover.write(aart.get('data'))
    >>>         received += int(aart.get('binary'))
    >>>     if received != size:
    >>>         print('something went wrong', file=sys.stderr)
    >>> cli.disconnect()

A :py:obj:`musicpd.CommandError` is raised if the album does not expose a cover.

You can also use `readpicture` command to fetch embedded picture:

.. code-block:: python

    >>> cli = musicpd.MPDClient()
    >>> cli.connect()
    >>> track = 'muse/Amon Tobin/2011-ISAM/01-Amon Tobin - Journeyman.mp3'
    >>> rpict = cli.readpicture(track, 0)
    >>> if not rpict:
    >>>     print('No embedded picture found', file=sys.stderr)
    >>>     sys.exit(1)
    >>> size = int(rpict['size'])
    >>> done = int(rpict['binary'])
    >>> with open('/tmp/cover', 'wb') as cover:
    >>>     cover.write(rpict['data'])
    >>>     while size > done:
    >>>         rpict = cli.readpicture(track, done)
    >>>         done += int(rpict['binary'])
    >>>         print(f'writing {rpict["binary"]}, done {100*done/size:03.0f}%')
    >>>         cover.write(rpict['data'])
    >>> cli.disconnect()

Refer to `MPD protocol documentation`_ for the meaning of `binary`, `size` and `data`.

.. _socket_timeout:

Socket timeout
--------------

.. note::
  When the timeout is reached it raises a :py:obj:`socket.timeout` exception. An :py:obj:`OSError` subclass.

A timeout is used for the initial MPD connection (``connect`` command), then
the socket is put in blocking mode with no timeout. Its value is set in
:py:obj:`musicpd.CONNECTION_TIMEOUT` at module level and
:py:obj:`musicpd.MPDClient.mpd_timeout` in MPDClient instances . However it
is possible to set socket timeout for all command setting
:py:obj:`musicpd.MPDClient.socket_timeout` attribute to a value in second.

Having ``socket_timeout`` enabled can help to detect "half-open connection".
For instance loosing connectivity without the server explicitly closing the
connection (switching network interface ethernet/wifi, router down, etc…).

**Nota bene**: with ``socket_timeout`` enabled each command sent to MPD might
timeout. A couple of seconds should be enough for commands to complete except
for the special case of ``idle`` command which by definition *“ waits until
there is a noteworthy change in one or more of MPD’s subsystems.”* (cf. `MPD
protocol documentation`_).

Here is a solution to use ``idle`` command with ``socket_timeout``:

.. code-block:: python

    import musicpd
    import select
    import socket

    cli = musicpd.MPDClient()
    try:
        cli.socket_timeout = 10  # seconds
        select_timeout = 5 # second
        cli.connect()
        while True:
            cli.send_idle()  # use send_ API to avoid blocking on read
            _read, _, _ = select.select([cli], [], [], select_timeout)
            if _read:  # tries to read response
                ret = cli.fetch_idle()
                print(', '.join(ret))  # Do something
            else: # cancels idle
                cli.noidle()
    except socket.timeout as err:
        print(f'{err} (timeout {cli.socket_timeout})')
    except (OSError, musicpd.MPDError) as err:
        print(f'{err!r}')
        if cli._sock is not None:
            cli.disconnect()
    except KeyboardInterrupt:
        pass

Some explanations:

  * First launch a non blocking ``idle`` command. This call do not wait for a
    response to avoid socket timeout waiting for an MPD event.
  * ``select`` waits for something to read on the socket (the idle response
    in this case), returns after ``select_timeout`` seconds anyway.
  * In case there is something to read read it using ``fetch_idle``
  * Nothing to read, cancel idle with ``noidle``

All three commands in the while loop (send_idle, fetch_idle, noidle) are not
triggering a socket timeout unless the connection is actually lost (actually it
could also be that MPD took too much time to answer, but MPD taking more than a
couple of seconds for these commands should never occur).

.. _exceptions:

Exceptions
----------

The :py:obj:`connect<musicpd.MPDClient.connect>` method raises
:py:obj:`ConnectionError<musicpd.ConnectionError>` only (an :py:obj:`MPDError<musicpd.MPDError>` exception) but then, calling other MPD commands, the module can raise
:py:obj:`MPDError<musicpd.MPDError>` or an :py:obj:`OSError` depending on the error and
where it occurs.

Then using musicpd module both :py:obj:`musicpd.MPDError` and :py:obj:`OSError`
exceptions families are expected, see :ref:`examples<exceptions_example>` for a
way to deal with this.

.. _MPD protocol documentation: http://www.musicpd.org/doc/protocol/
.. _snake case: https://en.wikipedia.org/wiki/Snake_case
.. vim: spell spelllang=en
