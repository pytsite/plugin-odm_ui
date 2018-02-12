"""PytSite Object Document Mapper UI Plugin Entities Browser
"""
__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from typing import Callable as _Callable, Union as _Union
from pytsite import router as _router, metatag as _metatag, lang as _lang, html as _html, http as _http, \
    events as _events
from plugins import widget as _widget, auth as _auth, odm as _odm, permissions as _permissions, http_api as _http_api
from . import _api, _model


class Browser(_widget.misc.BootstrapTable):
    """ODM Entities Browser.
    """

    def __init__(self, model: str):
        """Init.
        """
        super().__init__('odm-ui-browser-' + model)

        self._model = model
        if not self._model:
            raise RuntimeError('No model specified')

        # Model class and mock instance
        self._model_class = _api.get_model_class(self._model)
        self._mock = _api.dispense_entity(self._model)

        # Check permissions
        if not self._mock.odm_auth_check_permission('view'):
            raise _http.error.Forbidden()

        self._data_url = _http_api.url('odm_ui@get_rows', {'model': self._model})
        self._current_user = _auth.get_current_user()
        self._finder_adjust = self._default_finder_adjust

        # Browser title
        if not _router.request().is_xhr:
            self._title = self._model_class.t('odm_ui_browser_title_' + self._model)
            _metatag.t_set('title', self._title)
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
                self._toolbar.append(btn)
                self._toolbar.append(_html.Span('&nbsp;'))

            # 'Delete' toolbar button
            if self._mock.odm_auth_check_permission('delete') and self._mock.odm_ui_deletion_allowed():
                delete_form_url = _router.rule_url('odm_ui@d_form', {'model': self._model})
                title = _lang.t('odm_ui@delete_selected')
                btn = _html.A(href=delete_form_url, css='hidden btn btn-danger mass-action-button', title=title)
                btn.append(_html.I(css='fa fa-fw fa-remove'))
                self._toolbar.append(btn)
                self._toolbar.append(_html.Span('&nbsp;'))

            # Additional toolbar buttons
            for btn_data in self._model_class.odm_ui_browser_mass_action_buttons():
                ep = btn_data.get('ep')
                url = _router.rule_url(ep) if ep else '#'
                css = 'btn btn-{} mass-action-button'.format(btn_data.get('color', 'default'))
                icon = 'fa fa-fw fa-' + btn_data.get('icon', 'question')
                button = _html.A(href=url, css=css, title=btn_data.get('title'))
                if icon:
                    button.append(_html.I(css=icon))
                self.toolbar.append(button)
                self._toolbar.append(_html.Span('&nbsp;'))

        # Call model's class to perform setup tasks
        self._model_class.odm_ui_browser_setup(self)

        # Notify external events listeners
        _events.fire('odm_ui@browser_setup.{}'.format(self._model), browser=self)

        # Head columns
        if not self.data_fields:
            raise RuntimeError("No data fields are defined")

        # JS code
        self._js_module = 'odm-ui-browser'

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

    def _default_finder_adjust(self, finder: _odm.Finder):
        pass

    def _alter_head_row(self, row: _html.Tr):
        # Actions column
        if self._model_class.odm_ui_entity_actions_enabled():
            row.append(_html.Th(_lang.t('odm_ui@actions'), data_field='__actions'))

    def get_rows(self, offset: int = 0, limit: int = 0, sort_field: str = None, sort_order: _Union[int, str] = None,
                 search: str = None) -> dict:
        """Get browser rows.
        """
        r = {'total': 0, 'rows': []}

        # Setup finder
        finder = _odm.find(self._model)
        self._finder_adjust(finder)

        # Permission based limitations if current user can work with only its OWN entities
        show_all = False
        for perm_prefix in ('odm_auth@modify.', 'odm_auth@delete.'):
            perm_name = perm_prefix + self._model
            if _permissions.is_permission_defined(perm_name) and self._current_user.has_permission(perm_name):
                show_all = True
                break

        # Add constraints to the finder if user cannot see all records
        if not show_all:
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
        if sort_field and finder.mock.has_field(sort_field):
            if isinstance(sort_order, int):
                sort_order = _odm.I_DESC if sort_order < 0 else _odm.I_ASC
            elif isinstance(sort_order, str):
                sort_order = _odm.I_DESC if sort_order.lower() == 'desc' else _odm.I_ASC
            else:
                sort_order = _odm.I_ASC
            finder.sort([(sort_field, sort_order)])
        elif self._default_sort_field:
            finder.sort([(self._default_sort_field, self._default_sort_order)])

        # Iterate over result and get content for table rows
        cursor = finder.skip(offset).get(limit)
        for entity in cursor:
            row = entity.odm_ui_browser_row()
            _events.fire('odm_ui@browser_row.{}'.format(self._model), entity=entity, row=row)

            if not row:
                continue

            # Build row's cells
            cells = {}
            if isinstance(row, (list, tuple)):
                if len(row) != len(self.data_fields):
                    raise ValueError(
                        '{}.odm_ui_browser_row() returns invalid number of cells'.format(entity.__class__.__name__)
                    )
                for f_name, cell_content in zip([df[0] for df in self._data_fields], row):
                    cells[f_name] = cell_content
            elif isinstance(row, dict):
                for df in self._data_fields:
                    cells[df[0]] = row.get(df[0], '&nbsp;')
            else:
                raise TypeError('{}.odm_ui_browser_row() must return list, tuple or dict, got {}'.
                                format(entity.__class__.__name__, type(row)))

            # Action buttons
            if self._model_class.odm_ui_entity_actions_enabled():
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

                cells['__actions'] = actions.render()

            r['rows'].append(cells)

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
