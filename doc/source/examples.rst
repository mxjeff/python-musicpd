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

