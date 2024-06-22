import json
import sys
import os
from .main import name_to_python, import_tests, run, runall, list_tests, setup


OK = '\033[92m'
FAIL = '\033[91m'
ENDC = '\033[0m'


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


def output_result(lines, outcome, color=True, verbosity=0):
    if not hasattr(outcome, 'success') or not hasattr(outcome, 'title') or not hasattr(outcome, 'write'):
        sys.stderr.write("Invalid result object\n")
        return
    if outcome.success:
        stream = sys.stdout
        if verbosity > 0:
            stream.write("\n")
        if stream.isatty() and color:
            stream.write(OK)
            stream.write('\N{check mark}' + " ")
    else:
        stream = sys.stderr
        if verbosity > 0:
            stream.write("\n")
        if stream.isatty() and color:
            stream.write(FAIL)
            stream.write('\N{ballot x}' + " ")
    stream.write(outcome.title + "\n")
    if stream.isatty() and color:
        stream.write(ENDC)
    outcome.write(stream, verbosity)
    sys.stderr.write("\n".join(lines))


def output_lines(lines, outcome, color=True):
    if outcome:
        stream = sys.stdout
        stream.write("\n")
        if stream.isatty() and color:
            stream.write(OK)
            stream.write('\N{check mark}' + " ")
    else:
        stream = sys.stderr
        stream.write("\n")
        if stream.isatty() and color:
            stream.write(FAIL)
            stream.write('\N{ballot x}' + " ")
    if len(lines) > 0:
        stream.write(lines[0] + "\n")
    if stream.isatty() and color:
        stream.write(ENDC)
    for line in lines[1:]:
        stream.write(line + "\n")


def output(results, color=True, json_output=False, verbosity=0):
    if json_output:
        serializable = []
        for lines, result in results:
            if hasattr(result, 'to_dict'):
                sys.stderr.write("\n".join(lines))
                serializable.append(dict(result.to_dict()))
            else:
                serializable.append({"success": bool(result), "message": "\n".join(lines)})
        sys.stdout.write(json.dumps(serializable, indent=2))
    else:
        summary = []
        for lines, result in results:
            if isinstance(result, bool):
                output_lines(lines, result, color)
                if not result:
                    summary.append(lines[0])
            else:
                output_result(lines, result, color, verbosity)
                if not result.success:
                    summary.append("- " + result.title)
        if len(summary) > 0:
            sys.stderr.write("\n")
            sys.stderr.write(FAIL) if color and sys.stderr.isatty() else None
            sys.stderr.write(f"Failed tests: {len(summary)}\n")
            sys.stderr.write("\n".join(summary))
            sys.stderr.write(ENDC) if color and sys.stderr.isatty() else None
            sys.stderr.write("\n")
        else:
            sys.stderr.write("\n")
            sys.stderr.write(OK) if color and sys.stderr.isatty() else None
            sys.stderr.write("All tests passed\n")
            sys.stderr.write(ENDC) if color and sys.stderr.isatty() else None
            sys.stderr.write("\n")


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
    (command, command_args, what, args) = parse_args(sys.argv[1:])
    if command is None and what is None:
        print_usage()
        sys.exit(1)
    command_args = parse_arguments(command_args)
    file = command_args['f'] if 'f' in command_args else os.path.join(os.getcwd(), 'hatfile.py')
    json = True if 'j' in command_args else False
    verbosity = int(command_args['v']) if 'v' in command_args else 0
    result_list = []
    tests = load_tests(file)
    setup(tests)
    args = parse_arguments(args)
    color = True
    if command == 'run':
        for result in run(tests, what, args, command_args):
            result_list.append(result)
        output(result_list, color, json, verbosity)
    elif command == 'list':
        print_help(list_tests(tests, what, command_args))
    elif command == 'runall':
        for result in runall(tests, args, command_args):
            result_list.append(result)
        output(result_list, color, json, verbosity)
    else:
        result = (["Unknown command: " + " ".join(sys.argv)], False)
        result_list.append(result)
        output(result_list, color, json, verbosity)
