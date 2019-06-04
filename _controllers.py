"""PytSite Object Document Mapper UI Plugin Controllers
"""
__author__ = 'Oleksandr Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from pytsite import tpl, router, routing, errors, metatag
from plugins import admin
from . import _api


class Browse(routing.Controller):
    """Entities Browser
    """

    def exec(self) -> str:
        # Get browser
        browser = _api.get_browser(self.arg('model'))

        # Set page title
        metatag.t_set('title', browser.title)

        # Render admin template
        if self.arg('_pytsite_router_rule_name') == 'odm_ui@admin_browse':
            return admin.render(tpl.render('odm_ui@browse', {'browser': browser}))

        # Render user template
        elif self.arg('_pytsite_router_rule_name') == 'odm_ui@browse':
            try:
                # Call a controller provided by application
                self.args['browser'] = browser
                return router.call('odm_ui_browse', self.args)

            except routing.error.RuleNotFound:
                # Render a template provided by application
                return tpl.render('odm_ui/browse', {'browser': browser})

        # Unknown rule
        else:
            raise self.not_found()


class Form(routing.Controller):
    """Entity Form
    """

    def exec(self) -> str:
        rule_name = self.arg('_pytsite_router_rule_name')  # type: str
        model = self.arg('model')

        # Get form
        if rule_name.endswith('m_form'):
            try:
                eid = self.arg('eid')
                form = _api.get_m_form(model, eid if eid != '0' else None, hide_title=True)
                metatag.t_set('title', form.title)
            except errors.NotFound as e:
                raise self.not_found(e)
        elif rule_name.endswith('d_form'):
            eids = self.arg('ids', []) or self.arg('eids', [])
            form = _api.get_d_form(model, eids, hide_title=True)
        else:
            raise self.not_found()

        metatag.t_set('title', form.title)

        # Render admin template
        if 'admin' in rule_name:
            return admin.render(tpl.render('odm_ui@form', {'form': form}))

        # Render user template
        else:
            try:
                # Call a controller provided by application
                self.args['form'] = form
                return router.call('odm_ui_form', self.args)

            except routing.error.RuleNotFound:
                # Render a template provided by application
                return tpl.render('odm_ui/form', {'form': form})
