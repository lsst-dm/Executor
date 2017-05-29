import abc
import logging
import shutil
import six
import sys
import os


logger = logging.getLogger(__name__)


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

    Raises
    ------
    ValueError
        If a dataset repository already exists at specified location.
    """

    def __init__(self, path, mapper, mapper_file='_mapper'):
        self.path = path
        self.mapper_file = os.path.join(self.path, mapper_file)
        self.mapper_type = mapper

    def __str__(self):
        tmpl = '{map} in {file}'
        return tmpl.format(map=self.mapper_type, file=self.mapper_file)

    def __repr__(self):
        tmpl = '{cmd}({path!r}, {map!r}, mapper_file={file!r})'
        return tmpl.format(cmd=self.__class__.__name__, path=self.path,
                           map=self.mapper_type, file=self.mapper_file)

    def execute(self):
        if os.path.exists(self.path):
            msg = 'Dataset repository exists at \'{}\''.format(self.path)
            logger.error(msg)
            raise ValueError(msg)
        os.makedirs(self.path)
        with open(self.mapper_file, 'w') as f:
            f.write(self.mapper_type + '\n')


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

        * **pfn**: physical file name,
        * **meta**: a set of key/value pairs defining the metadata associated
          with a given file

        Additionally, **meta** field should include **template** entry which
        describes how the metadata should be used to place the file in a
        location recognized by the butler. See below for an example record. ::

            {
                'pfn': 'BIAS-2013-11-03-004.fits',
                'meta': {
                    'date': '2013-11-03',
                    'ccd': 4,
                    'template': 'BIAS/{date:s}/NONE/BIAS-{date:s}-{ccd:03d}.fits'
                }
            }

    """

    def __init__(self, path, records):
        self.records = [records] if isinstance(records, dict) else records
        self.path = os.path.abspath(path)

    def __repr__(self):
        tmpl = '{cmd}({path!r}, records={recs})'
        return tmpl.format(cmd=self.__class__.__name__, path=self.path,
                           recs=self.records)

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
    opts : `list` of `str`
        List of task's options.
    files : iterable of `str`
        Names of the data files which should be ingested to the repository.
    """

    def __init__(self, task, path, opts, files):
        self.receiver = task
        self.name = getattr(self.receiver, '_DefaultName')
        self.path = path
        self.opts = opts
        self.files = [files] if isinstance(files, six.string_types) else files

    def __repr__(self):
        tmpl = '{cmd}({task}, {path!r}, {opts}, {files})'
        return tmpl.format(cmd=self.__class__.__name__, task=self.receiver,
                           path=self.path, opts=self.opts, files=self.files)

    def __str__(self):
        name = self.name + '.py'
        args = ' '.join(self.opts + self.files)
        tmpl = '{task} {root} {argv}'
        return tmpl.format(task=name, root=self.path, argv=args)

    def execute(self):
        sys.argv = [self.name]
        sys.argv.append(self.path)
        sys.argv.append(self.opts)
        sys.argv.append(self.files)
        self.receiver.parseAndRun()


class RunTask(Command):
    """Run an LSST task.

    Parameters
    ----------
    task : CmdLineTask
        An LSST command line task, e.g. `processCcd`.
    path : `str`
        Location of dataset repository.
    args : `list` of `str`
        Task's optional arguments.
    """

    def __init__(self, task, path, args):
        self.receiver = task
        self.name = getattr(self.receiver, '_DefaultName')
        self.path = path
        self.args = args

    def __repr__(self):
        args = ' '.join([self.path] + self.args)
        tmpl = '{cmd}({task}, {path!r}, {argv})'
        return tmpl.format(cmd=self.__class__.__name__, task=self.receiver,
                           path=self.path, argv=args)

    def __str__(self):
        name = self.name + '.py'
        args = ' '.join(self.args)
        tmpl = '{task} {root} {argv}'
        return tmpl.format(task=name, root=self.path, argv=args)

    def execute(self):
        argv = [self.path] + self.args
        self.receiver.parseAndRun(args=argv)
