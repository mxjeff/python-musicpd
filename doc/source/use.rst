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
    print(client.mpd_version)          # print the mpd protocol version
    print(client.cmd('foo', 42))       # print result of the request "cmd foo 42"
                                       # (nb. for actual command, see link to the protocol below)
    client.disconnect()                # disconnect from the server

In the example above `cmd` in not an actual MPD command, for a list of
supported commands, their arguments (as MPD currently understands
them), and the functions used to parse their responses see :ref:`commands`.

See the `MPD protocol documentation`_ for more details.

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

Provide a 2-tuple as argument for command supporting ranges (cf. `MPD protocol documentation`_ for more details).
Possible ranges are: "START:END", "START:" and ":" :

.. code-block:: python

    # An intelligent clear
    # clears played track in the queue, currentsong included
    pos = client.currentsong().get('pos', 0)
    # the 2-tuple range object accepts str, no need to convert to int
    client.delete((0, pos))
    # missing end interpreted as highest value possible, pay attention still need a tuple.
    client.delete((pos,))  # purge queue from current to the end

A notable case is the `rangeid` command allowing an empty range specified
as a single colon as argument (i.e. sending just ":"):

.. code-block:: python

    # sending "rangeid :" to clear the range, play everything
    client.rangeid(())  # send an empty tuple

Empty start in range (i.e. ":END") are not possible and will raise a CommandError.

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
send a MPD command and then fetch the result later.
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

A `CommandError` is raised if the album does not expose a cover.

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

.. _MPD protocol documentation: http://www.musicpd.org/doc/protocol/
