import json
from typing import Iterable

import requests as r
from .decorators import test
from .main import TestWrapper

CONFIG = {
    "hosts": [],
    "routes": [],
    "options": {
        "session": True,
    }
}


def _do_replace(data, values):
    if isinstance(data, dict):
        ret = {}
        for k, v in data.items():
            if hasattr(v, "eval"):
                ret[k] = v.eval(values)
            elif isinstance(v, str):
                ret[k] = v.format(**values)
            else:
                ret[k] = _do_replace(v, values)
    elif isinstance(data, list):
        ret = []
        for v in data:
            if hasattr(v, "eval"):
                ret.append(v.eval(values))
            elif isinstance(v, str):
                ret.append(v.format(**values))
            else:
                ret.append(_do_replace(v, values))
    else:
        return data
    return ret


class JSON:
    def __init__(self, data):
        self.data = data

    def __str__(self):
        return json.dumps(self.data, sort_keys=True, indent=2)

    def __repr__(self):
        return self.__str__()

    def add_headers(self):
        return {'Content-Type': 'application/json'}

    def replace_placeholders(self, values):
        self.data = _do_replace(self.data, values)


class Response:
    def __init__(self, code, status=None, headers=None, body=None):
        self.code = code
        self.status = status
        self.headers = None
        self.body = body

    def __str__(self):
        if self.status is not None:
            return str(self.code) + " " + self.status
        return str(self.code)

    def __repr__(self):
        return self.__str__()

    def compare_body(self, other, vars={}):
        if self.body is None:
            return True
        elif isinstance(self.body, dict) or isinstance(self.body, list):
            d = _do_replace(self.body, vars)
            body = json.dumps(d, sort_keys=True, indent=2)
            other_body = json.dumps(json.loads(other), sort_keys=True, indent=2)
            return body == other_body
        else:
            return str(self.body) == str(other)


class Request:
    def __init__(self, headers={}, body=None):
        self.headers = headers
        if isinstance(body, dict) or isinstance(body, list):
            self.body = JSON(body)
        else:
            self.body = body

    def __str__(self):
        return str(self.body)

    def __repr__(self):
        return self.__str__()


class ToInt:
    def __init__(self, value):
        self.value = value

    def eval(self, values):
        return int(self.value.format(**values))


class ToBool:
    def __init__(self, value):
        self.value = value

    def eval(self, values):
        return bool(self.value.format(**values))


class Extractor:
    def __init__(self, path, key):
        self.path = path
        self.key = key

    def __str__(self):
        return self.path + " -> " + self.key

    def __repr__(self):
        return self.__str__()

    def path_parts(self):
        return self.path.split('.')

    def value_from_result(self, result):
        parts = self.path_parts()
        obj = result
        for part in parts:
            try:
                obj = obj[part]
            except TypeError:
                try:
                    obj = obj[int(part)]
                except Exception as e:
                    raise e
        return obj


class Route:
    def __init__(self, path, method="GET", request=None, response=200, headers={}, body=None, store=None, doc=None):
        self.path = path
        self.method = method
        self.doc = doc
        self.store = store
        if request is not None:
            self.request = request
        else:
            self.request = Request(headers, body)

        if isinstance(response, int):
            self.response = Response(response)
        else:
            self.response = response

    def __str__(self):
        if self.doc is not None:
            return self.doc
        else:
            return self.path + " " + self.method

    def __repr__(self):
        return self.__str__()


def visit(routes, hosts=None, session=None, storage=None, config=CONFIG):
    options = config['options']
    if hosts is None:
        hosts = config['hosts']
    if session is None:
        if 'session' in options:
            session = r if not options['session'] else r.session()
        else:
            session = r
    return handle_routes(session, hosts, routes, storage)


def create_session():
    return r.session()


def set_urls(urls):
    global CONFIG
    CONFIG['routes'] = CONFIG['routes'] + urls


def set_hosts(hosts):
    global CONFIG
    CONFIG['hosts'] = CONFIG['hosts'] + hosts


def set_options(options):
    global CONFIG
    if CONFIG['options'] is None:
        CONFIG['options'] = {}
    for k, v in CONFIG["options"].items():
        options[k] = v


def set_config(config):
    global CONFIG
    CONFIG = config


def url(root, path):
    if root[-1] == '/':
        root = root[:-1]
    if path[0] != '/':
        path = '/' + path
    return root + path


