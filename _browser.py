"""PytSite Object Document Mapper UI Plugin Entities Browser
"""
__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from typing import Callable as _Callable, Union as _Union
from pytsite import router as _router, metatag as _metatag, lang as _lang, html as _html, http as _http, \
    events as _events
from plugins import widget as _widget, auth as _auth, odm as _odm, permissions as _permissions, http_api as _http_api, \
    assetman as _assetman
from . import _api, _model


class Browser:
    """ODM Entities Browser
    """

    def __init__(self, model: str):
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

        # Widget
        widget_class = self._model_class.odm_ui_browser_widget_class()
        if not (issubclass(widget_class, _widget.misc.DataTable)):
            raise TypeError('Subclass of {} expected, got'.format(_widget.misc.DataTable, widget_class))
        self._widget = widget_class(
            uid='odm-ui-browser-' + model,
            data_url=_http_api.url('odm_ui@get_rows', {'model': self._model}),
        )

        # Check permissions
        if not self._mock.odm_auth_check_permission('view'):
            raise _http.error.Forbidden()

        self._current_user = _auth.get_current_user()
        self._finder_adjust = self._default_finder_adjust

        # Call model's class to perform setup tasks
        self._model_class.odm_ui_browser_setup(self)

        # Notify external events listeners
        _events.fire('odm_ui@browser_setup.{}'.format(self._model), browser=self)

        # Check if the model specified data fields
        if not self.data_fields:
            raise RuntimeError('No data fields was defined')

        # Actions column
        if self._model_class.odm_ui_entity_actions_enabled():
            self.insert_data_field('_actions', 'odm_ui@actions', False)

        _assetman.preload('odm_ui@css/odm-ui-browser.css')

    @property
    def model(self) -> str:
        """Get browser entities model
        """
        return self._model

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
    def default_sort_field(self) -> int:
        return _odm.I_DESC if self._widget.default_sort_field == 'desc' else _odm.I_ASC

    @default_sort_field.setter
    def default_sort_field(self, value: _Union[int, str]):
        if isinstance(value, int):
            value = 'desc' if value == _odm.I_DESC else 'asc'

        self._widget.default_sort_field = value

    @property
    def default_sort_order(self) -> str:
        return self._widget.default_sort_order

    @default_sort_order.setter
    def default_sort_order(self, value: str):
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
        show_all = self._current_user.has_role(['admin', 'dev'])

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
                '__id': str(entity.id),
                '__parent': str(entity.parent.id) if entity.parent else None,
            }

            if isinstance(row, (list, tuple)):
                expected_row_length = len(self.data_fields)
                if self._model_class.odm_ui_entity_actions_enabled():
                    expected_row_length -= 1
                if len(row) != expected_row_length:
                    raise ValueError(
                        '{}.odm_ui_browser_row() returns invalid number of cells'.format(entity.__class__.__name__)
                    )
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
                actions = self._get_entity_action_buttons(entity)
                for btn_data in entity.odm_ui_browser_entity_actions():
                    color = 'btn btn-xs btn-' + btn_data.get('color', 'default')
                    title = btn_data.get('title', '')
                    ep = btn_data.get('ep')
                    url = _router.rule_url(ep, {'ids': str(entity.id)}) if ep else '#'
                    css = btn_data.get('css', '')
                    btn = _html.A(href=url, css=color + css, title=title)
                    btn.append(_html.I(css='fa fa-fw fa-' + btn_data.get('icon', 'question')))
                    actions.append(btn)
                    actions.append(_html.TagLessElement('&nbsp;'))

                if not len(actions.children):
                    actions.set_attr('css', actions.get_attr('css') + ' empty')

                fields_data['_actions'] = actions.render()

            r['rows'].append(fields_data)

        return r

    @staticmethod
    def _get_entity_action_buttons(entity: _model.UIEntity) -> _html.Div:
        """Get action buttons for entity.
        """
        group = _html.Div(css='entity-actions', data_entity_id=str(entity.id))

        if entity.odm_ui_modification_allowed() and \
                (entity.odm_auth_check_permission('modify') or entity.odm_auth_check_permission('modify_own')):
            m_form_url = _router.rule_url('odm_ui@m_form', {
                'model': entity.model,
                'eid': str(entity.id),
                '__redirect': _router.rule_url('odm_ui@browse', {'model': entity.model}),
            })
            title = _lang.t('odm_ui@modify')
            a = _html.A(css='btn btn-xs btn-default', href=m_form_url, title=title)
            a.append(_html.I(css='fa fa-edit'))
            group.append(a)
            group.append(_html.TagLessElement('&nbsp;'))

        if entity.odm_ui_deletion_allowed() and \
                (entity.odm_auth_check_permission('delete') or entity.odm_auth_check_permission('delete_own')):
            d_form_url = _router.rule_url('odm_ui@d_form', {
                'model': entity.model,
                'ids': str(entity.id),
                '__redirect': _router.rule_url('odm_ui@browse', {'model': entity.model}),
            })
            title = _lang.t('odm_ui@delete')
            a = _html.A(css='btn btn-xs btn-danger', href=d_form_url, title=title)
            a.append(_html.I(css='fa fa-remove'))
            group.append(a)
            group.append(_html.TagLessElement('&nbsp;'))

        return group

    def render(self) -> str:

        # Browser title
        _metatag.t_set('title', self._model_class.t('odm_ui_browser_title_' + self._model))
        _metatag.t_set('description', '')

        # 'Create' toolbar button
        if self._mock.odm_auth_check_permission('create') and self._mock.odm_ui_creation_allowed():
            create_form_url = _router.rule_url('odm_ui@m_form', {
                'model': self._model,
                'eid': '0',
                '__redirect': _router.current_url(),
            })
            title = _lang.t('odm_ui@create')
            btn = _html.A(href=create_form_url, css='btn btn-default add-button', title=title)
            btn.append(_html.I(css='fa fa-fw fa-plus'))
            self._widget.toolbar.append(btn)
            self._widget.toolbar.append(_html.Span('&nbsp;'))

        # 'Delete' toolbar button
        if self._mock.odm_auth_check_permission('delete') and self._mock.odm_ui_deletion_allowed():
            delete_form_url = _router.rule_url('odm_ui@d_form', {'model': self._model})
            title = _lang.t('odm_ui@delete_selected')
            btn = _html.A(href=delete_form_url, css='hidden btn btn-danger mass-action-button', title=title)
            btn.append(_html.I(css='fa fa-fw fa-remove'))
            self._widget.toolbar.append(btn)
            self._widget.toolbar.append(_html.Span('&nbsp;'))

        # Additional toolbar buttons
        for btn_data in self._model_class.odm_ui_browser_mass_action_buttons():
            ep = btn_data.get('ep')
            url = _router.rule_url(ep) if ep else '#'
            css = 'btn btn-{} mass-action-button'.format(btn_data.get('color', 'default'))
            icon = 'fa fa-fw fa-' + btn_data.get('icon', 'question')
            button = _html.A(href=url, css=css, title=btn_data.get('title'))
            if icon:
                button.append(_html.I(css=icon))
            self._widget.toolbar.append(button)
            self._widget.toolbar.append(_html.Span('&nbsp;'))

        return self._widget.render()
