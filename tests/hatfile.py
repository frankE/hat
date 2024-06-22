from hat.http import Route, Extractor, Response, ToInt

HOSTS = ["http://localhost:8080/",]

ROUTES = [
    Route("/test", "GET", response=200,
          store=[Extractor("response.body-object.id", "testId")],
          doc="Test get request with id extractor"),
    Route("/test", "POST", response=Response(201, body={"id": ToInt("123{testId}"), "username": "test2"}),
          body={"id": ToInt("123{testId}"), "username": "test2"},
          doc="Test post request which uses the previously stored id"),
]

OPTIONS = {
    "session": True,
}
