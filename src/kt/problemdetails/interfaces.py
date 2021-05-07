# (c) 2021.  Keeper Technology LLC.  All Rights Reserved.
# Use is subject to license.  Reproduction and distribution is strictly
# prohibited.
#
# Subject to the following third party software licenses and terms and
# conditions (including open source):  www.keepertech.com/thirdpartylicenses

"""\
Interface definitions for :mod:`kt.problemdetails`.

"""

import zope.interface
import zope.interface.common.mapping
import zope.schema


class IProblemDetails(zope.interface.Interface):
    """Interface providing information that goes into an :rfc:`7807`
    problem report.

    The standardized fields for a problem report are provided as simple
    attributes, while extension fields are available via a method.

    """

    type = zope.schema.URI(
        title='Problem type reference',
        description='Reference to type of problem',
        required=False,
        missing_value=None,
    )

    title = zope.schema.TextLine(
        title='Title',
        description='Human-facing title describing the application error',
        required=False,
        missing_value=None,
    )

    status = zope.schema.Int(
        title='Status code',
        description='HTTP status code',
        min=400,
        max=599,
        required=False,
        missing_value=None,
    )

    detail = zope.schema.Text(
        title='Detailed description',
        description='Human-facing description of this instance of the problem',
        required=False,
        missing_value=None,
    )

    instance = zope.schema.URI(
        title='Instance reference',
        description='Reference to specific instance of problem',
        required=False,
        missing_value=None,
    )

    def extensions() -> zope.interface.common.mapping.IEnumerableMapping:
        """Return mapping of extension fields to be included in response."""
