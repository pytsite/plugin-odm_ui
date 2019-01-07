"""PytSite Object Document Mapper UI Plugin Entities Browser
"""
__author__ = 'Oleksandr Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from typing import Callable as _Callable, Union as _Union
from pytsite import router as _router, metatag as _metatag, lang as _lang, html as _html, events as _events
from plugins import widget as _widget, auth as _auth, odm as _odm, permissions as _permissions, http_api as _http_api
from . import _api, _model


class Browser:
    """ODM Entities Browser
    """

    def __init__(self, model: str, **kwargs):
        """Init
        """
        if not model:
            raise RuntimeError('No model specified')

        # Model
        self._model = model

        # Model class
        self._model_class = _api.get_model_class(self._model)

        # Entity mock
        self._mock = _api.dispense_entity(self._model)

        self._current_user = _auth.get_current_user()
        self._finder_adjust = self._default_finder_adjust
        self._browse_rule = kwargs.get('browse_rule', self._model_class.odm_ui_browse_rule())
        self._m_form_rule = kwargs.get('m_form_rule', self._model_class.odm_ui_m_form_rule())
        self._d_form_rule = kwargs.get('d_form_rule', self._model_class.odm_ui_d_form_rule())

        # Widget
        widget_class = self._model_class.odm_ui_browser_widget_class()
        if not (issubclass(widget_class, _widget.misc.DataTable)):
            raise TypeError('Subclass of {} expected, got'.format(_widget.misc.DataTable, widget_class))
        self._widget = widget_class(
            uid='odm-ui-browser-' + model,
            rows_url=_http_api.url('odm_ui@get_browser_rows', {
                'model': self._model,
                'browse_rule': self._browse_rule,
                'm_form_rule': self._m_form_rule,
                'd_form_rule': self._d_form_rule,
            }),
            update_rows_url=_http_api.url('odm_ui@put_browser_rows')
        )

        # Call model's class to perform setup tasks
        self._model_class.odm_ui_browser_setup(self)

        # Notify external events listeners
        _events.fire('odm_ui@browser_setup.{}'.format(self._model), browser=self)

        # Check if the model specified data fields
        if not self.data_fields:
            raise RuntimeError('No data fields was defined')

        # Actions column
        if self._model_class.odm_ui_entity_actions_enabled() and \
                (self._model_class.odm_ui_modification_allowed() or self._model_class.odm_ui_deletion_allowed()):
            self.insert_data_field('entity-actions', 'odm_ui@actions', False)

        # Metatags
        _metatag.t_set('title', self._model_class.t('odm_ui_browser_title_' + self._model))

    @property
    def model(self) -> str:
        """Get browser entities model
        """
        return self._model

    @property
    def browse_rule(self) -> str:
        """Get browser browse rule name
        """
        return self._browse_rule

    @property
    def m_form_rule(self) -> str:
        """Get m_form rule name
        """
        return self._m_form_rule

    @property
    def d_form_rule(self) -> str:
        """Get d_form rule name
        """
        return self._d_form_rule

    @property
    def mock(self) -> _model.UIEntity:
        """Get entity mock
        """
        return self._mock

    @property
    def finder_adjust(self) -> _Callable:
        return self._finder_adjust

    @finder_adjust.setter
    def finder_adjust(self, func: _Callable):
        self._finder_adjust = func

    @property
    def data_fields(self) -> _Union[list, tuple]:
        return self._widget.data_fields

    @data_fields.setter
    def data_fields(self, value: _Union[list, tuple]):
        self._widget.data_fields = value

    @property
    def default_sort_field(self) -> str:
        return self._widget.default_sort_field

    @default_sort_field.setter
    def default_sort_field(self, value: str):
        self._widget.default_sort_field = value

    @property
    def default_sort_order(self) -> str:
        return _odm.I_DESC if self._widget.default_sort_order == 'desc' else _odm.I_ASC

    @default_sort_order.setter
    def default_sort_order(self, value: _Union[int, str]):
        if isinstance(value, int):
            value = 'desc' if value == _odm.I_DESC else 'asc'

        self._widget.default_sort_order = value

    def insert_data_field(self, name: str, title: str = None, sortable: bool = True, pos: int = None):
        self._widget.insert_data_field(name, title, sortable, pos)

    def remove_data_field(self, name: str):
        self._widget.remove_data_field(name)

    def _default_finder_adjust(self, finder: _odm.Finder):
        pass

    def get_rows(self, offset: int = 0, limit: int = 0, sort_field: str = None, sort_order: _Union[int, str] = None,
                 search: str = None) -> dict:
        """Get browser rows.
        """
        r = {'total': 0, 'rows': []}

        # Sort order
        if sort_order is None:
            sort_order = self.default_sort_order

        # Setup finder
        finder = _odm.find(self._model)
        self._finder_adjust(finder)

        # Admins and developers has full access
        show_all = self._current_user.is_admin

        # Check if the current user is not admin, but have permission-based full access
        if not show_all:
            for perm_prefix in ('odm_auth@modify.', 'odm_auth@delete.'):
                perm_name = perm_prefix + self._model
                if _permissions.is_permission_defined(perm_name) and self._current_user.has_permission(perm_name):
                    show_all = True
                    break

        # Check if the current user does not have full access, but have access to its own entities
        if not show_all and (finder.mock.has_field('author') or finder.mock.has_field('owner')):
            for perm_prefix in ('odm_auth@modify_own.', 'odm_auth@delete_own.'):
                perm_name = perm_prefix + self._model
                if _permissions.is_permission_defined(perm_name) and self._current_user.has_permission(perm_name):
                    if finder.mock.has_field('author'):
                        finder.eq('author', self._current_user.uid)
                    elif finder.mock.has_field('owner'):
                        finder.eq('owner', self._current_user.uid)

        # Search
        if search:
            self._model_class.odm_ui_browser_search(finder, search)

        # Counting total
        r['total'] = finder.count()

        # Sort
        sort_order = _odm.I_DESC if sort_order in (-1, 'desc') else _odm.I_ASC
        if sort_field and finder.mock.has_field(sort_field):
            finder.sort([(sort_field, sort_order)])
        elif self.default_sort_field:
            finder.sort([(self.default_sort_field, sort_order)])

        # Get root elements first
        finder.add_sort('_parent', pos=0)

        # Iterate over result and get content for table rows
        cursor = finder.skip(offset).get(limit)
        for entity in cursor:
            row = entity.odm_ui_browser_row()
            _events.fire('odm_ui@browser_row.{}'.format(self._model), entity=entity, row=row)

            if not row:
                continue

            # Build row's cells
            fields_data = {
                '__id': entity.ref,
                '__parent': entity.parent.ref if entity.parent else None,
            }
            if isinstance(row, (list, tuple)):
                expected_row_length = len(self.data_fields)
                if self._model_class.odm_ui_entity_actions_enabled():
                    expected_row_length -= 1
                row_length = len(row)
                if row_length != expected_row_length:
                    raise ValueError('{}.odm_ui_browser_row() returns invalid number of cells: expected {}, got {}'.
                                     format(entity.__class__.__name__, expected_row_length, row_length))
                for f_name, cell_content in zip([df[0] for df in self.data_fields], row):
                    fields_data[f_name] = cell_content
            elif isinstance(row, dict):
                for df in self.data_fields:
                    fields_data[df[0]] = row.get(df[0], '&nbsp;')
            else:
                raise TypeError('{}.odm_ui_browser_row() must return list, tuple or dict, got {}'.
                                format(entity.__class__.__name__, type(row)))

            # Action buttons
            if self._model_class.odm_ui_entity_actions_enabled() and \
                    (self._model_class.odm_ui_modification_allowed() or self._model_class.odm_ui_deletion_allowed()):

                actions = _html.TagLessElement(child_sep='&nbsp;')
                for btn_data in entity.odm_ui_browser_entity_actions(self):
                    color = 'btn btn-sm btn-' + btn_data.get('color', 'default btn-light')
                    title = btn_data.get('title', '')
                    url = btn_data.get('url')
                    if not url:
                        rule = btn_data.get('rule')
                        url = _router.rule_url(rule, {'ids': str(entity.id)}) if rule else '#'
                    btn = _html.A(href=url, css=color + ' ' + btn_data.get('css', ''), title=title, role='button')
                    if btn_data.get('disabled'):
                        btn.set_attr('aria_disabled', 'true')
                        btn.add_css('disabled')
                    btn.append(_html.I(css=btn_data.get('icon', 'fa fas fa-fw fa-question')))
                    actions.append(btn)

                if not len(actions.children):
                    actions.set_attr('css', actions.get_attr('css') + ' empty')

                fields_data['entity-actions'] = actions.render()

            r['rows'].append(fields_data)

        return r

    def render(self) -> str:
        # 'Create' toolbar button
        if self._mock.odm_ui_creation_allowed() and self._mock.odm_auth_check_entity_permissions('create'):
            create_form_url = _router.rule_url(self._m_form_rule, {
                'model': self._model,
                'eid': 0,
                '__redirect': _router.current_url(),
            })
            title = _lang.t('odm_ui@create')
            btn = _html.A(href=create_form_url, css='btn btn-default btn-light add-button', title=title)
            btn.append(_html.I(css='fa fas fa-fw fa-plus'))
            self._widget.toolbar.append(btn)
            self._widget.toolbar.append(_html.Span('&nbsp;'))

        # 'Delete' toolbar button
        if self._mock.odm_ui_deletion_allowed():
            delete_form_url = _router.rule_url(self._d_form_rule, {'model': self._model})
            title = _lang.t('odm_ui@delete_selected')
            btn = _html.A(href=delete_form_url, css='hidden btn btn-danger mass-action-button sr-only', title=title)
            btn.append(_html.I(css='fa fas fa-fw fa-remove fa-times'))
            self._widget.toolbar.append(btn)
            self._widget.toolbar.append(_html.Span('&nbsp;'))

        # Additional toolbar buttons
        for btn_data in self._model_class.odm_ui_browser_mass_action_buttons():
            ep = btn_data.get('ep')
            url = _router.rule_url(ep) if ep else '#'
            css = 'btn btn-{} mass-action-button'.format(btn_data.get('color', 'default btn-light'))
            icon = 'fa fas fa-fw fa-' + btn_data.get('icon', 'question')
            button = _html.A(href=url, css=css, title=btn_data.get('title'))
            if icon:
                button.append(_html.I(css=icon))
            self._widget.toolbar.append(button)
            self._widget.toolbar.append(_html.Span('&nbsp;'))

        frm = _html.Form(self._widget.render(), action='#', method='post', css='table-responsive odm-ui-browser')

        return frm.render()

    def __str__(self) -> str:
        return self.render()
