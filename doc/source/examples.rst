.. SPDX-FileCopyrightText: 2018-2023 kaliko <kaliko@azylum.org>
.. SPDX-License-Identifier: LGPL-3.0-or-later

.. _examples:

Examples
========

Plain examples
--------------

Connect, if playing, get currently playing track, the next one:

.. literalinclude:: examples/connect.py
   :language: python
   :linenos:

Connect a specific password protected host:

.. literalinclude:: examples/connect_host.py
   :language: python
   :linenos:

Start playing current queue and set the volume:

.. literalinclude:: examples/playback.py
   :language: python
   :linenos:

Clear the queue, search artist, queue what's found and play:

.. literalinclude:: examples/findadd.py
   :language: python
   :linenos:

Object Oriented example
-----------------------

A plain client monitoring changes on MPD.

.. literalinclude:: examples/client.py
   :language: python
   :linenos:

.. _exceptions_example:

Dealing with Exceptions
-----------------------

Musicpd module will raise it's own :py:obj:`MPDError<musicpd.MPDError>`
exceptions **and** python :py:obj:`OSError`. Then you can wrap
:py:obj:`OSError` in :py:obj:`MPDError<musicpd.MPDError>` exceptions to have to deal
with a single type of exceptions in your code:

.. literalinclude:: examples/exceptions.py
   :language: python
   :linenos:
