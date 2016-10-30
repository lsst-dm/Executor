import argparse
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
    parser.add_argument('taskname', type=str,
                        help='name of the LSST task to run')
    parser.add_argument('path', type=str,
                        help='desired location of butler repository')
    parser.add_argument('files', nargs='+', type=str,
                        help='task\'s input data files')
    parser.add_argument('--calib', nargs='+', type=str,
                        help='calibration files', default=None)
    parser.add_argument('--bias', nargs='+', type=str,
                        help='calibration files for biases', default=None)
    parser.add_argument('--dark', nargs='+', type=str,
                        help='calibration files for darks', default=None)
    parser.add_argument('--defects', nargs='+', type=str,
                        help='calibration files for defects', default=None)
    parser.add_argument('--flat', nargs='+', type=str,
                        help='calibration files for flats', default=None)
    parser.add_argument('--fringe', nargs='+', type=str,
                        help='calibration files for fringes', default=None)
    parser.add_argument('--kernel', nargs='?', type=str,
                        help='calibration file for kernel', default=None)
    parser.add_argument('--validity', nargs=1, type=int,
                        help='calibration validity period', default=999)
    parser.add_argument('--mapper', nargs=1, type=str, help='butler mapper',
                        default='lsst.obs.hsc.HscMapper')
    parser.add_argument('--extras', nargs='*', type=str,
                        help='task\'s arguments (if any)')
    return parser


def execute(argv):
    """Execute an LSST task in an arbitrary location.

    Parameters
    ----------
    argv : list of `str`
        List representing command line arguments.
    """
    try:
        idx = argv.index('--extras')
    except ValueError:
        idx = len(argv)
    exec_args = argv[1:idx]
    task_args = argv[idx + 1:] if idx < len(argv) else None

    parser = create_parser()
    args = parser.parse_args(exec_args)

    for opt, val in vars(args).items():
        print(opt, val)

    # Create a map between task names and the code (i.e. modules and classes).
    snowflakes = {
        'ingestImages': ('lsst.pipe.tasks.ingest', 'IngestTask'),
    }
    mapper = TaskMapper(['lsst.pipe.tasks'], special=snowflakes)

    # Start with an empty command queue.
    queue = []

    # Enqueue command which will create an empty butler repository at a
    # given location with a required mapper.
    queue.append(InitRepo(args.path, args.mapper))

    # Add the command which will ingest raw data.
    name = 'ingestImages'
    tmpl_reg = '--mode {mod}'.format
    task = mapper.get_task(name)
    opts = tmpl_reg(mod='copy').split()
    queue.append(IngestData(task, args.path, args.files, opts))

    # Add the commands which will ingest required calibration data.
    name = 'ingestCalibs'
    tmpl_reg = '--calib {path} --calibType {type} --validity {val}'.format
    tmpl_alt = '--calib {path} --validity {val}'.format
    task = mapper.get_task(name)

    calib_types = ['calib', 'bias', 'dark', 'defects', 'flat', 'fringe']
    calibs = {opt: val for opt, val in vars(args).items()
              if opt in calib_types and val is not None}
    for type, files in calibs.items():
        if type != 'calib':
            opts = tmpl_reg(path=args.path, type=type, val=args.validity)
        else:
            opts = tmpl_alt(path=args.path, val=args.validity)
        queue.append(IngestData(task, args.path, files, opts.split()))

        # And this is the place where things are getting funny. The LSST task
        # responsible for ingesting calibration files to a butler repository
        # does NOT copy/move/link the files it only updates the registry in
        # the repository. Placing the files in the expected locations is
        # apparently left up to Cthulhu.
        queue.append(IngestCalibs(args.path, files))

    # The last special snowflake, ingesting kernel calibration file.
    if args.kernel is not None:
        queue.append(IngestKern(args.path, args.kernel))

    # Add the command which will run the LSST task.
    task = mapper.get_task(args.taskname)
    queue.append(RunTask(task, args.path, task_args))

    # Finally, execute the enqueued commands.
    for cmd in queue:
        cmd.execute()
