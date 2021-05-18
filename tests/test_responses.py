# (c) 2021.  Keeper Technology LLC.  All Rights Reserved.
# Use is subject to license.  Reproduction and distribution is strictly
# prohibited.
#
# Subject to the following third party software licenses and terms and
# conditions (including open source):  www.keepertech.com/thirdpartylicenses

"""\
Tests for kt.problemdetails.api.render_* functions.

"""

import logging

import zope.component
import zope.interface

import kt.problemdetails.api
import tests.utils


class ISomething(zope.interface.Interface):
    """Marker interface for an adaptable thing."""


class JSONTestCase(tests.utils.ProblemDetailsTestCase):

    def render(self, error):

        @self.app.route('/foo')
        def my_route():
            return kt.problemdetails.api.render_json(error)

        resp = self.http_get('/foo', status=None)
        self.assertEqual(resp.headers['Content-Type'],
                         'application/problem+json')
        return resp

    def test_no_adaptation_fallback(self):
        error = tests.utils.SampleError('bad stuff happened')

        resp = self.render(error)
        data = resp.get_json()

        self.assertEqual(resp.status_code, 500)

        self.assertEqual(data['detail'], 'bad stuff happened')
        self.assertEqual(data['status'], 500)
        self.assertEqual(data['title'], 'Something evil this way comes.')
        self.assertNotIn('instance', data)
        self.assertNotIn('type', data)

    def test_no_adaptation_needed(self):
        error = tests.utils.SampleProblemDetails()

        resp = self.render(error)
        data = resp.get_json()

        self.assertEqual(resp.status_code, 400)

        self.assertEqual(data['detail'], 'Evil is coming to *your* town.')
        self.assertEqual(data['instance'],
                         'https://api.example.com/errors/evil?town=54321')
        self.assertEqual(data['status'], 400)
        self.assertEqual(data['title'], 'Evil is Coming')
        self.assertEqual(data['type'], 'https://api.example.com/errors/evil')
        # Extension fields:
        self.assertEqual(data['severity'], 'really, really bad')
        self.assertEqual(data['whence'], 'Depths of Hades')

    def test_adaptation_used(self):
        error = tests.utils.SampleError('bad stuff happened')
        zope.interface.alsoProvides(error, ISomething)
        zope.component.provideAdapter(
            factory=tests.utils.SampleAdapter,
            adapts=[ISomething],
            provides=kt.problemdetails.interfaces.IProblemDetails,
        )

        resp = self.render(error)
        data = resp.get_json()

        self.assertEqual(resp.status_code, 409)

        self.assertEqual(data['detail'], 'They are coming for you.')
        self.assertEqual(data['status'], 409)
        self.assertEqual(data['title'], 'The Immortal Dead Have Arrived')
        self.assertEqual(data['type'], 'https://api.example.com/errors/tidha')
        self.assertNotIn('instance', data)
        # Extension fields:
        self.assertEqual(data['exception_class'], 'tests.utils.SampleError')

    def test_override_content_type(self):
        error = tests.utils.SampleProblemDetails()

        @self.app.route('/bar')
        def my_route():
            return kt.problemdetails.api.render_json(
                error, headers={'Content-Type': 'application/issue+json'})

        resp = self.http_get('/bar', status=400)
        self.assertEqual(resp.headers['Content-Type'],
                         'application/issue+json')


