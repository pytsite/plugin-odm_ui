"""PytSite Object Document Mapper UI Plugin HTTP API Controllers
"""
__author__ = 'Oleksandr Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from typing import Union as _Union
from pytsite import routing as _routing, formatters as _formatters, validation as _validation
from plugins import odm as _odm, http_api as _http_api
from . import _browser


class GetBrowseRows(_routing.Controller):
    """Get browser rows
    """

    def __init__(self):
        super().__init__()

        self.args.add_formatter('offset', _formatters.PositiveInt())
        self.args.add_formatter('limit', _formatters.PositiveInt())
        self.args.add_validation('order', _validation.rule.Enum(values=['asc', 'desc']))

    def exec(self) -> _Union:
        model = self.arg('model')
        offset = self.arg('offset', 0)
        limit = self.arg('limit', 0)

        browser = _browser.Browser(
            model=model,
            browse_rule=self.arg('browse_rule'),
            m_form_rule=self.arg('m_form_rule'),
            d_form_rule=self.arg('d_form_rule'),
        )

        r = browser.get_rows(offset, limit, self.arg('sort'), self.arg('order', 'asc'), self.arg('search'))

        if r['total'] and not r['rows']:
            offset -= limit
            if offset < 0:
                offset = 0

            r_args = self.request.inp
            r_args['model'] = model
            r_args['offset'] = offset

            return self.redirect(_http_api.url('odm_ui@browse_rows', r_args))

        return r


class GetWidgetEntitySelectSearch(_routing.Controller):
    def exec(self) -> dict:
        # Check if the model's class supports this operation
        cls = _odm.get_model_class(self.arg('model'))
        if not hasattr(cls, 'odm_ui_widget_select_search_entities'):
            raise self.not_found()

        return {'results': cls.odm_ui_widget_select_search_entities(self.args)}
