Using the client library
=========================

The client library can be used as follows:

.. code-block:: python

    client = musicpd.MPDClient()       # create client object
    client.connect()                   # use MPD_HOST/MPD_PORT if set else
                                       #   test ${XDG_RUNTIME_DIR}/mpd/socket for existence
                                       #   fallback to localhost:6600
                                       # connect support host/port argument as well
    print(client.mpd_version)          # print the mpd protocol version
    print(client.cmd('one', 2))        # print result of the command "cmd one 2"
    client.disconnect()                # disconnect from the server

For a list of supported commands, their arguments (as MPD currently understands
them), and the functions used to parse their responses see :ref:`commands`.

See the `MPD protocol documentation`_ for more details.

Command lists are also supported using `command_list_ok_begin()` and
`command_list_end()` :

.. code-block:: python

    client.command_list_ok_begin()       # start a command list
    client.update()                      # insert the update command into the list
    client.status()                      # insert the status command into the list
    results = client.command_list_end()  # results will be a list with the results

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


Commands may also return iterators instead of lists if `iterate` is set to
`True`:

.. code-block:: python

    client.iterate = True
    for song in client.playlistinfo():
        print song['file']

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


.. _MPD protocol documentation: http://www.musicpd.org/doc/protocol/
