Contributing
=============

Use git, `learn if needed`_.

Git Workflow
-------------
* ``master`` branch holds latest stable|release code
* ``dev`` branch holds current development code
* Work on a dedicated branch starting off ``dev``
* I like fast forward merges, **please rebase on** ``dev`` branch before submitting changes
* Advertise your work (cf. Note)

.. NOTE::
    **Git merge Workflow** |br|
    I currently don't care about a specific workflow concerning changes submission. |br|
    Don't bother with gitlab merge request or gh pull request. |br|
    All we need is a public git repo and a ref to fetch from as long you rebased on ``dev`` branch.

Coding
-------

* follow pep8
* write unittest
* actually test your code (unit and functional testing)


.. _`learn if needed`: https://git-scm.com/book/

.. |br| raw:: html

    <br />

.. vim: spell spelllang=en
