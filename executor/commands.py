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
    files : `list` of `str`
        Files to ingest.
    """

    def __init__(self, path, files):
        self.files = [files] if isinstance(files, str) else files
        self.path = os.path.join(path, 'CALIB')

    def execute(self):
        for file in self.files:
            name = os.path.basename(file)
            index = name.find('.')

            filter = 'NONE'
            tokens = name[:index].split('-')
            if len(tokens) == 5:
                type, year, month, day, ccd = tokens
            else:
                type, year, month, day, cam, band, cdd, = tokens
                filter = '-'.join([cam, band])
            date = '-'.join([year, month, day])
            subpath = '/'.join([type, date, filter])
            dest = os.path.join(self.path, subpath)
            if not os.path.exists(dest):
                os.makedirs(dest)

            shutil.copy(file, dest)


class IngestKern(Command):
    """Ingest kernel file to a butler repository.

    .. warning::
       This is a quick and dirty, temporary solution for HSC data repository!
       Once butler developers provide a generic interface for ingesting
       calibration files to a butler repository, it will be deprecated.

    Parameters
    ----------
    path : `str`
        Location of the butler repository.
    files : `list` of `str`
        Files to ingest.
    """
    def __init__(self, path, files):
        self.files = [files] if isinstance(files, str) else files
        self.path = os.path.join(path, 'CALIB')

    def execute(self):
        dest = os.path.join(self.path, 'BFKERNEL')
        if not os.path.exists(dest):
            os.makedirs(dest)
        for file in self.files:
            shutil.copy(file, dest)


class IngestData(Command):
    """Ingest data files to the data butler repository.

    Parameters
    ----------
    task : CmdLineTask
        The LSST task allowing to ingest data to the repository, e.g. `ingest`.
    path : `str`
        Desired location of data butler repository.
    files : iterable of `str`
        Names of the data files which should be ingested to the repository.
    opts : `list` of `str`
        List of task's options.
    """

    def __init__(self, task, path, files, opts):
        self.path = path
        self.files = [files] if isinstance(files, str) else files
        self.opts = opts
        self.receiver = task

    def execute(self):
        sys.argv = [self.receiver._DefaultName]
        sys.argv.append(self.path)
        [sys.argv.append(file) for file in self.opts + self.files]
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
