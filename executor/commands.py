import abc
import shutil
import sys
import os


class Command(object):
    """Define a command interface.
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def execute(self):
        pass


class InitRepo(Command):
    """Initialize a data butler repository at a given location.

    Parameters
    ----------
    path : `str`
        Desired location of the data butler repository.
    mapper : `str`
        Required mapper.
    mapper_file : `str`, optional
        Name of the mapper file, defaults to `_mapper`.

    Notes
    -----
    For now, any pre-existing butler repo at the given location is obliterated.
    """

    def __init__(self, path, mapper, mapper_file='_mapper'):
        self.path = path
        self.mapper = mapper + '\n'
        self.mapper_file = mapper_file

    def execute(self):
        if os.path.exists(self.path):
            shutil.rmtree(self.path)
        os.makedirs(self.path)
        file = os.path.join(self.path, self.mapper_file)
        with open(file, 'w') as f:
            f.write(self.mapper)


class IngestCalibs(Command):
    """Ingest calibration files to a butler repository.

    .. warning::
       This is a quick and dirty, temporary solution for HSC data repository!
       Once butler developers provide a generic interface for ingesting
       calibration files to a butler repository, it will be deprecated.

    Parameters
    ----------
    path : `str`
        Location of the butler repository.
    records : `list` of `dict`
        Records describing files to ingest. Each record should contain at
        least two fields:

        * `pfn`: physical file name,
        * `meta`: a set of key/value pairs defining the metadata associated
           with a given file

        Additionally, `meta` field should include `template` entry which
        describes how the metadata should be used to place the file in a
        location recognized by the butler. See below for an example record.

        ```
        {
            'pfn': 'BIAS-2013-11-03-004.fits',
            'meta': {
                'date': '2013-11-03',
                'ccd': 4
                'template': 'BIAS/{date:s}/NONE/BIAS-{date:s}-{ccd:03d}.fits'
            }
        }
        ```
    """

    def __init__(self, path, records):
        self.records = [records] if isinstance(records, dict) else records
        self.path = os.path.abspath(path)

    def execute(self):
        for rec in self.records:
            meta = rec['meta']
            subpath = meta['template'].format(**meta)
            dest = os.path.join(self.path, subpath)
            if not os.path.exists(os.path.dirname(dest)):
                os.makedirs(os.path.dirname(dest))
            shutil.copy(rec['pfn'], dest)


class IngestData(Command):
    """Ingest data files to the data butler repository.

    Parameters
    ----------
    task : CmdLineTask
        The LSST task allowing to ingest data to the repository, e.g. `ingest`.
    path : `str`
        Location of data butler repository.
    files : iterable of `str`
        Names of the data files which should be ingested to the repository.
    opts : `list` of `str`
        List of task's options.
    """

    def __init__(self, task, path, files, opts):
        self.path = path
        self.files = [files] if isinstance(files, unicode) else files
        self.opts = opts
        self.receiver = task

    def execute(self):
        sys.argv = [self.receiver._DefaultName]
        sys.argv.append(self.path)
        [sys.argv.append(arg) for arg in self.opts + self.files]
        self.receiver.parseAndRun()


class RunTask(Command):
    """Run an LSST task.

    Parameters
    ----------
    task : CmdLineTask
        An LSST command line task, e.g. `processCcd`.
    path : `str`
        Location of data butler repository.
    args : `list` of `str`
        Task's optional arguments.
    """

    def __init__(self, task, path, args):
        self.receiver = task
        self.argv = [path] + args

    def execute(self):
        self.receiver.parseAndRun(args=self.argv)
