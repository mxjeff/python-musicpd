.. include:: ../../README.rst

Installation
=============

**Latest stable release** from `PyPi <https://pypi.org/project/python-musicpd/>`_:

.. code:: bash

   pip install python-musicpd

**Latest development version** using pip + git:

.. code:: bash

    pip install git+https://gitlab.com/kaliko/python-musicpd.git



Build documentation
--------------------

.. code:: bash

    # Get the source
    git clone https://gitlab.com/kaliko/python-musicpd.git && cd python-musicpd
    # Installs sphinx if needed
    python3 -m venv venv && . ./venv/bin/activate
    pip install sphinx
    # And build
    python3 setup.py build_sphinx
    # Or call sphinx
    sphinx-build -d ./doc/build/doctrees doc/source -b html ./doc/build/html


Contents
=========

.. toctree::
   :maxdepth: 2

   use.rst
   doc.rst
   contribute.rst


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. vim: spell spelllang=en
