"""PytSite Object Document Mapper UI Plugin Forms
"""
__author__ = 'Oleksandr Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from pytsite import lang, http, events, router, html, logger, errors
from plugins import widget, form, odm, odm_auth
from plugins.odm_auth import PERM_CREATE, PERM_MODIFY, PERM_DELETE
from . import _model


class Modify(form.Form):
    def _on_setup_form(self):
        """Hook
        """
        model = self.attr('model')
        if not model:
            raise ValueError('Model is not specified')

        if not self.name:
            self.name = 'odm_ui_modify_' + model

        try:
            from ._api import dispense_entity
            entity = dispense_entity(model, self.attr('eid'))
        except odm.error.EntityNotFound:
            raise http.error.NotFound()

        if entity.is_new:
            # Check if entities of this model can be created
            perms_allow = entity.odm_auth_check_entity_permissions(PERM_CREATE)
            odm_ui_allows = entity.odm_ui_creation_allowed()
            if not (perms_allow and odm_ui_allows):
                raise http.error.Forbidden()

            # Setup form title
            self.title = entity.t('odm_ui_form_title_create_' + model)
        else:
            # Check if the entity can be modified
            perms_allow = entity.odm_auth_check_entity_permissions(PERM_MODIFY)
            odm_ui_allows = entity.odm_ui_modification_allowed()
            if not (perms_allow and odm_ui_allows):
                raise http.error.Forbidden()

            # Setup form title
            self.title = entity.t('odm_ui_form_title_modify_' + model)

        # Setting up the form through entity hook and global event
        entity.odm_ui_m_form_setup(self)
        events.fire('odm_ui@m_form_setup.{}'.format(model), frm=self, entity=entity)

        # Redirect
        if not self.redirect:
            self.redirect = 'ENTITY_VIEW'

        # CSS
        self.css += ' odm-ui-form odm-ui-m-form odm-ui-form-' + model

    def _on_setup_widgets(self):
        from ._api import dispense_entity

        model = self.attr('model')
        eid = self.attr('eid')

        # Setting up form's widgets through entity hook and global event
        entity = dispense_entity(model, eid)
        entity.odm_ui_m_form_setup_widgets(self)
        events.fire('odm_ui@m_form_setup_widgets.{}'.format(model), frm=self, entity=entity)

        if self.current_step == 1:
            # Entity model
            self.add_widget(widget.input.Hidden(
                uid='model',
                value=model,
                form_area='hidden',
            ))

            # Entity ID
            self.add_widget(widget.input.Hidden(
                uid='eid',
                value=eid,
                form_area='hidden',
            ))

            # Entity ref
            self.add_widget(widget.input.Hidden(
                uid='ref',
                value=entity.ref if not entity.is_new else None,
                form_area='hidden',
            ))

        # Cancel button URL
        cancel_href = self.redirect
        if not cancel_href or cancel_href == 'ENTITY_VIEW':
            if self.referer != self.location and self.referer:
                cancel_href = self.referer
            elif not entity.is_new and entity.odm_ui_view_url():
                cancel_href = entity.odm_ui_view_url()
            else:
                cancel_href = router.base_url()

        # Cancel button
        self.add_widget(widget.button.Link(
            uid='action_cancel_' + str(self.current_step),
            weight=150,
            value=lang.t('odm_ui@cancel'),
            icon='fa fas fa-fw fa-remove fa-times',
            href=cancel_href,
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
            router.session().add_error_message(str(e))
            raise e

        # Process 'special' redirect endpoint
        if self.redirect == 'ENTITY_VIEW':
            self.redirect = entity.odm_ui_view_url()


class MassAction(form.Form):
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
            self.redirect = router.rule_url(get_model_class(model).odm_ui_browse_rule(), {'model': model})

        self.css += ' odm-ui-mass-action-form'

    def _on_setup_widgets(self):
        """Hook.
        """
        from ._api import dispense_entity

        # List of items to process
        ol = html.Ol()
        for eid in self.attr('eids', self.attr('ids', [])):
            entity = dispense_entity(self.attr('model'), eid)
            self.add_widget(widget.input.Hidden(uid='eids-' + eid, name='eids', value=eid))
            ol.append(html.Li(entity.odm_ui_mass_action_entity_description()))
        self.add_widget(widget.static.HTML(uid='eids-text', em=ol))

        # Submit button
        submit_button = self.get_widget('action_submit')  # type: widget.button.Submit
        submit_button.value = lang.t('odm_ui@continue')
        submit_button.icon = 'angle-double-right'

        # Cancel button
        self.add_widget(widget.button.Link(
            uid='action_cancel',
            weight=100,
            value=lang.t('odm_ui@cancel'),
            href=self.referer or self.redirect or router.base_url(),
            icon='fa fas fa-ban',
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

        if not self.name:
            self.name = 'odm_ui_delete_' + model

        # Check permissions
        for eid in self.attr('eids', self.attr('ids', [])):
            e = odm.dispense(model, eid)  # type: odm_auth.OwnedEntity
            if not e.odm_auth_check_entity_permissions(PERM_DELETE):
                raise http.error.Forbidden()

        # Form title
        model_class = odm.get_model_class(model)  # type: _model.UIEntity
        self.title = model_class.t('odm_ui_form_title_delete_' + model)

        # Form CSS
        self.css += ' odm-ui-mass-d-form'

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

            router.session().add_info_message(lang.t('odm_ui@operation_successful'))

        # Entity deletion was forbidden
        except errors.ForbidDeletion as e:
            logger.error(e)
            router.session().add_error_message(lang.t('odm_ui@entity_deletion_forbidden') + '. ' + str(e))
