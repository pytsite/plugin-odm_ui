"""PytSite Object Document Mapper UI Plugin
"""
__author__ = 'Oleksandr Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

# Public API
from . import _widget as widget, _forms as forms, _model as model
from ._api import get_browser, get_m_form, get_d_form, get_model_class, dispense_entity
from ._browser import Browser
from ._model import UIEntity


def plugin_load_wsgi():
    from pytsite import router
    from plugins import admin, http_api, auth_ui
    from . import _controllers, _http_api_controllers

    abp = admin.base_path()

    # Route: ODM browser page
    router.handle(_controllers.Browse, abp + '/odm_ui/<model>', 'odm_ui@admin_browse', filters=auth_ui.AuthFilter)

    # Route: 'create/modify' ODM entity form display
    router.handle(_controllers.ModifyForm, abp + '/odm_ui/<model>/modify/<eid>', 'odm_ui@admin_m_form',
                  filters=auth_ui.AuthFilter)

    # Route: 'delete' form display
    router.handle(_controllers.DeleteForm, abp + '/odm_ui/<model>/delete', 'odm_ui@admin_d_form',
                  methods=('GET', 'POST'), filters=auth_ui.AuthFilter)

    # HTTP API handlers
    http_api.handle('GET', 'odm_ui/browse/rows/<model>', _http_api_controllers.GetBrowseRows, 'odm_ui@browse_rows')
    http_api.handle('GET', 'odm_ui/widget/entity_select_search/<model>',
                    _http_api_controllers.GetWidgetEntitySelectSearch, 'odm_ui@widget_entity_select_search')
