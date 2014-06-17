==============
python-musicpd
==============

Getting python-musicpd
----------------------

The latest release of python-musicpd can be found at
http://pypi.python.org/pypi/python-musicpd.


Getting the latest source code
------------------------------

If you would instead like to use the latest source code, you can grab a copy
of the development version from git by running the command:

  git clone git://git.kaliko.me/python-musicpd.git


Installing from source
----------------------

To install python-musicpd from source, simply run the command::

  python3 setup.py install

You can use the `--help` switch to `setup.py` for a complete list of commands
and their options.  See the `Installing Python Modules`_ document for more details.


Using the client library
------------------------

The client library can be used as follows::

    client = musicpd.MPDClient()       # create client object
    client.connect('localhost', 6600)  # connect to localhost:6600
    print client.mpd_version           # print the mpd version
    print client.cmd('one', 2)         # print result of the command "cmd one 2"
    client.close()                     # send the close command
    client.disconnect()                # disconnect from the server

A list of supported commands, their arguments (as MPD currently understands
them), and the functions used to parse their responses can be found in
`doc/commands.txt`.  See the `MPD protocol documentation`_ for more
details.

Command lists are also supported using `command_list_ok_begin()` and
`command_list_end()` ::

    client.command_list_ok_begin()       # start a command list
    client.update()                      # insert the update command into the list
    client.status()                      # insert the status command into the list
    results = client.command_list_end()  # results will be a list with the results


Commands may also return iterators instead of lists if `iterate` is set to
`True`::

    client.iterate = True
    for song in client.playlistinfo():
        print song['file']

Each command have a *send\_<CMD>* and a *fetch\_<CMD>* variant, which allows to
send a MPD command and then fetch the result later.
This is useful for the idle command::

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

Contacting authors
------------------

You can contact the original author by emailing J. Alexander Treuman
<jat⊘spatialrift.net>.  He can also be found idling in #mpd on
irc.freenode.net as jat.

The current maintainer can be found on xmpp chat room <kaliko.me⊘conf.azylum.org>
or you can contact him by email/xmpp <kaliko⊘azylum.org>.

 .. _Installing Python Modules: http://docs.python.org/3/install/
 .. _MPD protocol documentation: http://www.musicpd.org/doc/protocol/
