.. Executor documentation master file, created by
   sphinx-quickstart on Sun Oct 30 16:43:59 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Executor's documentation!
====================================

.. toctree::
   :caption: Table of Contents
   :maxdepth: 2

Introduction
============

With few exceptions, all LSST tasks science pipelines consists of use **data
butler** [`ref`__] for performing I/O operations.  The data butler stores
datasets (persisted forms of in-memory objects) and associated metadata in
**dataset repositories**.  This design implies that both tasks' input and
output data resides exclusively in dataset repositories.  Thus you can't run a
task unless you have one.

From an LSST developer's perspective, creating an input dataset repository
*from scratch* is a rare event and presence of excessive data in it is hardly a
matter of concern.  In contrast, due to its distributed architecture, in the
LSST production environment dataset repositories are created frequently with
very specific data. 

The primary goal of ``Executor`` is to create locally a minimal dataset
repository allowing a given LSST task to run and collects data of interest
after the it is finished.  Specifically, ``Executor`` will:

1. create a butler repository initializing an appropriate mapper;

2. ingest the input data to the repository and, optionally, required
   calibration files;

3. start the task;

4. collect output and metadata, logs, provenance data after the task is
   finished.

.. __: https://confluence.lsstcorp.org/display/DM/Data+Butler+Product+Definition

Prerequisites
=============

``Executor`` is merely a wrapper. To run tasks with its help you have to
have the LSST Stack installed and properly configured on your computer.
Installation of the LSST Stack is beyond the scope of this document, but fairly
complete instructions can be found `here`__.

.. note::
   At the moment, ``Executor`` works only with HSC mapper so you need to
   install ``obs_subaru`` package and its dependencies as well.

   
Once you have the Stack installed, setup the required packages:

.. code-block:: bash

   $ setup pipe_tasks
   $ setup obs_subaru

and you're good to go.

.. __: https://developer.lsst.io/build-ci/lsstsw.html

Installation
============

Currently ``Executor`` has no no automated installation procedure. To begin
using it, clone project's repository to a directory of choice:

.. code-block:: bash

   $ git clone git@github.com:mxk62/Executor.git

and update your ``PYTHONPATH`` and ``PATH`` variables

.. code-block:: bash

   export PYTHONPATH="$PYTHONPATH:$DIR/Executor"
   export PATH="$PATH:$DIR/Executor/bin"

where ``$DIR`` is the directory you've cloned the repository to.

Getting started
===============

Normally, to run an LSST task, e.g. ``processCcd``, you would type

.. code-block:: bash

   processCcd $REPO --id visit=904010 ccd=4 --output /tmp/output

where ``$REPO`` is a location of *a pre-existing* data butler repository.
However, if all you have is a bunch of files you can use ``Executor`` to make
it create one for you at the specified location, providing you give it some
hints about the nature of the files:  

.. code-block:: bash

   $ execute processCcd /tmp/repo HSCA90401142.fits \
   --bias BIAS-2013-11-03-004.fits --dark DARK-2013-11-03-004.fits \
   --flat FLAT-2013-11-03-HSC-I-004.fits --kernel brighter_fatter_kernel.pkl \
   --extras --id visit=904010 ccd=4 --output /tmp/output

The command above will initialize a data butler repository in ``/tmp/repo``,
ingest the data file ``HSCA90401142.fits``, required calibration files:
``BIAS-2013-11-03-004.fits``, ``DARK-2013-11-03-004.fits``,
``FLAT-2013-11-03-HSC-I-004.fits``, ``brighter_fatter_kernel.pkl`` and finally
run the ``processCcd``.

.. note::

   Note that all task specific options (if any) **must** follow the
   ``--extras`` option.

.. warning::

   By default, ``processCcd`` when run against HSC data repository will try to
   use atronometry reference catalog.  However, getting it work wih HSC data
   repositories seems to be a bit `tricky`__ and is not supported by
   ``Executor`` at the moment. To disable this feature, override default
   configuration by using following configuration overrides in
   ``$LSSTSW/build/obs_subaru/config/processCcd.py``

   .. code-block:: python

      calibrate.doPhotoCal = False
      calibrate.doAstrometry = False
      config.calibrate.requireAstrometry = False
      config.calibrate.requirePhotoCal = False
      config.calibrate.photoCal.applyColorTerms = False

   and commenting out line with ``setConfigFromEups``. Then make sure that
   ``processCcd`` will use the modified configuration

   .. code-block:: bash

      $ setup -r $LSSTSW/build/obs_subaru

.. __: https://jira.lsstcorp.org/browse/DM-5135

Using Executor
==============

Under construction.

Developer's corner
==================

Under construction.

Reference
=========

.. automodule:: executor.commands
   :members:

.. automodule:: executor.invoker
   :members:

.. automodule:: executor.mapper
   :members:


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