class XMLTestCase(tests.utils.ProblemDetailsTestCase):

    expected_ctype = 'application/problem+xml'

    def render(self, error):

        @self.app.route('/foo')
        def my_route():
            return kt.problemdetails.api.render_xml(error)

        resp = self.http_get('/foo', status=None)
        self.assertEqual(resp.headers['Content-Type'], self.expected_ctype)
        return resp

    def test_no_adaptation_fallback(self):
        error = tests.utils.SampleError('bad stuff happened')

        resp = self.render(error)
        content = resp.data.decode('utf-8')

        self.assertEqual(resp.status_code, 500)
        self.assertEqual(
            content,
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<problem xmlns="urn:ietf:rfc:7807">\n'
            '  <title>Something evil this way comes.</title>\n'
            '  <status>500</status>\n'
            '  <detail>bad stuff happened</detail>\n'
            '</problem>\n'
        )

    def test_no_adaptation_needed(self):
        error = tests.utils.SampleProblemDetails()

        resp = self.render(error)
        content = resp.data.decode('utf-8')

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            content,
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<problem xmlns="urn:ietf:rfc:7807">\n'
            '  <type>https://api.example.com/errors/evil</type>\n'
            '  <title>Evil is Coming</title>\n'
            '  <status>400</status>\n'
            '  <detail>Evil is coming to *your* town.</detail>\n'
            '  <instance>https://api.example.com/errors/evil?town=54321'
            '</instance>\n'
            '\n'
            '  <severity>really, really bad</severity>\n'
            '  <whence>Depths of Hades</whence>\n'
            '</problem>\n'
        )

    def test_adaptation_used(self):
        error = tests.utils.SampleError('bad stuff happened')
        zope.interface.alsoProvides(error, ISomething)
        zope.component.provideAdapter(
            factory=tests.utils.SampleAdapter,
            adapts=[ISomething],
            provides=kt.problemdetails.interfaces.IProblemDetails,
        )

        resp = self.render(error)

        self.assertEqual(resp.status_code, 409)
        content = resp.data.decode('utf-8')
        self.assertEqual(
            content,
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<problem xmlns="urn:ietf:rfc:7807">\n'
            '  <type>https://api.example.com/errors/tidha</type>\n'
            '  <title>The Immortal Dead Have Arrived</title>\n'
            '  <status>409</status>\n'
            '  <detail>They are coming for you.</detail>\n'
            '\n'
            '  <exception_class>tests.utils.SampleError</exception_class>\n'
            '</problem>\n'
        )

    def test_list_serialization_simple(self):
        error = tests.utils.SampleProblemDetails(
            extensions=dict(
                sequence=['abc', 'def'],
            )
        )
        error.instance = None
        resp = self.render(error)
        content = resp.data.decode('utf-8')

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            content,
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<problem xmlns="urn:ietf:rfc:7807">\n'
            '  <type>https://api.example.com/errors/evil</type>\n'
            '  <title>Evil is Coming</title>\n'
            '  <status>400</status>\n'
            '  <detail>Evil is coming to *your* town.</detail>\n'
            '\n'
            '  <sequence>\n'
            '    <i>abc</i>\n'
            '    <i>def</i>\n'
            '  </sequence>\n'
            '</problem>\n'
        )

    def test_list_serialization_objects(self):
        error = tests.utils.SampleProblemDetails(
            extensions=dict(
                sequence=[dict(field='abc'), dict(field='def')],
            )
        )
        error.instance = None
        resp = self.render(error)
        content = resp.data.decode('utf-8')

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            content,
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<problem xmlns="urn:ietf:rfc:7807">\n'
            '  <type>https://api.example.com/errors/evil</type>\n'
            '  <title>Evil is Coming</title>\n'
            '  <status>400</status>\n'
            '  <detail>Evil is coming to *your* town.</detail>\n'
            '\n'
            '  <sequence>\n'
            '    <i>\n'
            '      <field>abc</field>\n'
            '    </i>\n'
            '    <i>\n'
            '      <field>def</field>\n'
            '    </i>\n'
            '  </sequence>\n'
            '</problem>\n'
        )

    def test_object_serialization_simple(self):
        error = tests.utils.SampleProblemDetails(
            extensions=dict(
                name=dict(
                    given='Frank',
                    mi='N',
                    surname='Stein',
                ),
            )
        )
        error.instance = None
        resp = self.render(error)
        content = resp.data.decode('utf-8')

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            content,
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<problem xmlns="urn:ietf:rfc:7807">\n'
            '  <type>https://api.example.com/errors/evil</type>\n'
            '  <title>Evil is Coming</title>\n'
            '  <status>400</status>\n'
            '  <detail>Evil is coming to *your* town.</detail>\n'
            '\n'
            '  <name>\n'
            '    <given>Frank</given>\n'
            '    <mi>N</mi>\n'
            '    <surname>Stein</surname>\n'
            '  </name>\n'
            '</problem>\n'
        )

    def test_override_content_type(self):
        error = tests.utils.SampleProblemDetails()

        @self.app.route('/bar')
        def my_route():
            return kt.problemdetails.api.render_xml(
                error, headers={'Content-Type': 'application/xml'})

        resp = self.http_get('/bar', status=400)
        self.assertEqual(resp.headers['Content-Type'], 'application/xml')

    def test_without_standard_fields(self):
        error = tests.utils.SampleProblemDetails()
        error.detail = None
        error.instance = None
        error.status = None
        error.title = None
        error.type = None

        with self.assertLogs('kt.problemdetails', logging.WARNING) as cm:
            resp = self.render(error)
        rec, = cm.records
        self.assertEqual(rec.levelno, logging.WARNING)
        self.assertEqual(rec.name, 'kt.problemdetails.api')
        self.assertEqual(rec.getMessage(),
                         'response status not defined; applying 500')
        content = resp.data.decode('utf-8')

        self.assertEqual(resp.status_code, 500)
        self.assertEqual(
            content,
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<problem xmlns="urn:ietf:rfc:7807">\n'
            '  <severity>really, really bad</severity>\n'
            '  <whence>Depths of Hades</whence>\n'
            '</problem>\n'
        )
