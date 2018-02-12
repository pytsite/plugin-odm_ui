"""PytSite Object Document Mapper UI Plugin Controllers
"""

__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from pytsite import tpl as _tpl, router as _router, routing as _routing
from plugins import odm as _odm, admin as _admin
from . import _api, _browser


class Browse(_routing.Controller):
    def exec(self) -> str:
        return _admin.render(_tpl.render('odm_ui@browser', {
            'table': _browser.Browser(self.arg('model')).render()
        }))


class ModifyForm(_routing.Controller):
    def exec(self) -> str:
        """Get entity create/modify form.
        """
        model = self.arg('model')
        eid = self.arg('eid')
        try:
            form = _api.get_m_form(model, eid if eid != '0' else None, hide_title=True)
            form = _tpl.render('odm_ui@form', {'form': form})
            return _admin.render(form)
        except _odm.error.EntityNotFound:
            raise self.not_found()


class DeleteForm(_routing.Controller):
    def exec(self) -> str:
        model = self.arg('model')

        # Entities IDs to delete
        ids = _router.request().inp.get('ids', [])
        if isinstance(ids, str):
            ids = [ids]

        # No required arguments has been received
        if not model or not ids:
            raise self.not_found()

        return _admin.render(_tpl.render('odm_ui@form', {'form': _api.get_d_form(model, ids)}))
