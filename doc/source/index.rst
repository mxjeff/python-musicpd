.. SPDX-FileCopyrightText: 2018-2023  kaliko <kaliko@azylum.org>
.. SPDX-License-Identifier: LGPL-3.0-or-later

.. include:: ../../README.rst

Installation
=============

**Latest stable release** from `PyPi <https://pypi.org/project/python-musicpd/>`_:

.. code:: bash

   pip install python-musicpd

**Latest development version** using pip + git:

.. code:: bash

    pip install git+https://gitlab.com/kaliko/python-musicpd.git@dev


Library overview
================
Here is a snippet allowing to list the last modified artists in the media library:

.. code:: python3

        #!/usr/bin/env python3
        # coding: utf-8
        import musicpd

        def main():
            cli = musicpd.MPDClient()
            cli.connect()
            # Gets files count in the library
            nb_files = int(cli.stats()['songs'])
            # Gets the last 100 files modified
            files = cli.search('file', '', 'sort', 'Last-Modified', 'window', (nb_files-100,))
            # Print last modified artists in media library
            print(' / '.join({f.get('albumartist') for f in files}))
            cli.disconnect()

        # Script starts here
        if __name__ == '__main__':
            main()


Build documentation
===================

.. code:: bash

    # Get the source
    git clone https://gitlab.com/kaliko/python-musicpd.git && cd python-musicpd
    # Installs sphinx if needed
    python3 -m venv venv && . ./venv/bin/activate
    pip install sphinx
    # Call sphinx
    sphinx-build -d ./doc/build/doctrees doc/source -b html ./doc/build/html


Contents
=========

.. toctree::
   :maxdepth: 2

   self
   use.rst
   doc.rst
   examples.rst
   commands.rst
   contribute.rst


Indices and tables
==================

* :ref:`genindex`
* :ref:`search`


.. vim: spell spelllang=en