def construct_request(request, storage):
    params = {'headers': {}}
    for k, v in request.headers.items():
        params['headers'][k] = v.format(**storage)
    if request.body is not None:
        if hasattr(request.body, 'replace_placeholders'):
            request.body.replace_placeholders(storage)
            body = str(request.body)
        else:
            body = str(request.body).format(**storage)
        params['data'] = body
        if hasattr(request.body, 'add_headers'):
            params['headers'] = request.body.add_headers() | params['headers']

    return params


def compare_response(resp, response, vars=None):
    if resp.status_code != response.code:
        return False
    if not response.compare_body(resp.content.decode("utf-8"), vars):
        return False
    return True


def filter_routes(route, routes):
    if route is None:
        return routes

    urls = []
    parts = route.split(',')
    for part in parts:
        if part.isdigit():
            urls.append(routes[int(part)-1])

    return urls


def filter_hosts(host, hosts):
    if host is None:
        return hosts

    return host.split(',')


class HTTPCollectionResult:
    def __init__(self, name, results):
        self.name = name
        self.title = name
        success = True
        if isinstance(results, list):
            self.results = results
            for r in self.results:
                success = success and r.success if hasattr(r, 'success') else r
            self.success = success
        elif isinstance(results, HTTPCollectionResult):
            self.results = results.results
            self.success = results.success

    def to_dict(self):
        return {
            "success": self.success,
            "title": self.title,
            "results": [r.to_dict() if hasattr(r, 'to_dict') else r for r in self.results]
        }

    def write(self, stream, verbosity=0, indent=0):
        if verbosity >= 1:
            for r in self.results:
                if hasattr(r, "write") and hasattr(r, "success"):
                    if verbosity >= 2:
                        r.write(stream, verbosity, indent + 2)
                        stream.write("\n")
                    elif verbosity == 1 and not r.success:
                        r.write(stream, 2, indent + 2)
                        stream.write("\n")
        stream.flush()

    def __add__(self, other):
        if not isinstance(other, HTTPCollectionResult) and not isinstance(other, list):
            raise NotImplemented
        if isinstance(other, HTTPCollectionResult):
            return HTTPCollectionResult(self.name, self.results + other.results)
        if isinstance(other, list):
            return HTTPCollectionResult(self.name, self.results + other)

    def __iadd__(self, other):
        if not isinstance(other, HTTPCollectionResult) and not isinstance(other, list):
            raise NotImplemented

        if isinstance(other, HTTPCollectionResult):
            self.results += other.results
            return self
        if isinstance(other, list):
            self.results += other
            return self

    def __iter__(self):
        return self.results.__iter__()


class HTTPRoutesResult(HTTPCollectionResult):
    def write(self, stream, verbosity=0, indent=0):
        if verbosity >= 0:
            for r in self.results:
                if hasattr(r, "write") and hasattr(r, "success"):
                    if verbosity >= 1 and r.success:
                        r.write(stream, verbosity-1, indent + 2)
                        stream.write("\n")
                    elif verbosity >= 0 and not r.success:
                        r.write(stream, 2, indent + 2)
                        stream.write("\n")
        stream.flush()


