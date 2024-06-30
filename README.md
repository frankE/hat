# HAT - HTTP API Testing Tool

HAT is an HTTP API testing tool built to simplify the process of writing, managing, and executing API tests. It provides a framework for defining test cases and running tests against multiple hosts and routes.  
It's just a quick hack, because I needed a tool like this. This may or may not be developed further depending on my needs.

## Features

- Define and run individual tests or execute all tests at once
- Support for GET, POST, PUT, and DELETE HTTP methods
- JSON request and response handling
- Variable storage and replacement in requests and responses
- Customizable test configurations
- JSON output option for easy integration with other tools
- Verbosity levels for detailed debugging

## Installation

Install the requirements from requirements.txt.
Make sure the `hat` folder from inside the src folder is on your pythonpath and the `hat.py` script from the src folder is on your `$PATH`.

## Usage

The basic syntax for using HAT is:

```
hat [-v=<level>] [-j] [-f=<testfile>] [run] <test_name> [--arg1=value] [--arg2=value] ... | list [test_name] | runall [--arg1=value] [--arg2=value] ...
```

### Commands

- `run <test_name>`: Run a specific test
- `list [test_name]`: List available tests or details of a specific test
- `runall`: Run all available tests

### Options

- `-j`: Output results in JSON format
- `-f=<testfile>`: Specify a custom test file (default is `hatfile.py` in the current directory)
- `-v=<level>`: Set verbosity level (0-2)

### Examples

1. Run a specific test:
   ```
   hat run login_test --username=testuser --password=testpass
   ```

2. List all available tests:
   ```
   hat list
   ```

3. Run all tests with JSON output:
   ```
   hat -j runall
   ```

## Writing Tests

Tests are defined in a Python file (default: `hatfile.py`) using decorators and a simple API. Here's a basic example:

```python
from hat.decorators import test

@test()
def login_test(username='admin', password='test'):          # Parameters can be overwritten by test invovation
    """Test documentation goes here"""
    # Test logic
    # ...
    print(f"Username: {username}; Password: {password}")    # written to stdout after the test finishes
    return True  # or False for a failed test
```

For quick testing of a couple of routes there is the builtin `test_routes` test which tests all routes in the `ROUTES` list.

```python
from hat.http import Route, Extractor, Response
from hat.builtin import test_routes

HOSTS = ["http://test.example.com/", "https://staging.example.com"]     # Per default all routes will be called per host

OPTIONS = {
    "session": True,                                                    # Store session cookies, etc. 
}

ROUTES = [
    Route("/login", "POST", response=200,                               # visit the /login route on every host via POST request, expect a 200 response
          body={"username": "admin", "password": "admin"},              # send this body as json
          store=[Extractor("response.body-object.id", "adminUserId")],  # from the answer json, store the id property as `adminUserId`
          doc="Login as an admin"),                                     # documentation for the `hat list` command 
    Route("/users/count", "GET", response=Response(200, body={"count": 1}),
          doc="Get user count"),
    Route("/users/{adminUserId}", "GET", response=200,                  # Reuse the previously stored adminUserId
          doc="Get the admin user properties"),
    # ...
]
```

For the latter, you get a list of all defined routes via:
```
hat list test_routes
```

Lastly testcases can be composed out of individual tests. E.g.:

```python
from hat.decorators import http_test
from hat.http import Route, Extractor, visit, create_session
@http_test()
def test_login(session=None, storage=None):
   routes = [
      Route("/login", "POST", response=200,
            body={"username": "admin", "password": "admin"},
            store=[Extractor("response.body-object.id", "adminUserId")],
            doc="Login as an admin"),
   ]
   return visit(routes, None, session, storage)


@http_test()
def create_user():
   session = create_session()
   storage = {}
   results = test_login(session)
   routes = [
      Route("/users", "POST", response=201,
            body={"username": "test"},
            store=[Extractor("response.body-object.id", "newUserId")],
            doc="Create an user."),
      Route("/users/{newUserId}", "GET", response=200,
            doc="Get the newly created user by id"),
   ]
   results = results + visit(routes, None, session, storage)
   return results
```