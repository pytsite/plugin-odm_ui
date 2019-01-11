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


class GetBrowserRows(_routing.Controller):
    """Get browser rows
    """

    def __init__(self):
        super().__init__()

        self.args.add_formatter('offset', _formatters.PositiveInt())
        self.args.add_formatter('limit', _formatters.PositiveInt())
        self.args.add_formatter('search', _formatters.Str(max_len=64))
        self.args.add_validation('order', _validation.rule.Enum(values=['asc', 'desc']))

    def exec(self) -> _Union:
        browser = _browser.Browser(
            model=self.arg('model'),
            browse_rule=self.arg('browse_rule'),
            m_form_rule=self.arg('m_form_rule'),
            d_form_rule=self.arg('d_form_rule'),
        )

        r = browser.get_rows(self.args)

        if r['total'] and not r['rows']:
            offset = self.arg('offset') - self.arg('limit')
            if offset < 0:
                offset = 0

            r_args = self.request.inp
            r_args['model'] = browser.model
            r_args['offset'] = offset

            return self.redirect(_http_api.url('odm_ui@get_browser_rows', r_args))

        return r


class PutBrowserRows(_routing.Controller):
    def __init__(self):
        super().__init__()

        self.args.add_formatter('rows', _formatters.JSONArray())

    def exec(self):
        model = self.arg('model')

        for row in self.arg('rows'):
            e = _odm.dispense(model, row['__id'])
            e.f_set_multiple({
                '_parent': _odm.dispense(model, row['__parent']) if row['__parent'] else None,
                'order': row['order'],
            })
            e.save()

        return {'status': True}


class GetWidgetEntitySelect(_routing.Controller):
    def __init__(self):
        super().__init__()

        self.args.add_formatter('model', _formatters.JSONArray())
        self.args.add_formatter('sort_by', _formatters.Str(max_len=32))
        self.args.add_formatter('limit', _formatters.PositiveInt(10, 100))
        self.args.add_formatter('entity_title_args', _formatters.JSONObject())
        self.args.add_formatter('exclude', _formatters.JSONArray())
        self.args.add_formatter('depth_indent', _formatters.Str('-'))

        self.args.add_formatter('sort_order', _formatters.Str(lower=True))
        self.args.add_formatter('sort_order', _formatters.Transform(1, {'asc': 1, 'desc': -1}))
        self.args.add_formatter('sort_order', _formatters.Int(1, -1, 1))
        self.args.add_formatter('sort_order', _formatters.Enum(1, (-1, 1)))

    @staticmethod
    def _find_entities(args: dict) -> _Iterable[_model.UIEntity]:
        models = args['model']
        sort_by = args['sort_by']
        sort_order = args['sort_order']
        f = _odm.mfind(models)

        if sort_by:
            f.sort([(sort_by, sort_order)])

        exclude = args.get('exclude')
        if exclude:
            f.ninc('_ref', exclude)

        # Let model's class adjust finder
        for model in models:
            mock = _odm.dispense(model)  # type: _model.UIEntity
            mock.odm_ui_widget_select_search_entities(f, args)

        # Collect entities
        entities = []
        for e in f.get():  # type:  _model.UIEntity
            if e.odm_ui_widget_select_search_entities_is_visible(args):
                entities.append(e)
            if len(entities) - 1 == args['limit']:
                break

        # Do additional sorting, because MongoDB does not sort all languages properly
        if entities and sort_by and isinstance(entities[0].get_field(sort_by), _odm.field.String):
            entities = sorted(entities, key=lambda e: _pyuca_col.sort_key(e.f_get(sort_by)),
                              reverse=sort_order == _odm.I_DESC)

        return entities

    def _build_entities_flat_tree(self, args: dict) -> _Iterable[_model.UIEntity]:
        r = []

        for entity in self._find_entities(args):
            if entity not in r:
                # If parent of current entity is already appended
                if entity.parent and entity.parent in r:
                    # Skip all children after that parent
                    i = r.index(entity.parent) + 1
                    while i < len(r) and r[i].parent == entity.parent:
                        i += 1

                    r.insert(i, entity)
                else:
                    r.append(entity)

            # Insert entity's parents
            cur_entity = entity
            while cur_entity.parent and cur_entity.parent not in r:
                r.insert(r.index(cur_entity), cur_entity.parent)
                cur_entity = cur_entity.parent

        return r

    def exec(self) -> dict:
        items = []
        for entity in self._build_entities_flat_tree(self.args):
            # Title
            title = entity.odm_ui_widget_select_search_entities_title(self.args)
            if entity.depth:
                title = '{} {}'.format(self.arg('depth_indent') * entity.depth, title)

            items.append({'id': entity.ref, 'text': title})

        return {'results': items}
