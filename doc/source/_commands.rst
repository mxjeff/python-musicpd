Below the commands list last updated for v0.9.1.

Querying MPD’s status
^^^^^^^^^^^^^^^^^^^^^

Protocol documentation: `Querying MPD’s status <https://mpd.readthedocs.io/en/latest/protocol.html#querying-mpd-s-status>`_

* **clearerror** -> None
* **currentsong** -> dict
* **idle** -> list
* **status** -> dict
* **stats** -> dict

Playback Option
^^^^^^^^^^^^^^^

Protocol documentation: `Playback Option <https://mpd.readthedocs.io/en/latest/protocol.html#playback-options>`_

* **consume** -> None
* **crossfade** -> None
* **mixrampdb** -> None
* **mixrampdelay** -> None
* **random** -> None
* **repeat** -> None
* **setvol** -> None
* **getvol** -> dict
* **single** -> None
* **replay_gain_mode** -> None
* **replay_gain_status** -> str
* **volume** -> None

Controlling playback
^^^^^^^^^^^^^^^^^^^^

Protocol documentation: `Controlling playback <https://mpd.readthedocs.io/en/latest/protocol.html#controlling-playback>`_

* **next** -> None
* **pause** -> None
* **play** -> None
* **playid** -> None
* **previous** -> None
* **seek** -> None
* **seekid** -> None
* **seekcur** -> None
* **stop** -> None

The Queue
^^^^^^^^^

Protocol documentation: `The Queue <https://mpd.readthedocs.io/en/latest/protocol.html#the-queue>`_

* **add** -> None
* **addid** -> str
* **clear** -> None
* **delete** -> None
* **deleteid** -> None
* **move** -> None
* **moveid** -> None
* **playlist** -> list
* **playlistfind** -> list[dict]
* **playlistid** -> list[dict]
* **playlistinfo** -> list[dict]
* **playlistsearch** -> list[dict]
* **plchanges** -> list[dict]
* **plchangesposid** -> list[dict]
* **prio** -> None
* **prioid** -> None
* **rangeid** -> None
* **shuffle** -> None
* **swap** -> None
* **swapid** -> None
* **addtagid** -> None
* **cleartagid** -> None

Stored playlists
^^^^^^^^^^^^^^^^

Protocol documentation: `Stored playlists <https://mpd.readthedocs.io/en/latest/protocol.html#stored-playlists>`_

* **listplaylist** -> list
* **listplaylistinfo** -> list[dict]
* **listplaylists** -> dict
* **load** -> None
* **playlistadd** -> None
* **playlistclear** -> None
* **playlistdelete** -> None
* **playlistlength** -> dict
* **playlistmove** -> None
* **rename** -> None
* **rm** -> None
* **save** -> None

The music database
^^^^^^^^^^^^^^^^^^

Protocol documentation: `The music database <https://mpd.readthedocs.io/en/latest/protocol.html#the-music-database>`_

* **albumart** -> dict
* **count** -> dict
* **getfingerprint** -> dict
* **find** -> list[dict]
* **findadd** -> None
* **list** -> list
* **listall** -> list[dict]
* **listallinfo** -> list[dict]
* **listfiles** -> list[dict]
* **lsinfo** -> list[dict]
* **readcomments** -> dict
* **readpicture** -> dict
* **search** -> list[dict]
* **searchadd** -> None
* **searchaddpl** -> None
* **searchcount** -> dict
* **update** -> str
* **rescan** -> str

Mounts and neighbors
^^^^^^^^^^^^^^^^^^^^

Protocol documentation: `Mounts and neighbors <https://mpd.readthedocs.io/en/latest/protocol.html#mounts-and-neighbors>`_

* **mount** -> None
* **unmount** -> None
* **listmounts** -> list[dict]
* **listneighbors** -> list[dict]

Stickers
^^^^^^^^

Protocol documentation: `Stickers <https://mpd.readthedocs.io/en/latest/protocol.html#stickers>`_

* **sticker get** -> str
* **sticker set** -> None
* **sticker delete** -> None
* **sticker list** -> list
* **sticker find** -> list[dict]
* **stickernames** -> list

Connection settings
^^^^^^^^^^^^^^^^^^^

Protocol documentation: `Connection settings <https://mpd.readthedocs.io/en/latest/protocol.html#connection-settings>`_

* **password** -> None
* **ping** -> None
* **binarylimit** -> None
* **tagtypes** -> list
* **tagtypes disable** -> None
* **tagtypes enable** -> None
* **tagtypes clear** -> None
* **tagtypes all** -> None

Partition Commands
^^^^^^^^^^^^^^^^^^

Protocol documentation: `Partition Commands <https://mpd.readthedocs.io/en/latest/protocol.html#partition-commands>`_

* **partition** -> None
* **listpartitions** -> list
* **newpartition** -> None
* **delpartition** -> None
* **moveoutput** -> None

Audio output devices
^^^^^^^^^^^^^^^^^^^^

Protocol documentation: `Audio output devices <https://mpd.readthedocs.io/en/latest/protocol.html#audio-output-devices>`_

* **disableoutput** -> None
* **enableoutput** -> None
* **toggleoutput** -> None
* **outputs** -> list[dict]
* **outputset** -> None

Reflection
^^^^^^^^^^

Protocol documentation: `Reflection <https://mpd.readthedocs.io/en/latest/protocol.html#reflection>`_

* **config** -> dict
* **commands** -> list
* **notcommands** -> list
* **urlhandlers** -> list
* **decoders** -> list[dict]

Client to Client
^^^^^^^^^^^^^^^^

Protocol documentation: `Client to Client <https://mpd.readthedocs.io/en/latest/protocol.html#client-to-client>`_

* **subscribe** -> None
* **unsubscribe** -> None
* **channels** -> list
* **readmessages** -> list[dict]
* **sendmessage** -> None
