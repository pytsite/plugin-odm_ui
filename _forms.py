"""PytSite Object Document Mapper UI Plugin Forms
"""
__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from pytsite import lang as _lang, http as _http, events as _events, metatag as _metatag, router as _router, \
    html as _html, logger as _logger, errors as _errors
from plugins import widget as _widget, form as _form, odm as _odm, odm_auth as _odm_auth
from . import _model


class Modify(_form.Form):
    @property
    def update_meta_title(self) -> bool:
        return self.attr('update_meta_title')

    @update_meta_title.setter
    def update_meta_title(self, value: bool):
        self.attrs['update_meta_title'] = value

    def _on_setup_form(self, **kwargs):
        """Hook.
        :param **kwargs:
        """
        model = self.attr('model')

        if not model:
            raise ValueError('Model is not specified')

        self.attrs.setdefault('eid', 0)
        self.attrs.setdefault('update_meta_title', True)

        try:
            from ._api import dispense_entity
            entity = dispense_entity(model, self.attr('eid'))
        except _odm.error.EntityNotFound:
            raise _http.error.NotFound()

        # Check if entities of this model can be created
        if entity.is_new:
            perms_allow = entity.odm_auth_check_permission('create')
            odm_ui_allows = entity.odm_ui_creation_allowed()
            if not (perms_allow and odm_ui_allows):
                raise _http.error.Forbidden()

        # Check if the entity can be modified
        if not entity.is_new:
            perms_allow = entity.odm_auth_check_permission('modify') or entity.odm_auth_check_permission('modify_own')
            odm_ui_allows = entity.odm_ui_modification_allowed()
            if not (perms_allow and odm_ui_allows):
                raise _http.error.Forbidden()

        # Form title
        if entity.is_new:
            self._title = entity.t('odm_ui_form_title_create_' + model)
        else:
            self._title = entity.t('odm_ui_form_title_modify_' + model)

        # Setting up the form through entity hook and global event
        entity.odm_ui_m_form_setup(self)
        _events.fire('odm_ui@m_form_setup.{}'.format(model), frm=self, entity=entity)

        if self.attr('update_meta_title'):
            _metatag.t_set('title', self.title)

        # Default redirect
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
            cancel_href = _router.request().inp.get('__redirect')
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

        return _http.response.Redirect(self.redirect)


class MassAction(_form.Form):
    """ODM UI Mass Action Form.
    """

    def _on_setup_form(self, **kwargs):
        """Hook
        """
        super()._on_setup_form(**kwargs)

        if not self.attr('model'):
            raise ValueError('Model is not specified')

        eids = self.attr('eids', [])
        if isinstance(eids, str):
            self.attrs['eids'] = eids.split(',')

        if not self._redirect:
            self._redirect = _router.rule_url('odm_ui@browse', {'model': self.attr('model')})

    def _on_setup_widgets(self):
        """Hook.
        """
        from ._api import dispense_entity

        # List of items to process
        ol = _html.Ol()
        for eid in self.attr('eids'):
            entity = dispense_entity(self.attr('model'), eid)
            self.add_widget(_widget.input.Hidden(uid='ids-' + eid, name='ids', value=eid))
            ol.append(_html.Li(entity.odm_ui_mass_action_entity_description()))
        self.add_widget(_widget.static.HTML(uid='ids-text', em=ol))

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

    def _on_setup_form(self, **kwargs):
        """Hook.
        """
        super()._on_setup_form()

        model = self.attr('model')

        # Check permissions
        for eid in self.attr('eids', []):
            if not (_odm_auth.check_permission('delete', model) or
                    _odm_auth.check_permission('delete_own', model, eid)):
                raise _http.error.Forbidden()

        # Page title
        model_class = _odm.get_model_class(model)  # type: _model.UIEntity
        _metatag.t_set('title', model_class.t('odm_ui_form_title_delete_' + model))

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
            # Delete entities
            for eid in self.attr('eids', []):
                dispense_entity(model, eid).odm_ui_d_form_submit()

            _router.session().add_info_message(_lang.t('odm_ui@operation_successful'))

        # Entity deletion was forbidden
        except _errors.ForbidDeletion as e:
            _logger.error(e)
            _router.session().add_error_message(_lang.t('odm_ui@entity_deletion_forbidden') + '. ' + str(e))

        default_redirect = _router.rule_url('odm_ui@browse', {'model':model})

        return _http.response.Redirect(_router.request().inp.get('__redirect', default_redirect))
