"""PytSite Object Document Mapper UI Plugin HTTP API Controllers
"""
__author__ = 'Oleksandr Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from typing import Union as _Union, Iterable as _Iterable
from pyuca import Collator as _Collator
from pytsite import routing as _routing, formatters as _formatters, validation as _validation
from plugins import odm as _odm, http_api as _http_api
from . import _browser, _model

_pyuca_col = _Collator()


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


class GetWidgetEntitySelect(_routing.Controller):
    def __init__(self):
        super().__init__()

        self.args.add_formatter('model', _formatters.Str(max_len=32))
        self.args.add_formatter('sort_by', _formatters.Str(max_len=32))
        self.args.add_formatter('limit', _formatters.PositiveInt(10, 100))
        self.args.add_formatter('entity_title_args', _formatters.JSONObjectToDict())
        self.args.add_formatter('exclude', _formatters.JSONArrayToList())
        self.args.add_formatter('depth_indent', _formatters.Str('-'))

        self.args.add_formatter('sort_order', _formatters.Str(lower=True))
        self.args.add_formatter('sort_order', _formatters.Transform(1, {'asc': 1, 'desc': -1}))
        self.args.add_formatter('sort_order', _formatters.Int(1, -1, 1))
        self.args.add_formatter('sort_order', _formatters.Enum(1, (-1, 1)))

    @staticmethod
    def _build_finder(model: str, args: dict) -> _odm.Finder:
        cls = _odm.get_model_class(model)  # type: _model.UIEntity

        f = _odm.find(model)

        exclude = args.get('exclude')
        if exclude:
            f.ninc('_ref', exclude)

        sort_by = args.get('sort_by')
        if sort_by and f.mock.has_field(sort_by):
            f.sort([(sort_by, args.get('sort_order', _odm.I_ASC))])

        cls.odm_ui_widget_select_search_entities(f, args)

        return f

    def _build_entities_flat_tree(self, model: str, limit: int, args: dict) -> _Iterable[_model.UIEntity]:
        r = []

        for entity in self._build_finder(model, args).get(limit):
            # Append entity itself
            if entity not in r:
                r.append(entity)

            # Insert entity's parents
            cur_entity = entity
            while cur_entity.parent and cur_entity.parent not in r:
                r.insert(r.index(cur_entity), cur_entity.parent)
                cur_entity = cur_entity.parent

        return r

    def exec(self) -> dict:
        model = self.arg('model')
        sort_by = self.args.get('sort_by')
        sort_order = self.args.get('sort_order')
        limit = self.args.get('limit', 10)

        cls = _odm.get_model_class(model)
        if not issubclass(cls, _model.UIEntity):
            raise self.not_found()

        # Get entities tree
        entities = self._build_entities_flat_tree(model, limit, self.args)

        # Do additional sorting, because MongoDB does not sort all languages properly
        if sort_by and isinstance(_odm.dispense(model).get_field(sort_by), _odm.field.String):
            entities = sorted(entities, key=lambda e: _pyuca_col.sort_key(e.f_get(sort_by)),
                              reverse=sort_order == _odm.I_DESC)

        # Build final value to return
        items = []
        for entity in entities:
            # Title
            title = entity.odm_ui_widget_select_search_entities_title(self.args)
            if entity.depth:
                title = '{} {}'.format(self.arg('depth_indent') * entity.depth, title)

            items.append({'id': entity.ref, 'text': title})

        return {'results': items}
