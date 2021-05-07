# (c) 2021.  Keeper Technology LLC.  All Rights Reserved.
# Use is subject to license.  Reproduction and distribution is strictly
# prohibited.
#
# Subject to the following third party software licenses and terms and
# conditions (including open source):  www.keepertech.com/thirdpartylicenses

"""\
Tests support for kt.problemdetails tests.

"""

import unittest

import flask
import zope.interface

import kt.problemdetails.interfaces


class ProblemDetailsTestCase(unittest.TestCase):

    def setUp(self):
        super(ProblemDetailsTestCase, self).setUp()
        self.app = flask.Flask(__name__)
        self.app.config['PROPAGATE_EXCEPTIONS'] = True
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def request_context(self, *args, **kwargs):
        return self.app.test_request_context(*args, **kwargs)

    def http_get(self, path, status=200):
        response = self.client.get(path)
        if status:
            self.assertEqual(
                response.status_code, status,
                f'GET {path} status {response.status_code}, expected {status}')
        return response


class SampleError(Exception):
    """Something evil this way comes."""


@zope.interface.implementer(kt.problemdetails.interfaces.IProblemDetails)
class SampleProblemDetails:

    def __init__(self, extensions=None):
        self.status = 400
        self.title = 'Evil is Coming'
        self.detail = 'Evil is coming to *your* town.'
        self.instance = 'https://api.example.com/errors/evil?town=54321'
        self.type = 'https://api.example.com/errors/evil'
        if extensions is None:
            extensions = dict(
                severity='really, really bad',
                whence='Depths of Hades',
            )
        self._extensions = extensions

    def extensions(self):
        return self._extensions


@zope.interface.implementer(kt.problemdetails.interfaces.IProblemDetails)
class SampleAdapter:

    def __init__(self, context):
        self.context = context
        self.status = 409
        self.title = 'The Immortal Dead Have Arrived'
        self.detail = 'They are coming for you.'
        self.instance = None
        self.type = 'https://api.example.com/errors/tidha'

    def extensions(self):
        cls = self.context.__class__
        clsname = f'{cls.__module__}.{cls.__qualname__}'
        return dict(
            exception_class=clsname,
        )
