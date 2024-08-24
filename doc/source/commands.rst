.. SPDX-FileCopyrightText: 2018-2024 kaliko <kaliko@azylum.org>
.. SPDX-License-Identifier: LGPL-3.0-or-later

.. _commands:

Available commands
==================

Get current available commands:

.. code-block:: python

   import musicpd
   print(' '.join([cmd for cmd in musicpd.MPDClient()._commands.keys()]))

.. include:: _commands.rst
