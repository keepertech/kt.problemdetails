# (c) 2021.  Keeper Technology LLC.  All Rights Reserved.
# Use is subject to license.  Reproduction and distribution is strictly
# prohibited.
#
# Subject to the following third party software licenses and terms and
# conditions (including open source):  www.keepertech.com/thirdpartylicenses

"""\
Tests for kt.problemdetails use of adaptation.

"""

import logging
import unittest

import zope.component
import zope.interface

import kt.problemdetails.api
import kt.problemdetails.interfaces
import tests.utils


class ISomething(zope.interface.Interface):
    """Marker interface for an adaptable thing."""


class SadException(Exception):
    """ """

    def __str__(self):
        return ''


class AdaptationTestCase(unittest.TestCase):

    def test_no_adaptation_fallback(self):
        error = tests.utils.SampleError('bad stuff happened')

        data = kt.problemdetails.api.as_dict(error)

        self.assertEqual(data['detail'], 'bad stuff happened')
        self.assertEqual(data['status'], 500)
        self.assertEqual(data['title'], 'Something evil this way comes.')
        self.assertNotIn('instance', data)
        self.assertNotIn('type', data)

    def test_no_adaptation_fallback_no_text(self):
        error = SadException()

        data = kt.problemdetails.api.as_dict(error)

        self.assertEqual(data['status'], 500)
        self.assertNotIn('detail', data)
        self.assertNotIn('instance', data)
        self.assertNotIn('title', data)
        self.assertNotIn('type', data)

    def test_no_adaptation_needed(self):
        error = tests.utils.SampleProblemDetails()

        data = kt.problemdetails.api.as_dict(error)

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

        data = kt.problemdetails.api.as_dict(error)

        self.assertEqual(data['detail'], 'They are coming for you.')
        self.assertEqual(data['status'], 409)
        self.assertEqual(data['title'], 'The Immortal Dead Have Arrived')
        self.assertEqual(data['type'], 'https://api.example.com/errors/tidha')
        self.assertNotIn('instance', data)
        # Extension fields:
        self.assertEqual(data['exception_class'], 'tests.utils.SampleError')

    def test_extensions_cannot_override_standard_fields(self):
        error = tests.utils.SampleProblemDetails(
            extensions=dict(status='foo!'))

        with self.assertLogs('kt.problemdetails', logging.WARNING) as cm:
            data = kt.problemdetails.api.as_dict(error)

        rec, = cm.records
        self.assertEqual(rec.levelno, logging.WARNING)
        self.assertEqual(rec.name, 'kt.problemdetails.api')
        self.assertEqual(rec.getMessage(),
                         "extensions should not contain key 'status'")
