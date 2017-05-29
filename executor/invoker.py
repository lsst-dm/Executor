import argparse
import json
import jsonschema
import logging
import logging.config
import os
from .mapper import TaskMapper
from .commands import InitRepo, IngestCalibs, IngestData, RunTask
from .schema import default


def setup_logging(path='logging.json', level=logging.INFO):
    """Setup logging configuration.
    
    Parameters
    ----------
    path : `str`
        Path to logging configuration in JSON format.
    level : `int`
        Log level.
    """
    if os.path.exists(path):
        with open(path, 'r') as f:
            config = json.load(f)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=level)
    return logging.getLogger(__name__)


def create_parser():
    """Create command line parser.

    Returns
    -------
    parser : `argparse.Namespace`
        An object with attributes representing command line options.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('file', type=str,
                        help='job specification')
    parser.add_argument('-d', '--dry-run', dest='dryrun', action='store_false',
                        help='print commands instead execute')
    parser.add_argument('-l', '--logging',
                        help='logging configuration')
    parser.add_argument('-s', '--schema', type=str,
                        help='JSON schema', default=None)
    return parser


def create_repo(job, mapper):
    """Create a sequence of commands required to build a dataset repository.

    Parameters
    ----------
    job : `dict`
        Job description.
    mapper : `TaskMapper`
        A map between task names and their code (names of modules they are
        defined in and class names).

    Return
    ------
    `list` of `Commands`
        A list of commands allowing to build a dataset repository from scratch.
    """
    queue = []

    # Add the command that will create an empty butler repository at a
    # given location with a required mapper.
    repo = job['input']
    root, mapping = repo['root'], repo['mapper']
    cmd = InitRepo(root, mapping)
    queue.append(cmd)

    # Add the command which will ingest raw data.
    data = job['data']
    name = 'ingestImages'
    tmpl = '--mode {mod}'
    task = mapper.get_task(name)
    opts = tmpl.format(mod='copy').split()
    files = [rec['pfn'] for rec in data]
    cmd = IngestData(task, root, opts, files)
    queue.append(cmd)

    # Add the commands which will ingest calibration data, if any.
    calibs = job.get('calibs')
    if calibs is not None:
        name = 'ingestCalibs'
        tmpl = '--calib {path} --validity {val}'
        task = mapper.get_task(name)
        for rec in calibs:
            filename, meta = rec['pfn'], rec['meta']
            kind = meta.get('type')

            # Kernel does not require ingesting to repository's registry.
            if kind == 'bfKernel':
                continue

            # Update option template if type is specified explicitly.
            if kind in ['bias', 'dark', 'defect', 'flat', 'fringe']:
                tmpl += ' --calibType {type}'

            val = str(meta.get('validity', 999))
            opts = tmpl.format(path=root, type=kind, val=val).split()
            cmd = IngestData(task, root, opts, filename)
            queue.append(cmd)

        # And this is the place where things are getting really funny.
        # The LSST task responsible for ingesting calibration files to
        # a butler repository does NOT copy/move/link the files it only
        # updates the repository's registry.  Placing the files in
        # the expected locations is apparently left as an exercise for
        # a reader.
        cmd = IngestCalibs(root, calibs)
        queue.append(cmd)
    return queue


def validate_repo(job):
    """Validate pre-existing dataset repository.

    Parameters
    ----------
    job : `dict`
        Job description.

    Returns
    -------
    `list` of `Commands`
        A list of commands allowing to validate pre-existing dataset
        repository.
    """
    # TODO: Implement a protocol for dataset repository validation.
    queue = []
    return queue


def execute(argv):
    """Execute an LSST task in an arbitrary location.

    Parameters
    ----------
    argv : list of `str`
        List representing command line arguments.
    """
    parser = create_parser()
    args = parser.parse_args(argv[1:])

    logger = setup_logging(level=logging.WARNING)
    if args.logging is not None:
        logger = setup_logging(path=args.logging)
    logger.info('Logger configured, starting logging events.')

    logger.info('Reading job description from \'{}\'.'.format(args.file))
    with open(args.file, 'r') as f:
        job = json.load(f)

    msg = 'Validating job description; '
    if args.schema is not None:
        with open(args.schema, 'r') as s:
            schema = json.load(s)
        msg += 'using schema from \'{}\'.'.format(args.schema)
    else:
        schema = default
        msg += 'using internal schema.'
    logger.info(msg)
    jsonschema.validate(job, schema)

    # Mark input dataset repository as read only, unless specified otherwise
    # explicitly in job description.
    repo = job['input']
    repo.setdefault('readonly', True)

    # Build a map between task names and their code, i.e. modules and classes.
    snowflakes = {
        'ingestImages': ('lsst.pipe.tasks.ingest', 'IngestTask'),
    }
    mapper = TaskMapper(['lsst.pipe.tasks'], special=snowflakes)

    logger.info('Populating command queue...')
    queue = []

    # If the job description contains list of file specifications, either
    # build a brand new dataset repository from scratch or validate the
    # existing one
    data = job.get('data')
    if data is not None:
        isreadonly = job['input']['readonly']
        if isreadonly:
            logger.info('Using pre-existing input dataset repository; '
                        'enqueuing instructions for validation.')
            cmds = validate_repo(job)
        else:
            logger.info('Creating input dataset repository from scratch;'
                        'enqueuing instructions for building.')
            cmds = create_repo(job, mapper)
        queue.extend(cmds)
    else:
        logger.warning('Using pre-existing input dataset repository; '
                       'proceeding without validation.')

    # Add the command which will run the LSST task.
    logger.info('Enqueuing LSST task(s)...')
    root = job['input']['root']
    name, argv = job['task']['name'], job['task']['args']
    tmpl = '--output {out} {args}'
    argv = tmpl.format(out=job['output']['root'], args=' '.join(argv)).split()
    task = mapper.get_task(name)
    cmd = RunTask(task, root, argv)
    queue.append(cmd)

    # Finally, execute the enqueued commands.
    logger.info('Finished building, starting to execute commands...')
    if args.dryrun is True:
        for cmd in queue:
            logger.info('Executing: {}'.format(cmd))
            cmd.execute()
    else:
        for cmd in queue:
            logger.debug('Executing: {!r}'.format(cmd))
    logger.info('Done.')
