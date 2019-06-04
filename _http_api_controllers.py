"""PytSite Object Document Mapper UI Plugin HTTP API Controllers
"""
__author__ = 'Oleksandr Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from typing import Union, Iterable
from pyuca import Collator
from pytsite import routing, formatters, validation
from plugins import odm, http_api
from . import _browser, _model

_pyuca_col = Collator()


class GetBrowserRows(routing.Controller):
    """Get browser rows
    """

    def __init__(self):
        super().__init__()

        self.args.add_formatter('offset', formatters.PositiveInt())
        self.args.add_formatter('limit', formatters.PositiveInt())
        self.args.add_formatter('search', formatters.Str(max_len=64))
        self.args.add_validation('order', validation.rule.Enum(values=['asc', 'desc']))

    def exec(self) -> Union:
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

            return self.redirect(http_api.url('odm_ui@get_browser_rows', r_args))

        return r


class PutBrowserRows(routing.Controller):
    def __init__(self):
        super().__init__()

        self.args.add_formatter('rows', formatters.JSONArray())

    def exec(self):
        model = self.arg('model')

        for row in self.arg('rows'):
            e = odm.dispense(model, row['__id'])
            e.f_set_multiple({
                '_parent': odm.dispense(model, row['__parent']) if row['__parent'] else None,
                'order': row['order'],
            })
            e.save()

        return {'status': True}


class GetWidgetEntitySelect(routing.Controller):
    def __init__(self):
        super().__init__()

        self.args.add_formatter('model', formatters.JSONArray())
        self.args.add_formatter('sort_by', formatters.Str(max_len=32))
        self.args.add_formatter('limit', formatters.PositiveInt(10, 100))
        self.args.add_formatter('entity_title_args', formatters.JSONObject())
        self.args.add_formatter('exclude', formatters.JSONArray())
        self.args.add_formatter('depth_indent', formatters.Str('-'))

        self.args.add_formatter('sort_order', formatters.Str(lower=True))
        self.args.add_formatter('sort_order', formatters.Transform(1, {'asc': 1, 'desc': -1}))
        self.args.add_formatter('sort_order', formatters.Int(1, -1, 1))
        self.args.add_formatter('sort_order', formatters.Enum(1, (-1, 1)))

    @staticmethod
    def _find_entities(args: dict) -> Iterable[_model.UIEntity]:
        models = args['model']
        sort_by = args['sort_by']
        sort_order = args['sort_order']
        f = odm.mfind(models)

        if sort_by:
            f.sort([(sort_by, sort_order)])

        exclude = args.get('exclude')
        if exclude:
            f.ninc('_ref', exclude)

        # Let model's class adjust finder
        for model in models:
            mock = odm.dispense(model)  # type: _model.UIEntity
            mock.odm_ui_widget_select_search_entities(f, args)

        # Collect entities
        entities = []
        for entity in f.get():  # type:  _model.UIEntity
            if entity.odm_ui_widget_select_search_entities_is_visible(args):
                entities.append(entity)
            if len(entities) - 1 == args['limit']:
                break

        # Do additional sorting, because MongoDB does not sort all languages properly
        if entities and sort_by and isinstance(entities[0].get_field(sort_by), odm.field.String):
            entities = sorted(entities, key=lambda e: _pyuca_col.sort_key(e.f_get(sort_by)),
                              reverse=sort_order == odm.I_DESC)

        return entities

    def _build_entities_flat_tree(self, args: dict) -> Iterable[_model.UIEntity]:
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
