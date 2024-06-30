from hat.http import Route, Extractor, Response, ToInt, visit
from hat.builtin import test_routes
from hat.decorators import test, http_test
HOSTS = ["http://localhost:8080/",]

OPTIONS = {
    "session": True,
}

ROUTES = [
    Route("/test", "GET", response=200,
          store=[Extractor("response.body-object.id", "testId")],
          doc="Test get request with id extractor"),
    Route("/test", "POST", response=Response(201, body={"id": ToInt("123{testId}"), "username": "test2"}),
          body={"id": ToInt("123{testId}"), "username": "test2"},
          doc="Test post request which uses the previously stored id"),
    Route("/test", "POST", response=Response(201, body={"id": ToInt("1234"), "username": "test2"}),
          body={"id": ToInt("123{testId}"), "username": "test2"},
          doc="This test should fail"),
]


@test()
def test_passes():
    """This test should allways pass"""
    return True


@test()
def test_fails():
    """This test should allways fail"""
    return False


@http_test()
def http_test_fails():
    routes = [
        Route("/test", "GET", response=200,
              store=[Extractor("response.body-object.id", "testId")],
              doc="Test get request with id extractor"),
        Route("/test", "POST", response=Response(201, body={"id": ToInt("123{testId}"), "username": "test2"}),
              body={"id": ToInt("123{testId}"), "username": "test2"},
              doc="Test post request which uses the previously stored id"),
        Route("/test", "POST", response=Response(201, body={"id": ToInt("1234"), "username": "test2"}),
              body={"id": ToInt("123{testId}"), "username": "test2"},
              doc="This test should fail"),
    ]
    return visit(routes)


@http_test()
def http_test_passes():
    routes = [
        Route("/test", "GET", response=200,
              store=[Extractor("response.body-object.id", "testId")],
              doc="Test get request with id extractor"),
        Route("/test", "POST", response=Response(201, body={"id": ToInt("123{testId}"), "username": "test2"}),
              body={"id": ToInt("123{testId}"), "username": "test2"},
              doc="Test post request which uses the previously stored id"),
    ]
    return visit(routes)
