=====================================================
kt.problemdetails -- RFC 7807 Problem Details support
=====================================================

``kt.problemdetails`` supports generation of :rfc:`7807` responses via
adaptation from exception objects.  Specific adaptations can be
configured to produce serializations appropriate to specific exceptions.

The current implementation works with the Flask_ web framework.


Release history
---------------

#. Explicitly support Python 3.10.


1.0.0 (2021-05-20)
~~~~~~~~~~~~~~~~~~

Initial release, internal to Keeper Technology, LLC.


.. _Flask:
   https://flask.palletsprojects.com/
