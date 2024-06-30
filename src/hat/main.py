import sys
import importlib.machinery
import importlib.util
import traceback
import io

tasks = {}
IGNORE_BUILTIN = "IGNORE_BUILTIN"


class TestWrapper:
    def __init__(self):
        self.name = ''
        self.args = []
        self.func = None
        self.builtin = False

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def short_help(self):
        line = self.name
        for arg in self.args:
            arg = "--" + python_to_name(arg)
            line += " [" + arg + "]"
        return [line]

    def long_help(self):
        result = self.short_help()
        doc = self.func.__doc__.split("\n") if self.func.__doc__ is not None else []
        for d in doc:
            result.append("  " + d)

        return result


def filter_args(args, params):
    result = {}
    for k, v in args.items():
        if k in params:
            result[k] = v
    return result


def get_ignore_builtin(tests):
    if hasattr(tests, IGNORE_BUILTIN):
        return getattr(tests, IGNORE_BUILTIN)
    return False


def setup(tests):
    if hasattr(tests, "CONFIG"):
        from hat.http import set_config
        set_config(tests.CONFIG)
    if hasattr(tests, "ROUTES"):
        from hat.http import set_urls
        set_urls(tests.ROUTES)
    if hasattr(tests, "HOSTS"):
        from hat.http import set_hosts
        set_hosts(tests.HOSTS)
    if hasattr(tests, "OPTIONS"):
        from hat.http import set_options
        set_options(tests.OPTIONS)


def run(tests, function_name, args=None, command_args=None):
    ignore_builtin = get_ignore_builtin(tests)
    stdout = sys.stdout
    fn = name_to_python(function_name)
    if fn in tasks:
        sys.stdout = io.StringIO()
        try:
            success = tasks[fn](**filter_args(args, tasks[fn].args))
        except:
            success = False
            output = sys.stdout.getvalue()
            sys.stdout = stdout
            output += traceback.format_exc()
            output_lines = output.split("\n")
            result = [[function_name + ": "] + output_lines, success]
            return result
        if hasattr(success, 'write') and hasattr(success, 'title') and hasattr(success, 'success'):
            output = sys.stdout.getvalue()
            sys.stdout = stdout
            if output.strip() != '':
                output_lines = output.split("\n")
            else:
                output_lines = []
            result = [output_lines, success]
        else:
            output = sys.stdout.getvalue()
            sys.stdout = stdout
            if output.strip() != '':
                output_lines = output.split("\n")
            else:
                output_lines = []
            result = [[function_name + ": "] + output_lines, success]
    else:
        result = [[f"Test '{function_name}' not found"], False]
    return result


def runall(tests, args=None, command_args=None):
    for k, v in tasks.items():
        name = k
        if v.builtin and get_ignore_builtin(tests):
            continue
        yield run(tests, name, args, command_args)


def list_tests(tests, what=None, command_args=None):
    verbose = True if 'v' in command_args else False

    result = []
    if what is None:
        for k, v in tasks.items():
            name = python_to_name(k)
            if v.builtin and get_ignore_builtin(tests):
                continue
            if verbose:
                result += v.long_help()
            else:
                result += v.short_help()
    else:
        name = name_to_python(what)
        if name in tasks:
            if verbose:
                result += tasks[name].long_help()
            else:
                result += tasks[name].short_help()
        else:
           result += [f"Test not found: '{what}'"]

    return result


def import_tests(module, file):
    loader = importlib.machinery.SourceFileLoader(module, file)
    spec = importlib.util.spec_from_loader(module, loader)
    tests = importlib.util.module_from_spec(spec)
    loader.exec_module(tests)
    return tests


def python_to_name(name):
    return name.replace("_", "-")


def name_to_python(name):
    return name.replace("-", "_")