class HTTPResult:
    def __init__(self, message, success, route, host, response=None):
        self.message = message
        self.success = success
        self.route = route
        self.host = host
        self.response = response
        self.title = str(route) + ": " + url(host, route.path)

    def to_dict(self):
        try:
            response_json = json.loads(self.response.content.decode())
        except:
            response_json = None
        try:
            request_json = json.loads(self.response.body.decode())
        except:
            request_json = None
        obj = {
            "success": self.success,
            "message": self.message,
            "url": url(self.host, self.route.path),
            "method": self.route.method,
        }
        if self.response is not None:
            obj |= {
                "request": {
                    "url": self.response.request.url,
                    "headers": dict(self.response.request.headers),
                    "body": self.response.request.body,
                    "body-object": request_json
                },
                "response": {
                    "status-code": self.response.status_code,
                    "status": self.response.reason,
                    "headers": dict(self.response.headers),
                    "body": self.response.content.decode() if self.response.content is not None else None,
                    "body-object": response_json
                }
            }
        return obj

    def write_json(self, stream, verbosity=0):
        stream.write(json.dumps(self.to_dict(), sort_keys=True, indent=2))

    def write(self, stream, verbosity=0, indent=0):
        stream.write(" " * indent + self.title)
        if self.response is None and self.message is not None:
            stream.write(" " * indent + self.message)
            return
        if verbosity >= 1:
            stream.write(" " * indent)
            stream.write("Request: " + self.response.request.method + " " + self.response.request.url + "\n")
            stream.write(" " * indent)
            stream.write("Request Headers:\n")
            for k, v in self.response.request.headers.items():
                stream.write(" " * indent)
                stream.write(k + ": " + v + "\n")
        if self.response.request.body is not None and verbosity >= 2:
            stream.write(" " * indent)
            stream.write("Request Body:\n")
            try:
                obj = json.loads(self.response.request.body)
                body = json.dumps(obj, sort_keys=True, indent=2)
                body = "\n".join([" " * indent + part for part in body.split("\n")])
                stream.write(body)
            except json.JSONDecodeError as e:
                body = "\n".join([" " * indent + part for part in self.response.request.body.split("\n")])
                stream.write(body)

        if verbosity >= 1:
            stream.write("\n")
        if verbosity >= 1:
            stream.write(" " * indent)
            stream.write("Response: " + str(self.response.status_code) + " " + self.response.reason + "\n")
            stream.write(" " * indent)
            stream.write("Response Headers:\n")
            for k, v in self.response.headers.items():
                stream.write(" " * indent)
                stream.write(k + ": " + v + "\n")
        if self.response.content is not None and verbosity >= 2:
            stream.write(" " * indent)
            stream.write("Response Body:\n")
            try:
                obj = json.loads(self.response.content.decode())
                body = json.dumps(obj, sort_keys=True, indent=2)
                body = "\n".join([" " * indent + part for part in body.split("\n")])
                stream.write(body)
            except json.JSONDecodeError as e:
                if self.response.request.body is not None:
                    body = "\n".join([" " * indent + part for part in self.response.request.body.split("\n")])
                    stream.write(body)
        stream.flush()


class HttpRoutesWrapper(TestWrapper):
    def __init__(self):
        super().__init__()
        self.builtin = True

    def __call__(self, *args, **kwargs):
        return HTTPCollectionResult('ROUTES', self.func(*args, **kwargs))

    def short_help(self):
        result = [self.name, "  routes:"]
        for route in CONFIG['routes']:
            result.append("    " + str(route))
        result.append("  hosts: ")
        for host in CONFIG['hosts']:
            result.append("    " + str(host))
        return result

    def long_help(self):
        result = [self.name, "  routes:"]
        for i, route in enumerate(CONFIG['routes']):
            result.append("   {:2}. ".format(i+1) + str(route))
            if route.doc is not None:
                result.append("      " + route.path + " " + route.method)
        result.append("  hosts:")
        for i, host in enumerate(CONFIG['hosts']):
            result.append("   {:2}. ".format(i+1) + host)
        return result


class HttpWrapper(TestWrapper):
    def __call__(self, *args, **kwargs):
        return HTTPCollectionResult(self.name, self.func(*args, **kwargs))


def handle_routes(session, hosts, routes, storage=None):
    results = []
    for host in hosts:
        if storage is None:
            host_storage = {}
        else:
            host_storage = storage
        for route in routes:
            try:
                resp = None
                path = route.path.format(**host_storage)
                request = construct_request(route.request, host_storage)
                if route.method == "GET":
                    resp = session.get(url(host, path), **request)
                elif route.method == "POST":
                    resp = session.post(url(host, path), **request)
                elif route.method == "PUT":
                    resp = session.put(url(host, path), **request)
                elif route.method == "DELETE":
                    resp = session.delete(url(host, path), **request)
                else:
                    result = HTTPResult(f"Unknown method: '${route.method}'", False, route, host)
                    if route.store is not None:
                        for store in route.store:
                            host_storage[store.key] = store.value_from_result(result.to_dict())
                if resp is None:
                    result = HTTPResult(f"Unknown route: '{route.path}'", False, route, host)
                    # pass
                elif not compare_response(resp, route.response, host_storage):
                    result = HTTPResult("Unexpected response", False, route, host, resp)
                    if route.store is not None:
                        for store in route.store:
                            host_storage[store.key] = store.value_from_result(result.to_dict())
                else:
                    result = HTTPResult("Ok", True, route, host, resp)
                    if route.store is not None:
                        for store in route.store:
                            host_storage[store.key] = store.value_from_result(result.to_dict())
            except Exception as e:
                result = HTTPResult(str(e) + "\n", False, route, host)
            results.append(result)
    return results
