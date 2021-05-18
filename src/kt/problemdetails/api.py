# (c) 2021.  Keeper Technology LLC.  All Rights Reserved.
# Use is subject to license.  Reproduction and distribution is strictly
# prohibited.
#
# Subject to the following third party software licenses and terms and
# conditions (including open source):  www.keepertech.com/thirdpartylicenses

"""\
Serialization support for RFC 7807 Problem Details.

"""

import json
import logging
import xml.sax.saxutils

import flask
import flask.app

import kt.problemdetails.interfaces


CONTENT_TYPE_BASE = 'application/problem'

CONTENT_TYPE_JSON = CONTENT_TYPE_BASE + '+json'
"""Media type for JSON-encoded problem details."""

CONTENT_TYPE_XML = CONTENT_TYPE_BASE + '+xml'
"""Media type for XML-encoded problem details."""

logger = logging.getLogger(__name__)


def as_dict(error):
    """Convert error to JSON-encodable dictionary.

    If no adaption to
    :class:`~kt.problemdetails.interfaces.IProblemDetails` is available,
    a minimal problem details structure is generated.

    """
    err = kt.problemdetails.interfaces.IProblemDetails(error, None)
    if err is None:
        # Use fallback for exceptions:
        detail = str(error).strip()
        title = (error.__class__.__doc__ or '').strip()
        data = dict(
            status=500,
        )
        if detail:
            data['detail'] = detail
        if title:
            data['title'] = title
    else:
        data = dict(err.extensions())
        for attr in ('type', 'title', 'status', 'detail', 'instance'):
            if attr in data:
                logger.warning(f'extensions should not contain key {attr!r}')
            value = getattr(err, attr, None)
            if value is not None:
                data[attr] = value
    return data


def render_json(error, headers=None):
    """Render error as application/problem+json.

    If *headers* is given and non-``None``, it must be be mapping of
    additional headers that should be returned in the request.  If a
    **Content-Type** header is provided, it will be used instead of the
    default value for JSON problem detail responses.

    Returns a Flask response.

    """
    data = as_dict(error)
    status = _get_status(data)
    content = json.dumps(data, cls=flask.current_app.json_encoder)
    return _response(data, content, status, headers, CONTENT_TYPE_JSON)


def render_xml(error, headers=None):
    """Render error as application/problem+xml.

    If *headers* is given and non-``None``, it must be be mapping of
    additional headers that should be returned in the request.  If a
    **Content-Type** header is provided, it will be used instead of the
    default value for XML problem detail responses.

    Returns a Flask response.

    """
    data = as_dict(error)
    status = _get_status(data)
    content = [
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<problem xmlns="urn:ietf:rfc:7807">\n'
    ]
    have_data = False

    def serialize(name, value, indent='  '):
        if isinstance(value, list):
            content.append(f'{indent}<{name}>\n')
            for val in value:
                serialize('i', val, indent + '  ')
            content.append(f'{indent}</{name}>\n')
        elif isinstance(value, dict):
            content.append(f'{indent}<{name}>\n')
            for vname, val in value.items():
                serialize(vname, val, indent + '  ')
            content.append(f'{indent}</{name}>\n')
        else:
            value = xml.sax.saxutils.escape(str(value))
            content.append(f'{indent}<{name}>{value}</{name}>\n')

    # These are in the same order as defined in the specification.
    for attr in ('type', 'title', 'status', 'detail', 'instance'):
        if attr in data:
            have_data = True
            value = data.pop(attr)
            serialize(attr, value)

    # Ensure remaining bits are JSON-encodable, so that atypical
    # types are handled before applying RFC 7807 serialization
    # rules.
    if data:
        cooked = json.dumps(data, cls=flask.current_app.json_encoder)
        data = json.loads(cooked)
        if have_data:
            content.append('\n')

        for name, value in data.items():
            serialize(name, value)

    content.append('</problem>\n')
    content = ''.join(content)
    return _response(data, content, status, headers, CONTENT_TYPE_XML)


def _response(data, content, status, headers, ctype):
    content = content.encode('utf-8')
    hdrs = flask.app.Headers()
    if headers is not None:
        hdrs.extend(headers)
    if 'Content-Type' not in hdrs:
        hdrs['Content-Type'] = ctype
    return flask.make_response(content, status, hdrs)


def _get_status(data):
    if 'status' not in data:
        logger.warning('response status not defined; applying 500')
        return 500
    else:
        return data['status']
