"""PytSite Object Document Mapper UI Plugin
"""
__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from pytsite import plugman as _plugman

if _plugman.is_installed(__name__):
    # Public API
    from . import _widget as widget, _forms as forms, _model as model
    from ._browser import Browser
    from ._api import get_m_form, get_d_form, get_model_class


def plugin_load():
    from pytsite import tpl, lang, router
    from plugins import assetman, admin, http_api
    from . import _controllers, _http_api_controllers

    abp = admin.base_path()
    auth_filter = admin.AdminAccessFilterController

    # Route: ODM browser page
    router.handle(_controllers.Browse, abp + '/odm_ui/<model>', 'odm_ui@browse', filters=auth_filter)

    # Route: 'create/modify' ODM entity form display
    router.handle(_controllers.ModifyForm, abp + '/odm_ui/<model>/modify/<eid>', 'odm_ui@m_form', filters=auth_filter)

    # Route: 'delete' form display
    router.handle(_controllers.DeleteForm, abp + '/odm_ui/<model>/delete', 'odm_ui@d_form', methods=('GET', 'POST'),
                  filters=auth_filter)

    # Resources
    lang.register_package(__name__)
    tpl.register_package(__name__)

    assetman.register_package(__name__)
    assetman.t_js(__name__)

    # HTTP API handlers
    http_api.handle('GET', 'odm_ui/rows/<model>', _http_api_controllers.GetRows, 'odm_ui@get_rows')
