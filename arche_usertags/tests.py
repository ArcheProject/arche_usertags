import unittest

from arche.interfaces import IObjectUpdatedEvent
from arche.utils import get_view
from pyramid import testing
from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPNotFound
from zope.interface import Interface
from zope.interface import implementer
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject

from arche_usertags.interfaces import IUserTags


class IDummy(Interface):
    pass


@implementer(IDummy)
class DummyContext(testing.DummyResource):
    pass


class UserTagsTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from arche_usertags.models import UserTags
        return UserTags

    def test_verify_class(self):
        self.assertTrue(verifyClass(IUserTags, self._cut))

    def test_verify_obj(self):
        context = DummyContext()
        self.assertTrue(verifyObject(IUserTags, self._cut(context)))

    def test_add(self):
        context = DummyContext()
        obj = self._cut(context)
        obj.name = 'test'
        obj.add('admin')
        self.assertIn('test', obj.storage)
        self.assertIn('admin', obj)

    def test_add_notify(self):
        L = []
        def subsc(obj, event):
            L.append(event)
        self.config.add_subscriber(subsc, [IDummy, IObjectUpdatedEvent])
        context = DummyContext()
        obj = self._cut(context)
        obj.name = 'test'
        obj.catalog_index = 'something'
        obj.add('admin')
        self.assertEqual(len(L), 1)
        self.assertIn('something', L[0].changed)

    def test_remove(self):
        context = DummyContext()
        obj = self._cut(context)
        obj.name = 'test'
        obj.add('admin')
        obj.remove('admin')
        self.assertNotIn('admin', obj)

    def test_remove_notify(self):
        L = []
        def subsc(obj, event):
            L.append(event)
        self.config.add_subscriber(subsc, [IDummy, IObjectUpdatedEvent])
        context = DummyContext()
        obj = self._cut(context)
        obj.name = 'test'
        obj.catalog_index = 'something'
        obj.add('admin', notify = False)
        self.assertEqual(len(L), 0)
        obj.remove('admin')
        self.assertEqual(len(L), 1)
        self.assertIn('something', L[0].changed)

    def test_add_url(self):
        context = DummyContext()
        obj = self._cut(context)
        obj.name = 'test'
        request = testing.DummyRequest()
        self.assertEqual(obj.add_url(request), 'http://example.com/__usertags__/test/+')

    def test_remove_url(self):
        context = DummyContext()
        obj = self._cut(context)
        obj.name = 'test'
        request = testing.DummyRequest()
        self.assertEqual(obj.remove_url(request), 'http://example.com/__usertags__/test/-')

    def test_action_url(self):
        context = DummyContext()
        obj = self._cut(context)
        obj.name = 'test'
        request = testing.DummyRequest()
        self.assertEqual(obj.action_url(request, 'hello'), 'http://example.com/__usertags__/test/hello')

    def test_empty_is_true(self):
        context = DummyContext()
        obj = self._cut(context)
        self.assertTrue(obj)

    def test_convert_to_other_set(self):
        context = DummyContext()
        obj = self._cut(context)
        obj.name = 'test'
        obj.add('a')
        obj.add('b')
        obj.add('c')
        self.assertEqual(frozenset(obj), frozenset(['a', 'b', 'c']))


class UserTagsViewTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from arche_usertags.views import UserTagsView
        return UserTagsView

    def _mk_view(self, subpath = (), tag = 'testing', is_xhr = True):
        context = DummyContext()
        request = testing.DummyRequest(subpath = subpath, is_xhr = is_xhr)
        view = self._cut(context, request)
        view.tag = tag
        return view

    def _register_dummy_adapter(self):
        from arche_usertags.models import UserTags
        class _UserTags(UserTags):
            name = 'testing'
        self.config.registry.registerAdapter(_UserTags, required = (IDummy,), name = 'testing')

    def test_call(self):
        self.config.testing_securitypolicy('mrs_hello')
        view = self._mk_view(subpath = ('testing', 'dummy'))
        view.dummy = lambda: 'hello world'
        view.actions['dummy'] = 'dummy'
        self.assertEqual(view(), 'hello world')

    def test_get_action_no_subpath(self):
        view = self._mk_view()
        self.assertRaises(HTTPNotFound, view.get_action)

    def test_get_action_wrong_action(self):
        view = self._mk_view(subpath = ('testing', '404'))
        self.assertRaises(HTTPNotFound, view.get_action)

    def test_get_action_existing_method_no_user(self):
        view = self._mk_view(subpath = ('testing', '+'))
        self.assertRaises(HTTPForbidden, view.get_action)

    def test_get_action_wrong_tag(self):
        view = self._mk_view(subpath = ('404', '+'))
        self.assertRaises(HTTPNotFound, view.get_action)

    def test_get_action_add(self):
        self.config.testing_securitypolicy('jane_doe')
        view = self._mk_view(subpath = ('testing', '+'))
        self.assertEqual(view.get_action(), view.add)

    def test_get_list(self):
        self.config.testing_securitypolicy('jane_doe')
        view = self._mk_view(subpath = ('testing', 'list'))
        self.assertEqual(view.get_action(), view.list)

    def test_get_remove(self):
        self.config.testing_securitypolicy('jane_doe')
        view = self._mk_view(subpath = ('testing', '-'))
        self.assertEqual(view.get_action(), view.remove)

    def test_adapter(self):
        self._register_dummy_adapter()
        view = self._mk_view()
        self.assertTrue(IUserTags.providedBy(view.adapter))

    def test_add(self):
        self._register_dummy_adapter()
        self.config.testing_securitypolicy('jane_doe')
        view = self._mk_view(subpath = ('testing', '+'))
        view.add()
        self.assertIn('jane_doe', view.adapter)

    def test_add_not_authorized(self):
        self._register_dummy_adapter()
        self.config.testing_securitypolicy('jane_doe', permissive = False)
        view = self._mk_view()
        self.assertRaises(HTTPForbidden, view.add)

    def test_remove(self):
        self._register_dummy_adapter()
        self.config.testing_securitypolicy('jane_doe')
        view = self._mk_view()
        view.adapter.add('jane_doe')
        self.assertIn('jane_doe', view.adapter)
        view.remove()
        self.assertNotIn('jane_doe', view.adapter)

    def test_list(self):
        self._register_dummy_adapter()
        view = self._mk_view()
        self.assertEqual(view.list(), {'items': ()})
        view.adapter.add('jane_doe')
        self.assertEqual(view.list(), {'items': ('jane_doe',)})


class UserTagsUtilsTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.include('arche_usertags.utils')

    def tearDown(self):
        testing.tearDown()

    def test_add_usertag_adds_adapter(self):
        self.config.testing_securitypolicy('hello_there')
        self.config.add_usertag('testing', IDummy)
        context = DummyContext()
        self.failUnless(self.config.registry.queryAdapter(context, IUserTags, name = 'testing'))

    def test_add_usertag_adds_view(self):
        self.config.testing_securitypolicy('hello_there')
        self.config.add_usertag('testing', IDummy)
        context = DummyContext()
        request = testing.DummyRequest()
        self.assertTrue(get_view(context, request, view_name = '__usertags__'))
