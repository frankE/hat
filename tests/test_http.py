import unittest
import requests as r

from hat.http import Extractor
from .server import WebServer, host_name, server_port
from multiprocessing import Process

from hat import http


class UnitTests(unittest.TestCase):
    def test_filter_routes(self):
        from hat.http import filter_routes
        routes = ["abcd", "def", "ghi", "jkl", "mno", "xzy"]
        filtered = filter_routes("1,2,6", routes)
        self.assertEqual(filtered, ["abcd", "def", "xzy"])


class HttpRoutesTestCase(unittest.TestCase):
    def setUp(self):
        self.hosts = ["http://{}:{}/".format(host_name, server_port)]
        self.server = WebServer(host_name, server_port)
        self.process = Process(target=self.server.start_server)
        self.process.start()

    def tearDown(self):
        self.process.kill()
        self.server.stop_server()
        self.process.join()
        self.process.close()

    def test_server(self):
        resp = r.get("http://{}:{}/".format(host_name, server_port), timeout=5)
        resp.close()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["id"], 1)

    def test_handle_basic_route(self):
        session = r
        routes = [
            http.Route("/", method="GET")
        ]
        for i, result in enumerate(http.handle_routes(session, routes=routes, hosts=self.hosts)):
            self.assertEqual(i, 0)
            self.assertEqual(result.success, True)
            self.assertEqual(result.response.status_code, 200)

    def test_handle_multiple_routes(self):
        session = r
        routes = [
            http.Route("/", method="GET"),
            http.Route("/", method="GET"),
            http.Route("/", method="GET"),
            http.Route("/", method="GET"),
        ]
        for i, result in enumerate(http.handle_routes(session, routes=routes, hosts=self.hosts)):
            self.assertEqual(result.success, True)
            self.assertEqual(result.response.status_code, 200)

        self.assertEqual(i, len(routes)-1)

    def test_handle_post_route(self):
        session = r
        routes = [
            http.Route("/", method="POST", body={"username": "test", "password": "test"}, response=201),
        ]
        for i, result in enumerate(http.handle_routes(session, routes=routes, hosts=self.hosts)):
            self.assertEqual(result.success, True)
            self.assertEqual(result.response.status_code, 201)
            self.assertEqual(result.response.json(), {"username": "test", "password": "test"})
        self.assertEqual(i, len(routes)-1)

    def test_handle_extractor_route(self):
        session = r
        routes = [
            http.Route("/", method="GET", response=200, store=[Extractor("response.body-object.id", "id")]),
            http.Route("/", method="POST", body={"id": "{id}"}, response=201),
        ]
        for i, result in enumerate(http.handle_routes(session, routes=routes, hosts=self.hosts)):
            if i == 0:
                self.assertEqual(result.success, True)
                self.assertEqual(result.response.status_code, 200)
            else:
                self.assertEqual(result.success, True)
                self.assertEqual(result.response.status_code, 201)
                self.assertEqual(result.response.json(), {"id": '1'})
        self.assertEqual(i, len(routes) - 1)


if __name__ == '__main__':
    unittest.main()

