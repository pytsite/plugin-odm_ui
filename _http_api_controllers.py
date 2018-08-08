"""PytSite Object Document Mapper UI Plugin HTTP API Controllers
"""
__author__ = 'Oleksandr Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from pytsite import routing as _routing, formatters as _formatters, validation as _validation
from plugins import odm as _odm
from . import _browser


class GetAdminBrowseRows(_routing.Controller):
    """Get browser rows
    """

    def __init__(self):
        super().__init__()

        self.args.add_formatter('offset', _formatters.PositiveInt())
        self.args.add_formatter('limit', _formatters.PositiveInt())
        self.args.add_validation('order', _validation.rule.Enum(values=['asc', 'desc']))

    def exec(self) -> dict:
        return _browser.Browser(self.arg('model')).get_rows(
            self.arg('offset', 0),
            self.arg('limit', 0),
            self.arg('sort'),
            self.arg('order', 'asc'),
            self.arg('search')
        )


class GetWidgetEntitySelectSearch(_routing.Controller):
    def exec(self) -> dict:
        # Check if the model's class supports this operation
        cls = _odm.get_model_class(self.arg('model'))
        if not hasattr(cls, 'odm_ui_widget_select_search_entities'):
            raise self.not_found()

        return {'results': cls.odm_ui_widget_select_search_entities(self.args)}
