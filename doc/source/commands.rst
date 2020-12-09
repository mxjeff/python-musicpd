.. _commands:

Available commands
==================

Get current available commands:

.. code-block:: python

   import musicpd
   print(' '.join([cmd for cmd in musicpd.MPDClient()._commands.keys()]))


List, last updated for v0.4.5:

.. literalinclude:: commands.txt
