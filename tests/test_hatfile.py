import os.path
import sys
import unittest
from multiprocessing import Process
from .server import WebServer, host_name, server_port
import hat.cmd
from hat.http import CONFIG


class HatFileTestCase(unittest.TestCase):
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
        CONFIG['routes'].clear()
        CONFIG['hosts'].clear()

    def test_hatfile_list(self):
        sys.argv.clear()
        sys.argv.append("hat")
        sys.argv.append("-f=" + os.path.join(os.path.abspath(os.path.dirname(__file__)), "hatfile.py"))
        sys.argv.append("-v")
        sys.argv.append("list")
        hat.cmd.main()
        print("This test should output 3 route descriptions and their urls and method as well as 4 test methods")
        print()

    def test_hatfile(self):
        sys.argv.clear()
        sys.argv.append("hat")
        sys.argv.append("-f=" + os.path.join(os.path.abspath(os.path.dirname(__file__)), "hatfile.py"))
        sys.argv.append("runall")
        hat.cmd.main()
        print("This test should output 2 successful tests and 3 failed tests")
        print()

    def test_hatfile_filtered(self):
        sys.argv.clear()
        sys.argv.append("hat")
        sys.argv.append("-f=" + os.path.join(os.path.abspath(os.path.dirname(__file__)), "hatfile.py"))
        sys.argv.append("test_http")
        sys.argv.append("--route=2")
        hat.cmd.main()
        print("This test should output 1 failed tests")
        print()


if __name__ == '__main__':
    unittest.main()
