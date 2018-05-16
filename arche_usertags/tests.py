import unittest

from arche.interfaces import IObjectUpdatedEvent, IIndexedContent, IContent
from arche.testing import barebone_fixture
from arche.utils import get_view
from pyramid import testing
from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPNotFound
from zope.interface import Interface
from zope.interface import implementer
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject

from arche_usertags.interfaces import IUserTags


class IDummy(IContent):
    pass


@implementer(IDummy, IIndexedContent)
class DummyContext(testing.DummyResource):
    uid = 'uid'


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
        self.config.include('arche_usertags.views')
        context = DummyContext()
        obj = self._cut(context)
        obj.name = 'test'
        request = testing.DummyRequest()
        self.assertEqual(obj.add_url(request), 'http://example.com/autags/test/+/uid')

    def test_remove_url(self):
        self.config.include('arche_usertags.views')
        context = DummyContext()
        obj = self._cut(context)
        obj.name = 'test'
        request = testing.DummyRequest()
        self.assertEqual(obj.remove_url(request), 'http://example.com/autags/test/-/uid')

    def test_action_url(self):
        self.config.include('arche_usertags.views')
        context = DummyContext()
        obj = self._cut(context)
        obj.name = 'test'
        request = testing.DummyRequest()
        self.assertEqual(obj.action_url(request, 'hello'), 'http://example.com/autags/test/hello/uid')

    def test_convert_to_other_set(self):
        context = DummyContext()
        obj = self._cut(context)

    def test_add_allowed(self):
        context = DummyContext()
        obj = self._cut(context)
        obj.name = 'test'
        self.config.testing_securitypolicy('jane_doe', permissive=True)
        request = testing.DummyRequest()
        self.assertEqual(obj.add_allowed(request), True)
        self.config.testing_securitypolicy('jane_doe', permissive=False)
        request = testing.DummyRequest()
        self.assertEqual(obj.add_allowed(request), False)

    def test_view_allowed(self):
        self.config.testing_securitypolicy('jane_doe')
        context = DummyContext()
        obj = self._cut(context)
        obj.name = 'test'
        request = testing.DummyRequest()
        self.assertEqual(obj.view_allowed(request), True)
        self.config.testing_securitypolicy('jane_doe', permissive=False)
        request = testing.DummyRequest()
        self.assertEqual(obj.view_allowed(request), False)

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

    def test_add_perm_callback(self):
        self.config.testing_securitypolicy('jane_doe')
        context = DummyContext()
        obj = self._cut(context)

        def _perm_callback_true(*args):
            return True

        def _perm_callback_false(*args):
            return False

        request = testing.DummyRequest()
        obj.add_perm_callback = _perm_callback_true
        self.assertTrue(obj.add_allowed(request))
        obj.add_perm_callback = _perm_callback_false
        self.assertFalse(obj.add_allowed(request))


class UserTagsViewTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.include('arche.testing')
        self.config.include('arche.testing.catalog')

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from arche_usertags.views import UserTagsView
        return UserTagsView

    def _mk_view(self, action = '', tag = 'testing', uid = 'uid' ,is_xhr = True):
        root = barebone_fixture(self.config)
        root['context'] = context = DummyContext()
        matchdict = {'action': action, 'tag': tag, 'uid': uid}
        request = testing.DummyRequest(matchdict = matchdict, is_xhr = is_xhr)
        request.root = root
        return self._cut(context, request)

    def _register_dummy_adapter(self):
        from arche_usertags.models import UserTags
        class _UserTags(UserTags):
            name = 'testing'
        self.config.registry.registerAdapter(_UserTags, required = (IDummy,), name = 'testing')

    def test_call(self):
        self.config.testing_securitypolicy('mrs_hello')
        view = self._mk_view(action = 'dummy')
        view.dummy = lambda: 'hello world'
        view.actions['dummy'] = 'dummy'
        self.assertEqual(view(), 'hello world')

    def test_get_action_existing_method_no_user(self):
        view = self._mk_view(action = '+')
        self.assertRaises(HTTPForbidden, view.get_action)

    def test_get_action(self):
        self.config.testing_securitypolicy('jane_doe')
        view = self._mk_view(action = 'dummy')
        view.dummy = lambda: 'hello world'
        view.actions['dummy'] = 'dummy'
        self.assertEqual(view.get_action(), view.dummy)

    def test_get_action_nonexistent(self):
        self.config.testing_securitypolicy('jane_doe')
        view = self._mk_view(action = '404')
        self.assertRaises(HTTPNotFound, view.get_action)

    def test_wrong_tag(self):
        self.config.testing_securitypolicy('mrs_hello')
        view = self._mk_view(tag = '404', action = '+')
        view.tag_context = DummyContext()
        try:
            view.adapter
            self.fail("HTTPNotFound should've been raised")
        except HTTPNotFound:
            pass

    def test_adapter(self):
        self._register_dummy_adapter()
        view = self._mk_view()
        self.assertTrue(IUserTags.providedBy(view.adapter))

    def test_add(self):
        self.config.include('.views')
        self._register_dummy_adapter()
        self.config.testing_securitypolicy('jane_doe')
        view = self._mk_view(tag = 'testing', action = '+')
        view.add()
        self.assertIn('jane_doe', view.adapter)

    def test_add_not_authorized(self):
        self._register_dummy_adapter()
        self.config.testing_securitypolicy('jane_doe', permissive = False)
        view = self._mk_view(action = '+')
        self.assertRaises(HTTPForbidden, view.add)

    def test_remove(self):
        self.config.include('.views')
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
