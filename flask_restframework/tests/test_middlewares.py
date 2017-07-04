import base64

import pytest
from flask.wrappers import Response

from flask.ext.restframework.authentication_backend import SimpleBasicAuth
from flask.ext.restframework.middlewares import AuthenticationMiddleware
from flask.ext.restframework.tests.compat import mock


@pytest.mark.test_auth_middleware_with_basic_auth
def test_auth_middleware_with_basic_auth():

    am = AuthenticationMiddleware(mock.Mock(
        config={
            "BASIC_AUTH_LOGIN": "1",
            "BASIC_AUTH_PASSWORD": "1"
        }
    ))



    with mock.patch.object(AuthenticationMiddleware, "get_view") as m:
        m.return_value = mock.Mock(
            authentication_backends=[SimpleBasicAuth]
        )

        with mock.patch("flask.globals.request") as m:
            response = am.before_request()
        assert response.headers['WWW-Authenticate'] == 'Basic realm="User Visible Realm"'
        assert response.status_code == 401


        with mock.patch("flask.globals.request", mock.Mock(
            authorization=mock.Mock(
                username="1",
                password="2"
            )
        )):
            response = am.before_request()
            assert response.headers['WWW-Authenticate'] == 'Basic realm="User Visible Realm"'
            assert response.status_code == 401

        with mock.patch("flask.globals.request", mock.Mock(
            authorization=mock.Mock(
                username="1",
                password="1"
            )
        )):
            response = am.before_request()
            assert response == None


