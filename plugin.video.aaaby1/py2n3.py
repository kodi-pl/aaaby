# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, unicode_literals, print_function
from builtins import *  # dirty hack
# from future.utils import PY3, python_2_unicode_compatible

import gzip
if not hasattr(gzip, 'compress'):
    from io import BytesIO

    def gzip_compress(data, compresslevel=9):
        """
        Missing gzip.compress implementation for older Python then 3.2.

        Compress the data, returning a bytes object containing
        the compressed data. compresslevel and mtime have the same
        meaning as in the GzipFile constructor above.
        """
        buf = BytesIO()
        with gzip.GzipFile(fileobj=buf, mode='wb', compresslevel=compresslevel) as f:
            f.write(data)
        return buf.getvalue()

    def gzip_decompress(data):
        """
        Missing gzip.decompress implementation for older Python then 3.2.

        Decompress the data, returning a bytes object containing the uncompressed data.
        """
        buf = BytesIO(data)
        with gzip.GzipFile(fileobj=buf, mode='rb') as f:
            return f.read(data)

    gzip.compress = gzip_compress
    gzip.decompress = gzip_decompress
