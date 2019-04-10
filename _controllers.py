"""PytSite Object Document Mapper UI Plugin Controllers
"""
__author__ = 'Oleksandr Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from pytsite import tpl as _tpl, router as _router, routing as _routing, errors as _errors, metatag as _metatag
from plugins import admin as _admin
from . import _api


class Browse(_routing.Controller):
    """Entities Browser
    """

    def exec(self) -> str:
        # Get browser
        browser = _api.get_browser(self.arg('model'))

        # Set page title
        _metatag.t_set('title', browser.title)

        # Render admin template
        if self.arg('_pytsite_router_rule_name') == 'odm_ui@admin_browse':
            return _admin.render(_tpl.render('odm_ui@browse', {'browser': browser}))

        # Render user template
        elif self.arg('_pytsite_router_rule_name') == 'odm_ui@browse':
            try:
                # Call a controller provided by application
                return _router.call('odm_ui_browse', {'browser': browser})

            except _routing.error.RuleNotFound:
                # Render a template provided by application
                return _tpl.render('odm_ui/browse', {'browser': browser})

        # Unknown rule
        else:
            raise self.not_found()


class Form(_routing.Controller):
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
                _metatag.t_set('title', form.title)
            except _errors.NotFound as e:
                raise self.not_found(e)
        elif rule_name.endswith('d_form'):
            eids = self.arg('ids', []) or self.arg('eids', [])
            form = _api.get_d_form(model, eids, hide_title=True)
        else:
            raise self.not_found()

        _metatag.t_set('title', form.title)

        # Render admin template
        if 'admin' in rule_name:
            return _admin.render(_tpl.render('odm_ui@form', {'form': form}))

        # Render user template
        else:
            try:
                # Call a controller provided by application
                return _router.call('odm_ui_form', {'form': form})

            except _routing.error.RuleNotFound:
                # Render a template provided by application
                return _tpl.render('odm_ui/form', {'form': form})
