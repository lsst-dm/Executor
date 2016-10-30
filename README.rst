Executor
========

A wrapper allowing to run the LSST tasks in arbitrary locations.

Prerequisites
-------------

To use ``Executor`` you have to have access to a working LSST Stack
installation.

Installation
------------

At the moment there is no automated installation procedure. To begin using
``Executor`` clone project's repository to a directory of choice::

    $ git clone git@github.com:mxk62/Executor.git

Then add ``$DIR/Executor`` and ``$DIR/Executor/bin`` to your ``PYTHONPATH`` and ``PATH`` respectively.


Generating documentation
------------------------

To generate project's documentation you need `sphinx`_ with `numpydoc`_
extension. Once you have them installed on your system, go to
``$DIR/Executor/docs`` and run::

   $ make html

Then open ``$DIR/Executor/docs/_build/html/index.html`` in your favourite
browser.


.. _sphinx: https://pypi.python.org/pypi/Sphinx
.. _numpydoc: https://pypi.python.org/pypi/numpydoc

