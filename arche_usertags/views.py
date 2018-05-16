from arche.security import PERM_VIEW
from arche.views.base import BaseView
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPNotFound
from zope.interface.interfaces import ComponentLookupError

from arche_usertags.interfaces import IUserTags


class UserTagsView(BaseView):
    actions = {'+': 'add',
               '-': 'remove',
               'list': 'list'}

    @reify
    def adapter(self):
        tag = self.request.matchdict.get('tag', None)
        try:
            return self.request.registry.getAdapter(self.tag_context, IUserTags, name = tag)
        except ComponentLookupError:
            if not self.tag_context:
                raise HTTPNotFound("No object with that UID")
            raise HTTPNotFound("No such tag")

    @reify
    def tag_context(self):
        uid = self.request.matchdict.get('uid', None)
        #Check perm later instead - makes debugging easier
        return self.resolve_uid(uid, perm = None)

    def __call__(self):
        action_callable = self.get_action()
        return action_callable()

    def get_action(self):
        action = self.request.matchdict.get('action', None)
        try:
            action_name = self.actions[action]
        except KeyError:
            raise HTTPNotFound("No such action")
        if self.request.authenticated_userid is None:
            raise HTTPForbidden("Must be authenticated")
        return getattr(self, action_name)

    def add(self):
        if not self.adapter.add_allowed(self.request):
            raise HTTPForbidden("Not allowed")
        self.adapter.add(self.request.authenticated_userid)
        return self._return_success()

    def remove(self):
        if not self.adapter.add_allowed(self.request):
            raise HTTPForbidden("Not allowed")
        self.adapter.remove(self.request.authenticated_userid)
        return self._return_success()

    def list(self):
        if not self.adapter.view_allowed(self.request):
            raise HTTPForbidden("Not allowed")
        return {'items': tuple(self.adapter)}

    def _return_success(self):
        if self.request.is_xhr:
            user_in = self.request.authenticated_userid in self.adapter
            return {'status': 'success',
                    'user_in': user_in,
                    'total': len(self.adapter),
                    'toggle_url': user_in and self.adapter.remove_url(self.request) or self.adapter.add_url(self.request)}
        return HTTPFound(location = self.request.resource_url(self.context))


def includeme(config):
    config.add_route('usertags_view', '/autags/{tag}/{action}/{uid}')
    config.add_view(UserTagsView,
                    route_name='usertags_view',
                    renderer = 'json',
                    permission = PERM_VIEW)
