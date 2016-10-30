import importlib
import inspect
import pkgutil
import pyclbr


class TaskMapper(object):
    """Map task names to their code.

    Creates a mapping between task names and ordered pairs (tuples) indicating
    both names of modules they are in and the classes representing them.

    Parameters
    ----------
    pkg_names : `list` of `str`
        List of package names to inspect.
    specials : `dict`, optional
        Task naming conventions in the LSST code base are incoherent so any
        mapping heuristic will invariably fail. Instead of ad hoc changes
        use this dictionary to add all the special snowflakes as a temporary
        solution and keep bugging developers to fix the exceptions. Its
        elements should follow the template below

            <task name>: (<package name>, <class name>)

        e.g.

           'ingestImages': ('lsst.pipe.tasks.ingest', 'IngestTask')

    """

    def __init__(self, pkg_names, special=None):
        self.map = {}
        packages = [importlib.import_module(name) for name in pkg_names]
        for pkg in packages:
            self.map.update(self.map_tasks(pkg))
        if special is not None:
            self.map.update(special)

    def get_task(self, task_name):
        """Return the class representing a given task.

        Parameters
        ----------
        task_name : `str`
            Name of the LSST task.

        Returns
        -------
        task : CmdLineTask
            Class representing a given task.

        Raises
        ------
        `ValueError`
            If the task was not found.
        """
        try:
            mod_name, cls_name = self.map[task_name]
        except KeyError:
            raise ValueError('Task \'%s\' not found.' % task_name)
        mod = importlib.import_module(mod_name)
        classes = {name: cls
                   for name, cls in inspect.getmembers(mod, inspect.isclass)}
        return classes[cls_name]

    @staticmethod
    def map_tasks(pkg):
        """Map task names to their modules and classes.

        The method assumes that the task name is practically identical with
        the respective class name except that class name

        1. ends with 'Task',
        2. follows CapWord naming convention.

        So task `doSomething` is expected to be implemented by the class
        `DoSomethingTask`.

        Parameters
        ----------
        pkg : `str`
            Package to search.
        """
        tasks = {}
        for _, mod, _ in pkgutil.iter_modules(pkg.__path__):
            classes = pyclbr.readmodule(mod, path=pkg.__path__)
            tasks.update({name: pkg.__name__ + '.' + cls.module
                          for name, cls in classes.items()
                          if (cls.module == mod and
                              cls.name.lower().endswith('task'))})
        return {cls[0].lower() + cls[1:-4]: (mod, cls)
                for cls, mod in tasks.items()}
