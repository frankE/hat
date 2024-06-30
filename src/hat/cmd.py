import json
import sys
import os
from .main import name_to_python, import_tests, run, runall, list_tests, setup


OK = '\033[92m'
FAIL = '\033[91m'
ENDC = '\033[0m'


class JsonOutput(object):
    def __init__(self):
        self.serializable = []

    def write(self, results):
        assert len(results) == 2
        lines = results[0]
        result = results[1]
        if hasattr(result, 'to_dict'):
            sys.stderr.write("\n".join(lines))
            self.serializable.append(dict(result.to_dict()))
        else:
            self.serializable.append({"success": bool(result), "message": "\n".join(lines)})

    def finalize(self):
        json.dump(self.serializable, sys.stdout, indent=2)


class ReadableOutput(object):
    def __init__(self, verbosity=0, color=True):
        self.summary = []
        self.verbosity = verbosity
        self.color = color

    def write(self, results):
        assert len(results) == 2
        lines = results[0]
        result = results[1]
        if isinstance(result, bool):
            self._output_lines(lines, result)
            if not result:
                self.summary.append("- " + lines[0])
        elif hasattr(result, 'success') and hasattr(result, 'title') and hasattr(result, 'write'):
            self._output_result(lines, result)
            if not result.success:
                self.summary.append("- " + result.title)
        else:
            raise Exception("Oh no!")

    def finalize(self):
        if len(self.summary) > 0:
            sys.stderr.write("\n")
            sys.stderr.write(FAIL) if self.color and sys.stderr.isatty() else None
            sys.stderr.write(f"Failed tests: {len(self.summary)}\n")
            sys.stderr.write("\n".join(self.summary))
            sys.stderr.write(ENDC) if self.color and sys.stderr.isatty() else None
            sys.stderr.write("\n")
        else:
            sys.stderr.write("\n")
            sys.stderr.write(OK) if self.color and sys.stderr.isatty() else None
            sys.stderr.write("All tests passed\n")
            sys.stderr.write(ENDC) if self.color and sys.stderr.isatty() else None
            sys.stderr.write("\n")

    def _output_lines(self, lines, result):
        if result:
            stream = sys.stdout
            #stream.write("\n")
            if stream.isatty() and self.color:
                stream.write(OK)
                stream.write('\N{check mark}' + " ")
        else:
            stream = sys.stderr
            # stream.write("\n")
            if stream.isatty() and self.color:
                stream.write(FAIL)
                stream.write('\N{ballot x}' + " ")
        if len(lines) > 0:
            stream.write(lines[0] + "\n")
        if stream.isatty() and self.color:
            stream.write(ENDC)
        for line in lines[1:]:
            stream.write(line + "\n")

    def _output_result(self, lines, result):
        if result.success:
            stream = sys.stdout
            # if self.verbosity > 0:
            #     stream.write("\n")
            if stream.isatty() and self.color:
                stream.write(OK)
                stream.write('\N{check mark}' + " ")
        else:
            stream = sys.stderr
            # if self.verbosity > 0:
            #     stream.write("\n")
            if stream.isatty() and self.color:
                stream.write(FAIL)
                stream.write('\N{ballot x}' + " ")
        stream.write(result.title + "\n")
        if stream.isatty() and self.color:
            stream.write(ENDC)
        result.write(stream, self.verbosity)
        sys.stderr.write("\n".join(lines))


def parse_arguments(args):
    p = {}
    for arg in args:
        if arg.startswith("-"):
            arg = arg.lstrip("-")
            parts = arg.split("=", 1)
            name = name_to_python(parts[0])
            if len(parts) < 2 or parts[1] == "True" or parts[1] == "true":
                p[name] = True
                continue
            elif parts[1] == "False" or parts[1] == "false":
                p[name] = False
                continue
            p[name] = parts[1]
    return p


# todo: add a proper command line parser
def parse_args(argv):
    command = None
    command_args = []
    what = None
    args = []
    for n in range(0, len(argv)):
        if argv[n] == 'run':
            command = 'run'
        elif argv[n] == 'list':
            command = 'list'
        elif argv[n] == 'runall':
            command = 'runall'
        elif command is None and argv[n].startswith('-'):
            command_args.append(argv[n])
        elif command is not None and (what is not None or command == 'runall') and argv[n].startswith('--'):
            args.append(argv[n])
        elif command == 'run' or command == 'list' and not argv[n].startswith('-'):
            what = argv[n]
        elif command is None and not argv[n].startswith('-'):
            command = 'run'
            what = argv[n]
        else:
            print("Unknown argument: " + argv[n])
    return command, command_args, what, args


def print_help(lines):
    sys.stdout.write("\n".join(lines))
    sys.stdout.write("\n")


def print_usage():
    print("Usage: hat [-j] [-f={testfile}] [run] test_name [--arg1=value] [--arg2=value] ... | list [test_name] | runall [--arg1=value] [--arg2=value] ...")


def load_tests(file):
    if os.path.isfile(file):
        return import_tests('hatfile', file)
    else:
        print("File not found: " + file)
        sys.exit(1)


def main():
    success = True
    (command, command_args, what, args) = parse_args(sys.argv[1:])
    if command is None and what is None:
        print_usage()
        sys.exit(1)
    command_args = parse_arguments(command_args)
    file = command_args['f'] if 'f' in command_args else os.path.join(os.getcwd(), 'hatfile.py')
    verbosity = int(command_args['v']) if 'v' in command_args else 0
    output = JsonOutput() if 'j' in command_args else ReadableOutput(verbosity, True)
    tests = load_tests(file)
    setup(tests)
    args = parse_arguments(args)
    if command == 'run':
        result = run(tests, what, args, command_args)
        success &= result[1].success if hasattr(result[1], 'success') else bool(result[1])
        output.write(result)
        output.finalize()
    elif command == 'list':
        print_help(list_tests(tests, what, command_args))
    elif command == 'runall':
        for result in runall(tests, args, command_args):
            success &= result[1].success if hasattr(result[1], 'success') else bool(result[1])
            output.write(result)
        output.finalize()
    else:
        result = (["Unknown command: " + " ".join(sys.argv)], False)
        output.write(result)
        success = False
    return 0 if success else 1

