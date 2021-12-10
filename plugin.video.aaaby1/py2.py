# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, unicode_literals, print_function
from six.moves.collections_abc import Mapping, Sequence
import json

#
# This file can NOT is futures and buildins
#


def _endcode_data_value(value):
    if isinstance(value, Mapping):
        return 'JSON:%s' % json.dumps(value, separators=(u',', u':'))
    if isinstance(value, str):
        return value
    if not isinstance(value, unicode):
        value = unicode(value)
    return value.encode('utf-8')
