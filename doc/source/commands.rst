.. SPDX-FileCopyrightText: 2018-2021  kaliko <kaliko@azylum.org>
.. SPDX-License-Identifier: GPL-3.0-or-later

.. _commands:

Available commands
==================

Get current available commands:

.. code-block:: python

   import musicpd
   print(' '.join([cmd for cmd in musicpd.MPDClient()._commands.keys()]))


List, last updated for v0.6.0:

.. literalinclude:: commands.txt
