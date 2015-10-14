from BTrees.OOBTree import OOBTree
from BTrees.OOBTree import OOSet
from arche.events import ObjectUpdatedEvent
from arche.security import PERM_VIEW
from zope.component.event import objectEventNotify
from zope.interface import implementer

from arche_usertags.interfaces import IUserTags


@implementer(IUserTags)
class UserTags(object):
    __doc__ = IUserTags.__doc__
    name = '' #Name of the adapter and the tag
    view_name = '__usertags__'
    catalog_index = None
    add_perm = PERM_VIEW
    
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
        return request.resource_url(self.context, self.view_name, self.name, action)

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
