import argparse
import json
import jsonschema
from .mapper import TaskMapper
from .commands import InitRepo, IngestCalibs, IngestData, RunTask
from .schema import default


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
    else:
        schema = default
    jsonschema.validate(job, schema)

    root = job['input']['root']

    # Create a map between task names and the code (i.e. modules and classes).
    snowflakes = {
        'ingestImages': ('lsst.pipe.tasks.ingest', 'IngestTask'),
    }
    mapper = TaskMapper(['lsst.pipe.tasks'], special=snowflakes)

    # Start building the command queue.
    queue = []

    # If the value of the field 'data' contains list of file specifications,
    # build the butler repository from scratch.
    data = job.get('data')
    if data is not None:
        if not data:
            raise ValueError('no files to ingest.')

        # Add the command that will create an empty butler repository at a
        # given location with a required mapper.
        try:
            mapping = job['input']['mapper']
        except KeyError:
            raise ValueError('mapper not specified, '
                             'cannot create butler repository.')
        queue.append(InitRepo(root, mapping))

        # Add the command which will ingest raw data.
        name = 'ingestImages'
        tmpl = '--mode {mod}'
        task = mapper.get_task(name)
        files = [rec['pfn'] for rec in data]
        opts = tmpl.format(mod='copy').split()
        queue.append(IngestData(task, root, files, opts))

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
                queue.append(IngestData(task, root, filename, opts))

            # And this is the place where things are getting really funny.
            # The LSST task responsible for ingesting calibration files to
            # a butler repository does NOT copy/move/link the files it only
            # updates the repository's registry.  Placing the files in
            # the expected locations is apparently left as an exercise for
            # a reader.
            queue.append(IngestCalibs(root, calibs))

    # Add the command which will run the LSST task.
    name, args = job['task']['name'], job['task']['args']
    tmpl = '--output {out} {args}'
    args = tmpl.format(out=job['output']['root'], args=' '.join(args)).split()
    task = mapper.get_task(name)
    queue.append(RunTask(task, root, args))

    # Finally, execute the enqueued commands.
    for cmd in queue:
        cmd.execute()
