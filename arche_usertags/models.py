from UserDict import IterableUserDict

from BTrees.OOBTree import OOBTree
from BTrees.OOBTree import OOSet
from arche.events import ObjectUpdatedEvent
from arche.security import PERM_VIEW
from zope.component.event import objectEventNotify
from zope.interface import implementer

from arche_usertags.interfaces import IUserTags


@implementer(IUserTags)
class UserTags(IterableUserDict):
    __doc__ = IUserTags.__doc__
    name = '' #Name of the adapter and the tag
    view_name = '__usertags__'
    catalog_index = None
    add_perm = PERM_VIEW
    
    def __init__(self, context):
        self.context = context
        try:
            self.data = self.context.__tags_storage__
        except AttributeError:
            self.context.__tags_storage__ = OOBTree()
            self.data = self.context.__tags_storage__

    def add(self, userid, notify = True):
        storage = self.setdefault(self.name, OOSet())
        if userid not in storage:
            storage.add(userid)
            if self.catalog_index and notify:
                self._notify()

    def remove(self, userid, notify = True):
        if userid in self.get(self.name, ()):
            self[self.name].remove(userid)
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

    def __setitem__(self, key, item):
        self.data[key] = OOSet(item)

    def __nonzero__(self):
        return True
