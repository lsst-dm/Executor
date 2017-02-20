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

With few exceptions, all LSST tasks science pipelines use **data butler**
[`ref`__] for performing I/O operations.  The data butler stores datasets
(persisted forms of in-memory objects) and associated metadata in **dataset
repositories**.  This design implies that both tasks' input and output data
resides exclusively in dataset repositories.  Thus you can't run a task unless
you have one.

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

    $ git clone git@github.com:lsst-dm/Executor.git

and update your ``PYTHONPATH`` and ``PATH``:

.. code-block:: bash

   export PYTHONPATH="$PYTHONPATH:$DIR/Executor"
   export PATH="$PATH:$DIR/Executor/bin"

where ``$DIR`` is the directory you've cloned the repository to.

Getting started
===============

Normally, to run an LSST task, e.g. ``processCcd``, you would type

.. code-block:: bash

   $ processCcd /tmp/input --id visit=904010 ccd=4 --output /tmp/output

where ``/tmp/input`` is the location of *a pre-existing* dataset repository.

You can do the same with ``Executor``

.. code-block:: bash

   $ execute processCcd.json

where ``processCcd.json`` is job specification in JSON format:

.. code-block:: json

   {
       "task": {
           "name": "processCcd",
           "args": [ "--id", "visit=904010", "ccd=4" ]
       },
       "input": {
           "root": "/tmp/input"
       },
       "output": {
           "root": "/tmp/output"
       }
   }

Though it looks like a lot of extra work, the example above only shows that you
can use ``Executor`` even if your data sit already in a dataset repository.

Keep in mind though that ``Executors``'s primary goal is to launch an LSST task
when you don't have this luxury and all you have at hand is a bunch of files.
In such a case, ``Executor`` will make one for you providing you give it some
hints.  For example, if you modify the ``processCcd.json`` as below

.. code-block:: json
   :emphasize-lines: 8,13-20

   {
       "task": {
           "name": "processCcd",
           "args": [ "--id", "visit=904010", "ccd=4" ]
       },
       "input": {
           "root"; "/tmp/input",
           "mapper": "lsst.obs.hsc.HscMapper"
       },
       "output": {
           "root": "/tmp/output"
       },
       "data": [
           {
               "pfn": "HSCA90401142.fits",
               "meta": {
                   "type": "raw"
               }
           }
       ]
   }

and run ``execute processCcd.json`` again, ``Executor`` will:

1. create the dataset repository root, i.e., ``/tmp/input``,
2. set the mapper to use (line 8),
3. ingest file ``HSCA90401142.fits`` to the repository (lines 10-15), and
   finally,
4. run ``processCcd`` with specified data ids.

Though don't do it yet! Beside the data files, you will need to ingest a few
calibration files as well:

.. code-block:: json
   :emphasize-lines: 21-

   {
       "task": {
           "name": "processCcd",
           "args": [ "--id", "visit=904010", "ccd=4" ]
       },
       "input": {
           "root"; "/tmp/input",
           "mapper": "lsst.obs.hsc.HscMapper"
       },
       "output": {
           "root": "/tmp/output"
       },
       "data": [
           {
               "pfn": "HSCA90401142.fits",
               "meta": {
                   "type": "raw"
               }
           }
       ],
       "calibs": [
           {
               "pfn": "BIAS-2013-11-03-004.fits",
               "meta": {
                   "type": "bias",
                   "validity": 999,
                   "calibDate": "2013-11-03",
                   "ccd": 4,
                   "template": "CALIB/BIAS/{calibDate:s}/NONE/BIAS-{calibDate:s}-{ccd:03d}.fits"
               }
           },
           {
               "pfn": "DARK-2013-11-03-004.fits",
               "meta": {
                   "type": "dark",
                   "validity": 999,
                   "calibDate": "2013-11-03",
                   "ccd": 4,
                   "template": "CALIB/DARK/{calibDate:s}/NONE/DARK-{calibDate:s}-{ccd:03d}.fits"
               }
           },
           {
               "pfn": "FLAT-2013-11-03-004.fits",
               "meta": {
                   "type": "flat",
                   "validity": 999,
                   "calibDate": "2013-11-03",
                   "filter": "HSC-I",
                   "ccd": 4,
                   "template": "CALIB/FLAT/{calibDate:s}/{filter:s}/FLAT-{calibDate:s}-{ccd:03d}.fits"
               }
           },
           {
               "pfn": "brighter_fatter_kernel.pkl",
               "meta": {
                   "type": "bfKernel",
                   "template": "CALIB/BFKERNEL/brighter_fatter_kernel.pkl"
               }
           }
       ]
   }

Now you're ready to run ``processCcd`` without worring about having a dataset repository. Enjoy!

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

