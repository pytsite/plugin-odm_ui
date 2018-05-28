"""PytSite Object Document Mapper UI Plugin Models
"""
__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from typing import Tuple as _Tuple, Dict as _Dict, Type as _Type
from pytsite import router as _router, lang as _lang
from plugins import widget as _widget, odm as _odm, odm_auth as _odm_auth, form as _form


class UIEntity(_odm_auth.model.OwnedEntity):
    """ODM entity with UI related methods.
    """

    @classmethod
    def odm_ui_browser_widget_class(cls) -> _Type[_widget.misc.DataTable]:
        return _widget.misc.BootstrapTable

    @classmethod
    def odm_ui_browser_setup(cls, browser):
        """Setup ODM UI browser hook.

        :type browser: odm_ui.Browser
        """
        pass

    @classmethod
    def odm_ui_browser_search(cls, finder: _odm.Finder, query: str):
        """Adjust ODM browser finder while performing search.
        """
        if finder.mock.has_text_index:
            finder.text(query)
        else:
            for name, field in finder.mock.fields.items():
                if isinstance(field, _odm.field.String):
                    finder.or_regex(name, query, True)

    @classmethod
    def odm_ui_browser_mass_action_buttons(cls) -> _Tuple[_Dict, ...]:
        """Get toolbar mass actions buttons data.
        """
        return ()

    def odm_ui_browser_row(self) -> _Tuple:
        """Get single UI browser row.
        """
        return ()

    @classmethod
    def odm_ui_creation_allowed(cls) -> bool:
        """Should be UI entity creation function be available.
        """
        return True

    @classmethod
    def odm_ui_modification_allowed(cls) -> bool:
        """Should be UI entity modification function be available.
        """
        return True

    @classmethod
    def odm_ui_deletion_allowed(cls) -> bool:
        """Should be UI entity deletion function be available.
        """
        return True

    @classmethod
    def odm_ui_entity_actions_enabled(cls) -> bool:
        """Should the 'actions' column be visible in the entities browser.
        """
        return True

    def odm_ui_browser_entity_actions(self) -> _Tuple[_Dict, ...]:
        """Get actions buttons data for single data row.
        """
        return ()

    def odm_ui_mass_action_entity_description(self) -> str:
        """Get entity description on mass action forms.
        """
        if hasattr(self, 'id'):
            return str(self.id)

    @classmethod
    def odm_ui_browse_rule(cls) -> str:
        """Get browse router's rule name
        """
        return 'odm_ui@admin_browse'

    def odm_ui_browse_url(self, args: dict = None):
        """Get browse URL
        """
        args.update({
            'model': self.model
        })

        return _router.rule_url(self.odm_ui_browse_rule(), args)

    @classmethod
    def odm_ui_m_form_rule(cls) -> str:
        """Get modify form router's rule name
        """
        return 'odm_ui@admin_m_form'

    def odm_ui_m_form_url(self, args: dict = None):
        """Get modify form URL
        """
        if args is None:
            args = {}

        args.update({
            'model': self.model,
            'eid': str(self.id),
            '__redirect': 'ENTITY_VIEW',
        })

        return _router.rule_url(self.odm_ui_m_form_rule(), args)

    @property
    def modify_url(self) -> str:
        """Shortcut
        """
        return self.odm_ui_m_form_url()

    def odm_ui_m_form_setup(self, frm: _form.Form):
        """Hook
        """
        pass

    def odm_ui_m_form_setup_widgets(self, frm: _form.Form):
        """Hook
        """
        weight = 0
        for uid, field in self.fields.items():
            if uid.startswith('_') or field is None:
                continue

            weight += 10

            if isinstance(field, _odm.field.Bool):
                frm.add_widget(_widget.select.Checkbox(
                    uid=uid,
                    weight=weight,
                    label=self.t(uid),
                    required=field.required,
                    default=field.default,
                    value=field.get_val(),
                ))
            elif isinstance(field, _odm.field.Integer):
                frm.add_widget(_widget.input.Integer(
                    uid=uid,
                    weight=weight,
                    label=self.t(uid),
                    required=field.required,
                    default=field.default,
                    value=field.get_val(),
                ))
            elif isinstance(field, _odm.field.Decimal):
                frm.add_widget(_widget.input.Decimal(
                    uid=uid,
                    weight=weight,
                    label=self.t(uid),
                    required=field.required,
                    default=field.default,
                    value=field.get_val(),
                ))
            elif isinstance(field, _odm.field.Email):
                frm.add_widget(_widget.input.Email(
                    uid=uid,
                    weight=weight,
                    label=self.t(uid),
                    required=field.required,
                    default=field.default,
                    value=field.get_val(),
                ))
            elif isinstance(field, _odm.field.String):
                frm.add_widget(_widget.input.Text(
                    uid=uid,
                    weight=weight,
                    label=self.t(uid),
                    required=field.required,
                    default=field.default,
                    value=field.get_val(),
                ))
            elif isinstance(field, _odm.field.Enum):
                frm.add_widget(_widget.select.Select(
                    uid=uid,
                    weight=weight,
                    label=self.t(uid),
                    required=field.required,
                    items=[(x, self.t(x)) for x in field.values],
                    default=field.default,
                    value=field.get_val(),
                ))

    def odm_ui_m_form_validate(self, frm: _form.Form):
        """Hook
        """
        pass

    def odm_ui_m_form_submit(self, frm: _form.Form):
        """Hook
        """
        # Populate form values to entity fields
        for f_name, f_value in frm.values.items():
            if self.has_field(f_name):
                self.f_set(f_name, f_value)

        # Save entity
        self.save()
        _router.session().add_info_message(_lang.t('odm_ui@operation_successful'))

    @classmethod
    def odm_ui_d_form_rule(cls) -> str:
        return 'odm_ui@admin_d_form'

    def odm_ui_d_form_url(self, ajax: bool = False) -> str:
        args = {
            'model': self.model,
            'eids': str(self.id)
        }

        if ajax:
            args['ajax'] = 'true'

        return _router.rule_url(self.odm_ui_d_form_rule(), args)

    def odm_ui_d_form_setup(self, frm: _form.Form):
        """Hook
        """
        raise NotImplementedError('Not implemented yet')

    def odm_ui_d_form_setup_widgets(self, frm: _form.Form):
        """Hook
        """
        raise NotImplementedError('Not implemented yet')

    def odm_ui_d_form_validate(self, frm: _form.Form):
        """Hook
        """
        raise NotImplementedError('Not implemented yet')

    def odm_ui_d_form_submit(self):
        """Hook
        """
        self.delete()

    @classmethod
    def odm_ui_view_rule(cls) -> str:
        """Get view router rule name
        """
        raise NotImplementedError('Not implemented yet')

    def odm_ui_view_url(self, args: dict = None) -> str:
        if self.is_new:
            raise RuntimeError("Cannot generate view URL for non-saved entity of model '{}'".format(self.model))

        if args is None:
            args = {}

        args.update({
            'model': self.model,
            'eid': str(self.id),
        })

        return _router.rule_url(self.odm_ui_view_rule(), args)

    @property
    def url(self) -> str:
        """Shortcut
        """
        return self.odm_ui_view_url()

    def as_jsonable(self, **kwargs) -> dict:
        r = super().as_jsonable(**kwargs)

        view_perm = self.odm_auth_check_permission('view')
        modify_perm = self.odm_auth_check_permission('modify')
        delete_perm = self.odm_auth_check_permission('delete')

        r['permissions'] = {
            'view': view_perm,
            'modify': modify_perm,
            'delete': delete_perm,
        }

        if view_perm:
            r['url'] = self.url

        if modify_perm:
            r['modify_url'] = self.modify_url

        return r
