# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, unicode_literals, print_function
from builtins import *  # dirty hack
from future.utils import PY3, python_2_unicode_compatible

import sys
from six.moves.urllib.parse import parse_qs, urlencode, quote_plus
from six.moves.urllib.parse import parse_qsl
from six.moves.collections_abc import Mapping, Sequence
# import json
from collections import namedtuple
from itertools import chain
from contextlib import contextmanager
import pickle
from base64 import b64encode, b64decode
from inspect import ismethod
from py2n3 import gzip
from qualname import qualname

# Will be replaced with kodi.six
import xbmc
import xbmcgui
import xbmcplugin


class adict(dict):

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            return None

    def __getstate__(self):
        return dict(self)


def mkmdict(seq):
    dct = {}
    for key, val in seq:
        dct.setdefault(key, []).append(val)
    return dct


def get_attr(obj, name, default=None):
    if isinstance(name, str):
        name = name.split('.')
    if not name:
        return default
    if obj is None:
        try:
            obj = globals()[name[0]]
        except KeyError:
            return default
        name = name[1:]
    for key in name:
        try:
            obj = getattr(obj, key)
        except AttributeError:
            return default
    return obj


ParsedUrl = namedtuple('ParsedUrl', 'link multi fragment')
ParsedUrl.args = property(lambda self: adict((k, vv[-1]) for k, vv in self.multi.items() if vv))

Call = namedtuple('Call', 'method args')


class KopException(ValueError):
    pass


class KopIncorrectArgvError(KopException):
    pass


class KopRouter(object):
    def __init__(self):
        pass


def mkargs(*args, **kwargs):
    """Addon action arguments. Syntax suger."""
    return args, kwargs


def call(method, *args, **kwargs):
    """Addon action with arguments. Syntax suger."""
    return Call(method, (args, kwargs))


def encode_data(data):
    octet = b64encode(gzip.compress(pickle.dumps(data)), b'-_').replace(b'=', b'')
    return octet.decode('ascii')
    # return {k: _endcode_data_value(v) for k, v in data.items()}
    # return {k: json.dumps(v) for k, v in data.items()}


def decode_data(octet):
    if not isinstance(octet, bytes):
        octet = octet.encode('utf8')
    mod = len(octet) % 4
    if mod:  # restore padding
        octet += b'=' * (4 - mod)
    return pickle.loads(gzip.decompress(b64decode(octet, b'-_')))


def item_iter(obj):
    """
    Return item (key, value) iterator from dict or pair sequence.
    Empty seqence for None.
    """
    if obj is None:
        return ()
    if isinstance(obj, Mapping):
        return obj.items()
    return obj


def encode_url(url, direct=None, encode=None):
    """
    Helper. Make URL with given data.

    All keys are quoted.
    All data from `direct` are quoted.
    All data from `encode` are picked (+gzip +b64).
    """
    direct = item_iter(direct)
    encode = item_iter(encode)
    sep = '&' if '?' in url else '?'
    return '%s%s%s' % (url, sep, '&'.join(chain(
        ('%s=%s' % (quote_plus(k), quote_plus(v)) for k, v in direct),
        ('%s=%s' % (quote_plus(k), encode_data(v)) for k, v in encode))))


def make_url(*args, **kwargs):
    """
    Make URL:  make_url(url, [encode_keys,] ...)

    Any keyword parameters are encoded into query.
    On all values with key from `encode_keys` encode_data() is used.
    """
    if not 1 <= len(args) <= 2:
        raise TypeError('Missing argument, use make_url(url, [encode_keys,]...)')
    url = args[0]
    if len(args) == 1:
        return encode_url(url, direct=kwargs)
    encode_keys = args[1]
    direct = {k: v for k, v in kwargs if k not in encode_keys}
    encode = {k: v for k, v in kwargs if k in encode_keys}
    return encode_url(url, direct=direct, encode=encode)


def parse_url(url, encode_keys=None):
    """
    Split URL into link (scheme, host, port...) and encoded query and fragment.
    """
    def parse_val(key, val):
        if key in encode_keys:
            return decode_data(val)
        return val

    if encode_keys is None:
        encode_keys = ()
    url, _, fragment = url.partition('#')
    url, _, query = url.partition('?')
    multi_args = mkmdict((k, parse_val(k, v)) for k, v in parse_qsl(query))
    return ParsedUrl(url, multi_args, fragment)


@python_2_unicode_compatible
class KopAddon(object):
    """
    Main Kodi Addon object. Does all dirty work for you.

    KopAddon([argv])

    Parameters
    ----------
    args : list or None
        Kodi plugin args (url, addon_id, query)
    """

    #: Keys for decode variables in URL query.
    encoded_keys = {'params', 'data'}

    def __init__(self, argv=None):
        if argv is None:
            argv = sys.argv
        if len(argv) < 3 or not argv[1].isdigit() or argv[2][:1] != '?':
            raise KopIncorrectArgvError('Incorrect addon args: %s' % argv)
        self.link = argv[0]
        self.id = int(argv[1])
        purl = parse_url(argv[2], self.encoded_keys)
        self.multi = purl.multi
        self.args = purl.args

    def __repr__(self):
        return 'KopAddon(id={self.id}, args={self.args})'.format(self=self)

    def mkurl(self, action='', params=None, data=None, **kwargs):
        """
        Make addon URL with given data.

        Argument `action` has to be a string.
        If `params` or `data` is not None then is is picked (+gzip +b64) first.
        All other data in `kwargs` will be just quoted.
        """
        kwargs['action'] = action
        encode = {}
        if params is not None:
            encode['params'] = params
        if data is not None:
            encode['data'] = data
        return encode_url(self.link, direct=kwargs, encode=encode)

    def dispatcher(self, root, missing=None):
        """
        Addon URL dispatcher.
        """
        action = self.args.get('action')
        params = self._get_call_params()
        if action:
            handle = self._find_call(action)
            if handle:
                self._call(handle, *params)
            elif missing is not None:
                self._call(missing, (action,))
        else:
            assert root
            self._call(root)

    @contextmanager
    def directory(self, safe=False):
        kd = AddonDirectory(self)
        try:
            yield kd
        except:
            kd.end(False)
            if not safe:
                raise
        else:
            kd.end(True)
        finally:
            pass

    def _get_call_params(self):
        params = self.args.get('params')
        if not isinstance(params, Sequence):
            return (), {}
        if len(params) == 2:
            return params
        params = params[:2]
        if not params:
            return ((), {})
        if len(params) == 1:
            return (params[0], {})
        return params

    def _find_call(self, name):
        handle = get_attr(None, name)
        return handle

    def _call(self, handle, args=None, kwargs=None):
        if args is None:
            args = ()
        if kwargs is None:
            kwargs = {}
        print('CALL', handle, args, kwargs)
        return handle(*args, **kwargs)


