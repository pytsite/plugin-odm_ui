"""PytSite Object Document Mapper UI Plugin Entities Browser
"""
__author__ = 'Oleksandr Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

import htmler
from typing import Union
from pytsite import router, lang, events, routing, errors
from plugins import widget, auth, odm, http_api, odm_auth
from plugins.odm_auth import PERM_CREATE, PERM_MODIFY, PERM_DELETE, PERM_MODIFY_OWN, PERM_DELETE_OWN
from . import _api


class Browser:
    """ODM Entities Browser
    """

    def __init__(self, model: str, **kwargs):
        """Init
        """
        if not model:
            raise RuntimeError('No model specified')

        if not odm_auth.check_model_permissions(model, [PERM_CREATE, PERM_MODIFY, PERM_DELETE,
                                                        PERM_MODIFY_OWN, PERM_DELETE_OWN]):
            raise errors.ForbidOperation("Current user is not allowed to browse '{}' entities".format(model))

        # Model
        self._model = model

        # Model class
        self._model_class = _api.get_model_class(self._model)

        self._current_user = auth.get_current_user()
        self._browse_rule = kwargs.get('browse_rule', self._model_class.odm_ui_browse_rule())
        self._m_form_rule = kwargs.get('m_form_rule', self._model_class.odm_ui_m_form_rule())
        self._d_form_rule = kwargs.get('d_form_rule', self._model_class.odm_ui_d_form_rule())

        # Widget
        widget_class = self._model_class.odm_ui_browser_widget_class()
        if not (issubclass(widget_class, widget.misc.DataTable)):
            raise TypeError('Subclass of {} expected, got'.format(widget.misc.DataTable, widget_class))
        self._widget = widget_class(
            uid='odm-ui-browser-' + model,
            rows_url=http_api.url('odm_ui@get_browser_rows', {
                'model': self._model,
                'browse_rule': self._browse_rule,
                'm_form_rule': self._m_form_rule,
                'd_form_rule': self._d_form_rule,
            }),
            update_rows_url=http_api.url('odm_ui@put_browser_rows', {'model': model})
        )

        # Call model's class to perform setup tasks
        _api.dispense_entity(self._model).odm_ui_browser_setup(self)

        # Notify external events listeners
        events.fire('odm_ui@browser_setup.{}'.format(self._model), browser=self)

        # Check if the model specified data fields
        if not self.data_fields:
            raise RuntimeError('No data fields was defined')

        # Actions column
        if self._model_class.odm_ui_entity_actions_enabled() and \
                (self._model_class.odm_ui_modification_allowed() or self._model_class.odm_ui_deletion_allowed()):
            self.insert_data_field('entity-actions', 'odm_ui@actions', False)

    @property
    def model(self) -> str:
        """Get browser entities model
        """
        return self._model

    @property
    def title(self) -> str:
        """Get browser's title
        """
        return self._model_class.t('odm_ui_browser_title_' + self._model)

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
    def data_fields(self) -> Union[list, tuple]:
        return self._widget.data_fields

    @data_fields.setter
    def data_fields(self, value: Union[list, tuple]):
        self._widget.data_fields = value

    @property
    def default_sort_field(self) -> str:
        return self._widget.default_sort_field

    @default_sort_field.setter
    def default_sort_field(self, value: str):
        self._widget.default_sort_field = value

    @property
    def default_sort_order(self) -> str:
        return odm.I_DESC if self._widget.default_sort_order == 'desc' else odm.I_ASC

    @default_sort_order.setter
    def default_sort_order(self, value: Union[int, str]):
        if isinstance(value, int):
            value = 'desc' if value == odm.I_DESC else 'asc'

        self._widget.default_sort_order = value

    def insert_data_field(self, name: str, title: str = None, sortable: bool = True, pos: int = None):
        self._widget.insert_data_field(name, title, sortable, pos)

    def remove_data_field(self, name: str):
        self._widget.remove_data_field(name)

    def get_rows(self, args: routing.ControllerArgs) -> dict:
        """Get browser rows.
        """
        # Instantiate finder
        finder = odm.find(self._model)

        # Check if the user can modify/delete any entity
        if not odm_auth.check_model_permissions(self._model, [PERM_MODIFY, PERM_DELETE]) and \
                odm_auth.check_model_permissions(self._model, [PERM_MODIFY_OWN, PERM_DELETE_OWN]):
            # Show only entities owned by user
            finder.mock.has_field('author') and finder.eq('author', self._current_user)

        # Let model to finish finder setup
        _api.dispense_entity(self._model).odm_ui_browser_setup_finder(finder, args)

        # Sort
        sort_order = odm.I_DESC if args.get('order', self.default_sort_order) in (-1, 'desc') else odm.I_ASC
        sort_field = args.get('sort')
        if sort_field and finder.mock.has_field(sort_field):
            finder.sort([(sort_field, sort_order)])
        elif self.default_sort_field:
            finder.sort([(self.default_sort_field, sort_order)])

        # Get root elements first
        finder.add_sort('_parent', pos=0)

        # Prepare result
        r = {
            'total': finder.count(),
            'rows': []
        }

        # Build table rows
        cursor = finder.skip(args.get('offset', 0)).get(args.get('limit', 0))
        for entity in cursor:
            row = entity.odm_ui_browser_row()
            events.fire('odm_ui@browser_row.{}'.format(self._model), entity=entity, row=row)

            if not row:
                continue

            # Build row's cells
            fields_data = {
                '__id': str(entity.id),
                '__parent': str(entity.parent.id) if entity.parent else None,
            }

            if not isinstance(row, dict):
                raise TypeError('{}.odm_ui_browser_row() must return dict, got {}'.
                                format(entity.__class__.__name__, type(row)))

            for df in self.data_fields:
                fields_data[df[0]] = row.get(df[0], '&nbsp;')

            # Action buttons
            if self._model_class.odm_ui_entity_actions_enabled() and \
                    (self._model_class.odm_ui_modification_allowed() or self._model_class.odm_ui_deletion_allowed()):

                actions = htmler.TagLessElement(child_sep='&nbsp;')
                for btn_data in entity.odm_ui_browser_entity_actions(self):
                    color = 'btn btn-sm btn-' + btn_data.get('color', 'default btn-light')
                    title = btn_data.get('title', '')
                    url = btn_data.get('url')
                    if not url:
                        rule = btn_data.get('rule')
                        url = router.rule_url(rule, {'ids': str(entity.id)}) if rule else '#'
                    btn = htmler.A(href=url, css=color + ' ' + btn_data.get('css', ''), title=title, role='button')
                    if btn_data.get('disabled'):
                        btn.set_attr('aria_disabled', 'true')
                        btn.add_css('disabled')
                    btn.append_child(htmler.I(css=btn_data.get('icon', 'fa fas fa-fw fa-question')))
                    actions.append_child(btn)

                fields_data['entity-actions'] = actions.render()

            r['rows'].append(fields_data)

        return r

    def render(self) -> str:
        # 'Create' toolbar button
        if self._model_class.odm_ui_creation_allowed() and odm_auth.check_model_permissions(self._model, PERM_CREATE):
            create_form_url = router.rule_url(self._m_form_rule, {
                'model': self._model,
                'eid': 0,
                '__redirect': router.current_url(),
            })
            title = lang.t('odm_ui@create')
            btn = htmler.A(href=create_form_url, css='btn btn-default btn-light add-button', title=title)
            btn.append_child(htmler.I(css='fa fas fa-fw fa-plus'))
            self._widget.toolbar.append_child(btn)
            self._widget.toolbar.append_child(htmler.Span('&nbsp;'))

        # 'Delete' toolbar button
        if self._model_class.odm_ui_deletion_allowed():
            delete_form_url = router.rule_url(self._d_form_rule, {'model': self._model})
            title = lang.t('odm_ui@delete_selected')
            btn = htmler.A(href=delete_form_url, css='hidden btn btn-danger mass-action-button sr-only', title=title)
            btn.append_child(htmler.I(css='fa fas fa-fw fa-remove fa-times'))
            self._widget.toolbar.append_child(btn)
            self._widget.toolbar.append_child(htmler.Span('&nbsp;'))

        # Additional toolbar buttons
        for btn_data in self._model_class.odm_ui_browser_mass_action_buttons():
            ep = btn_data.get('ep')
            url = router.rule_url(ep) if ep else '#'
            css = 'btn btn-{} mass-action-button'.format(btn_data.get('color', 'default btn-light'))
            icon = 'fa fas fa-fw fa-' + btn_data.get('icon', 'question')
            button = htmler.A(href=url, css=css, title=btn_data.get('title'))
            if icon:
                button.append_child(htmler.I(css=icon))
            self._widget.toolbar.append_child(button)
            self._widget.toolbar.append_child(htmler.Span('&nbsp;'))

        frm = htmler.Form(self._widget.render(), action='#', method='post', css='table-responsive odm-ui-browser')

        return frm.render()

    def __str__(self) -> str:
        return self.render()
