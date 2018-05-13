"""PytSite Object Document Mapper UI Plugin Forms
"""
__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from pytsite import lang as _lang, http as _http, events as _events, router as _router, html as _html, \
    logger as _logger, errors as _errors
from plugins import widget as _widget, form as _form, odm as _odm, odm_auth as _odm_auth
from . import _model


class Modify(_form.Form):
    def _on_setup_form(self):
        """Hook
        """
        model = self.attr('model')
        if not model:
            raise ValueError('Model is not specified')

        try:
            from ._api import dispense_entity
            entity = dispense_entity(model, self.attr('eid'))
        except _odm.error.EntityNotFound:
            raise _http.error.NotFound()

        if entity.is_new:
            # Check if entities of this model can be created
            perms_allow = entity.odm_auth_check_permission('create')
            odm_ui_allows = entity.odm_ui_creation_allowed()
            if not (perms_allow and odm_ui_allows):
                raise _http.error.Forbidden()

            # Setup form title
            self.title = entity.t('odm_ui_form_title_create_' + model)
        else:
            # Check if the entity can be modified
            perms_allow = entity.odm_auth_check_permission('modify') or entity.odm_auth_check_permission('modify_own')
            odm_ui_allows = entity.odm_ui_modification_allowed()
            if not (perms_allow and odm_ui_allows):
                raise _http.error.Forbidden()

            # Setup form title
            self.title = entity.t('odm_ui_form_title_modify_' + model)

        # Setting up the form through entity hook and global event
        entity.odm_ui_m_form_setup(self)
        _events.fire('odm_ui@m_form_setup.{}'.format(model), frm=self, entity=entity)

        # Redirect
        if not self.redirect:
            self.redirect = 'ENTITY_VIEW'

        # CSS
        self.css += ' odm-ui-form odm-ui-form-' + model

    def _on_setup_widgets(self):
        from ._api import dispense_entity

        model = self.attr('model')
        eid = self.attr('eid')

        # Setting up form's widgets through entity hook and global event
        entity = dispense_entity(model, eid)
        entity.odm_ui_m_form_setup_widgets(self)
        _events.fire('odm_ui@m_form_setup_widgets.{}'.format(model), frm=self, entity=entity)

        if self.current_step == 1:
            # Entity model
            self.add_widget(_widget.input.Hidden(
                uid='model',
                value=model,
                form_area='hidden',
            ))

            # Entity ID
            self.add_widget(_widget.input.Hidden(
                uid='eid',
                value=eid,
                form_area='hidden',
            ))

        # Cancel button
        cancel_href = '#'
        if not self.modal:
            cancel_href = self.redirect
            if not cancel_href or cancel_href == 'ENTITY_VIEW':
                if not entity.is_new and entity.odm_ui_view_url():
                    cancel_href = entity.odm_ui_view_url()
                else:
                    cancel_href = _router.base_url()

        self.add_widget(_widget.button.Link(
            weight=15,
            uid='action_cancel_' + str(self.current_step),
            value=_lang.t('odm_ui@cancel'),
            icon='fa fa-fw fa-remove',
            href=cancel_href,
            dismiss='modal',
            form_area='footer',
        ))

    def _on_validate(self):
        # Ask entity to validate the form
        from ._api import dispense_entity

        dispense_entity(self.attr('model'), self.attr('eid')).odm_ui_m_form_validate(self)

    def _on_submit(self):
        from ._api import dispense_entity

        # Dispense entity
        entity = dispense_entity(self.attr('model'), self.attr('eid'))

        # Fill entity fields
        try:
            entity.odm_ui_m_form_submit(self)
        except Exception as e:
            _router.session().add_error_message(str(e))
            raise e

        # Process 'special' redirect endpoint
        if self.redirect == 'ENTITY_VIEW':
            self.redirect = entity.odm_ui_view_url()

        return _http.RedirectResponse(self.redirect)


class MassAction(_form.Form):
    """ODM UI Mass Action Form.
    """

    def _on_setup_form(self):
        """Hook
        """
        super()._on_setup_form()

        model = self.attr('model')
        if not model:
            raise ValueError('Model is not specified')

        eids = self.attr('eids', self.attr('ids', []))
        if isinstance(eids, str):
            self.set_attr('eids', eids.split(','))

        if not self.redirect:
            from ._api import get_model_class
            self.redirect = _router.rule_url(get_model_class(model).odm_ui_browse_rule(), {'model': model})

    def _on_setup_widgets(self):
        """Hook.
        """
        from ._api import dispense_entity

        # List of items to process
        ol = _html.Ol()
        for eid in self.attr('eids', self.attr('ids', [])):
            entity = dispense_entity(self.attr('model'), eid)
            self.add_widget(_widget.input.Hidden(uid='eids-' + eid, name='eids', value=eid))
            ol.append(_html.Li(entity.odm_ui_mass_action_entity_description()))
        self.add_widget(_widget.static.HTML(uid='eids-text', em=ol))

        # Submit button
        submit_button = self.get_widget('action_submit')  # type: _widget.button.Submit
        submit_button.value = _lang.t('odm_ui@continue')
        submit_button.icon = 'angle-double-right'

        # Cancel button
        self.add_widget(_widget.button.Link(
            uid='action_cancel',
            weight=10,
            value=_lang.t('odm_ui@cancel'),
            href=self.redirect,
            icon='fa fa-fw fa-ban',
            form_area='footer'
        ))


class Delete(MassAction):
    """Entities Delete Form.
    """

    def _on_setup_form(self):
        """Hook.
        """
        super()._on_setup_form()

        model = self.attr('model')

        # Check permissions
        for eid in self.attr('eids', self.attr('ids', [])):
            if not (_odm_auth.check_permission('delete', model) or
                    _odm_auth.check_permission('delete_own', model, eid)):
                raise _http.error.Forbidden()

        # Form title
        model_class = _odm.get_model_class(model)  # type: _model.UIEntity
        self.title = model_class.t('odm_ui_form_title_delete_' + model)

    def _on_setup_widgets(self):
        """Hook.
        """
        super()._on_setup_widgets()

        # Change submit button color
        self.get_widget('action_submit').color = 'danger'

    def _on_submit(self):
        from ._api import dispense_entity

        model = self.attr('model')

        try:
            # Ask entities to process deletion
            for eid in self.attr('eids', self.attr('ids', [])):
                dispense_entity(model, eid).odm_ui_d_form_submit()

            _router.session().add_info_message(_lang.t('odm_ui@operation_successful'))

        # Entity deletion was forbidden
        except _errors.ForbidDeletion as e:
            _logger.error(e)
            _router.session().add_error_message(_lang.t('odm_ui@entity_deletion_forbidden') + '. ' + str(e))

        return _http.RedirectResponse(self.redirect)
