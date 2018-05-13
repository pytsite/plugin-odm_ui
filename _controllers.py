"""PytSite Object Document Mapper UI Plugin Controllers
"""
__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from pytsite import tpl as _tpl, router as _router, routing as _routing, metatag as _metatag
from plugins import odm as _odm, admin as _admin
from . import _api


class Browse(_routing.Controller):
    """Entities browser
    """
    def exec(self) -> str:
        return _admin.render(_tpl.render('odm_ui@browse', {
            'browser': _api.get_browser(self.arg('model'))
        }))


class ModifyForm(_routing.Controller):
    def exec(self) -> str:
        """Get entity create/modify form.
        """
        try:
            eid = self.arg('eid')
            form = _api.get_m_form(self.arg('model'), eid if eid != '0' else None, hide_title=True)
            _metatag.t_set('title', form.title)
            return _admin.render(_tpl.render('odm_ui@form', {'form': form}))

        except _odm.error.EntityNotFound:
            raise self.not_found()


class DeleteForm(_routing.Controller):
    def exec(self) -> str:
        model = self.arg('model')
        eids = self.arg('eids', self.arg('ids', []))

        # No required arguments has been received
        if not model or not eids:
            raise self.not_found()

        redirect = _router.rule_url('odm_ui@admin_browse', {'model': self.arg('model')})
        form = _api.get_d_form(model, eids, redirect=redirect, hide_title=True)
        _metatag.t_set('title', form.title)

        return _admin.render(_tpl.render('odm_ui@form', {'form': form}))
