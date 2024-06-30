import requests as r
from .decorators import test
from .http import HttpRoutesWrapper, filter_routes, filter_hosts, HTTPResult, handle_routes, CONFIG, Route


@test(wrapper=HttpRoutesWrapper)
def test_routes(route=None, host=None, use_session=None, config=CONFIG):
    options = config['options']

    if use_session is None and 'session' in options:
        use_session = options['session']
    routes = filter_routes(route, config['routes'])
    hosts = filter_hosts(host, config['hosts'])
    if use_session:
        session = r.session()
    else:
        session = r
    if len(routes) == 0:
        pass
        return HTTPResult("No routes found.", False, Route('/'), '/')
    else:
        return handle_routes(session, hosts, routes)
