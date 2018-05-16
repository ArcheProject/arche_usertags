from BTrees.OOBTree import OOBTree
from BTrees.OOBTree import OOSet
from arche.events import ObjectUpdatedEvent
from arche.security import PERM_VIEW
from pyramid.security import Authenticated
from zope.component.event import objectEventNotify
from zope.interface import implementer

from arche_usertags.interfaces import IUserTags


@implementer(IUserTags)
class UserTags(object):
    __doc__ = IUserTags.__doc__
    name = '' #Name of the adapter and the tag
    catalog_index = None
    add_perm = Authenticated
    view_perm = PERM_VIEW
    # Alternative way to check permission
    add_perm_callback = None
    view_perm_callback = None

    def __init__(self, context):
        self.context = context
        try:
            self.storage = context.__tags_storage__
        except AttributeError:
            context.__tags_storage__ = OOBTree()
            self.storage = context.__tags_storage__
        self.data = self.storage.get(self.name, ())

    def add(self, userid, notify = True):
        if isinstance(self.data, tuple):
            self.data = self.storage[self.name] = OOSet()
        if userid not in self:
            self.data.add(userid)
            if self.catalog_index and notify:
                self._notify()

    def remove(self, userid, notify = True):
        if userid in self:
            self.data.remove(userid)
            if self.catalog_index and notify:
                self._notify()

    def add_url(self, request):
        return self.action_url(request, '+')

    def remove_url(self, request):
        return self.action_url(request, '-')

    def action_url(self, request, action):
        return request.route_url('usertags_view', tag=self.name, action=action, uid=self.context.uid)

    def add_allowed(self, request):
        if self.add_perm_callback is not None:
            return self.add_perm_callback(request)
        if self.add_perm:
            return request.has_permission(self.add_perm, self.context)
        return True

    def view_allowed(self, request):
        if self.view_perm_callback is not None:
            return self.view_perm_callback(request)
        if self.view_perm:
            return request.has_permission(self.view_perm, self.context)
        return True

    def _notify(self):
        event = ObjectUpdatedEvent(self.context, changed = (self.catalog_index,))
        objectEventNotify(event)

    def __nonzero__(self):
        return True

    def __iter__(self):
        return iter(self.data)

    def __contains__(self, value):
        return value in self.data

    def __len__(self):
        return len(self.data)
