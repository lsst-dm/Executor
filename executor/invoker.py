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


def execute(argv):
    """Execute an LSST task in an arbitrary location.

    Parameters
    ----------
    argv : list of `str`
        List representing command line arguments.
    """
    parser = create_parser()
    args = parser.parse_args(argv[1:])

    logger = setup_logging(level=logging.INFO)
    if args.logging is not None:
        logger = setup_logging(path=args.logging)
    logger.info('Logger configured, starting logging events.')

    logger.info('Reading job description from \'%s\'.' % args.file)
    with open(args.file, 'r') as f:
        job = json.load(f)

    msg = 'Validating job description; '
    if args.schema is not None:
        with open(args.schema, 'r') as s:
            schema = json.load(s)
        msg += 'using schema from \'%s\'.'.format(args.schema)
    else:
        schema = default
        msg += 'using internal schema.'
    logger.info(msg)
    jsonschema.validate(job, schema)

    root = job['input']['root']

    # Build a map between task names and their code, i.e. modules and classes.
    snowflakes = {
        'ingestImages': ('lsst.pipe.tasks.ingest', 'IngestTask'),
    }
    mapper = TaskMapper(['lsst.pipe.tasks'], special=snowflakes)

    logger.info('Building command queue...')
    queue = []

    # If the value of the field 'data' contains list of file specifications,
    # build the butler repository from scratch.
    data = job.get('data')
    if data is not None:
        if not data:
            msg = 'No files to ingest'
            logger.error(msg)
            raise ValueError(msg)

        # Add the command that will create an empty butler repository at a
        # given location with a required mapper.
        try:
            mapping = job['input']['mapper']
        except KeyError:
            msg = 'Mapper not specified, cannot create dataset repository.'
            logger.error(msg)
            raise ValueError(msg)
        cmd = InitRepo(root, mapping)
        queue.append(cmd)

        # Add the command which will ingest raw data.
        name = 'ingestImages'
        tmpl = '--mode {mod}'
        task = mapper.get_task(name)
        files = [rec['pfn'] for rec in data]
        opts = tmpl.format(mod='copy').split()
        cmd = IngestData(task, root, files, opts)
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

    # Add the command which will run the LSST task.
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