class AddonDirectory(object):
    """
    Thiny wrapper for plugin list.

    See: xbmcgui.ListItem, xbmcplugin.addDirectoryItem, xbmcplugin.endOfDirectory.
    """

    def __init__(self, addon=None):
        if addon is None:
            addon = globals()['addon']
        self.addon = addon

    def end(self, success=True):
        xbmcplugin.endOfDirectory(self.addon.id, success)

    def add_dir(self, *args):
        if not args:
            raise TypeError('AddonDirectory.add_dir() Missing endpoint argument')
        name = None
        params = ()
        if len(args) < 2:
            if isinstance(args[0], str):
                name = endpoint = args[0]
            else:
                endpoint = args[0]
        elif len(args) < 3:
            name, endpoint = args
        else:
            raise TypeError('AddonDirectory.add_dir() Too many arguments')
        if isinstance(endpoint, Call):
            endpoint, params = endpoint.method, endpoint.args
        if ismethod(endpoint):
            obj = endpoint.__self__
            ser = obj
            if not params:
                params = (), {}
            params = (ser,) + params[0], params[1]
        if name is None:
            handle = self.addon._find_call(endpoint)
            if handle:
                name = getattr(handle, 'title', endpoint)
            else:
                name = endpoint
        url = self.addon.mkurl(qualname(endpoint), params=params or None)
        item = xbmcgui.ListItem(name)
        xbmcplugin.addDirectoryItem(handle=self.addon.id, url=url, listitem=item, isFolder=True)
        print('DD : %r : %r' % (name, url))
        print('ITEM·%s·%s·' % (name, url))
        return item


def test_1():
    addon = KopAddon()
    print(addon.args)
    print(addon.args.a)
    print(addon.args.b)
    print(addon)
    print(str(addon))
    dd = ({'a': 42, 'b': 'abc', 'c': 'zażółć', 'd': {'x': 1, 'y': 2.3, 'z': 'żółw'}})
    # print(f'dd={dd!r} -> {pickle.dumps(dd)!r}')
    url = addon.mkurl('go', data=dd)
    print(url)
    print(KopAddon(['plugin://aaaby', '124', '?'+url.partition('?')[2]]).args)


# Command-line tests
if __name__ == '__main__':
    if sys.argv[1:2] == ['--fake']:
        del sys.argv[:2]



def grab_videos():
    return ()


# class my_cda(Directory):
#     content = 'videos'
#     title = 'Moje CDA'
#
#     def directory(self):
#         with addon.directory() as kd:
#             kd.title = self.title
#             kd.content = 'addons'
#             kd.add_dir('Moje CDA', my_cda)


class Foo(object):

    N = 5

    def __init__(self, x, y=8, z=9):
        self.x = x
        self.y = y
        self.z = z

    def my_anything(self, a, b=2, c=3):
        print('Foo(x=%r, y=%r, z=%r).anything(a=%r, b=%r, c=%r) Foo.N=%r' % (self.x, self.y, self.z, a, b, c, self.N))

    @classmethod
    def my_class(cls, a, b=2, c=3):
        print('Foo.anything(a=%r, b=%r, c=%r) Foo.N=%r' % (a, b, c, cls.N))

    @staticmethod
    def my_static(a, b=2, c=3):
        print('Foo.anything(a=%r, b=%r, c=%r) no N' % (a, b, c))


def my_anything(a, b=2, c=3):
    print('anything(a=%r, b=%r, c=%r)' % (a, b, c))


def my_history():
    with addon.directory() as kd:
        kd.title = 'Moje CDA'
        kd.content = 'videos'
        for video in grab_videos():
            kd.add_item(video)


def my_cda():
    with addon.directory() as kd:
        kd.title = 'Moje CDA'
        kd.content = 'addons'
        kd.add_dir('Historia', my_history)
        kd.add_dir('Cokolwiek 1', call(my_anything, 42, c=123))
        kd.add_dir('Cokolwiek 2', call(Foo.my_static, 42, c=123))
        kd.add_dir('Cokolwiek 3', call(Foo.my_class, 42, c=123))
        kd.add_dir('Cokolwiek 4', call(Foo(77, z=99).my_anything, 42, c=123))


def root():
    with addon.directory() as kd:
        kd.title = 'Nowe CDA'
        kd.content = 'addons'
        kd.add_dir('Moje CDA', my_cda)


def missing(name):
    print('Action %r not found' % name)


addon = KopAddon()
print('Addon args: %r' % addon.args)

xbmc.log('Aaaby argv: %r' % sys.argv, xbmc.LOGINFO)
addon.dispatcher(root, missing=missing)
