import argparse
import json
import jsonschema
from .mapper import TaskMapper
from .commands import InitRepo, IngestCalibs, IngestKern, IngestData, RunTask


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

    with open(args.file, 'r') as f:
        job = json.load(f)
    if args.schema is not None:
        with open(args.schema, 'r') as s:
            schema = json.load(s)
        jsonschema.validate(job, schema)

    # Create a map between task names and the code (i.e. modules and classes).
    snowflakes = {
        'ingestImages': ('lsst.pipe.tasks.ingest', 'IngestTask'),
    }
    mapper = TaskMapper(['lsst.pipe.tasks'], special=snowflakes)

    # Start with an empty command queue.
    queue = []

    # Enqueue command which will create an empty butler repository at a
    # given location with a required mapper.
    repo = job['repo']
    queue.append(InitRepo(repo['root'], repo['mapper']))

    # Add the command which will ingest raw data.
    name = 'ingestImages'
    tmpl_reg = '--mode {mod}'.format
    task = mapper.get_task(name)
    files = [rec['pfn'] for rec in job['data']]
    opts = tmpl_reg(mod='copy').split()
    queue.append(IngestData(task, repo['root'], files, opts))

    # Add the commands which will ingest required calibration data.
    name = 'ingestCalibs'
    tmpl_reg = '--calib {path} --calibType {type} --validity {val}'.format
    tmpl_alt = '--calib {path} --validity {val}'.format
    task = mapper.get_task(name)
    calibs = job['calibs']
    for rec in calibs:
        filename, meta = rec['pfn'], rec['meta']
        try:
            kind, validity = meta['type'], meta['validity']
        except KeyError:
            raise ValueError('incomplete metadata for file: %s' % rec['pfn'])

        # Kernel does not require ingesting.
        if kind == 'bfKernel':
            continue

        if kind in ['bias', 'dark', 'defect', 'flat', 'fringe']:
            opts = tmpl_reg(path=repo['root'], type=kind, val=str(validity))
        else:
            opts = tmpl_alt(path=repo['root'], val=str(validity))
        queue.append(IngestData(task, repo['root'], filename, opts.split()))

    # And this is the place where things are getting really funny. The LSST
    # task responsible for ingesting calibration files to a butler repository
    # does NOT copy/move/link the files it only updates the registry in
    # the repository. Placing the files in the expected locations is
    # apparently left up to Cthulhu.
    queue.append(IngestCalibs(repo['root'], calibs))

    # Add the command which will run the LSST task.
    name, args = job['task']['name'], job['task']['args']
    task = mapper.get_task(name)
    queue.append(RunTask(task, repo['root'], args))

    # Finally, execute the enqueued commands.
    for cmd in queue:
        cmd.execute()
