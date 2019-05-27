"""PytSite Object Document Mapper UI Plugin Models
"""
__author__ = 'Oleksandr Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from typing import Tuple as _Tuple, Dict as _Dict, Type as _Type, List as _List, Union as _Union, Optional as _Optional
from pytsite import router as _router, lang as _lang, routing as _routing
from plugins import widget as _widget, odm as _odm, odm_auth as _odm_auth, form as _form, admin as _admin
from plugins.odm_auth import PERM_MODIFY, PERM_DELETE

_ADM_BP = _admin.base_path()


class UIEntity(_odm_auth.model.OwnedEntity):
    """ODM entity with UI related methods.
    """

    @classmethod
    def _get_rule(cls, rule_type: str) -> _Optional[str]:
        path = _router.current_path()

        ref = _router.request().referrer
        ref_path = _router.url(ref, add_lang_prefix=False, as_list=True)[2] if ref else ''

        if path.startswith(_ADM_BP) or ref_path.startswith(_ADM_BP):
            rule_type = 'admin_' + rule_type

        return 'odm_ui@' + rule_type

    @classmethod
    def odm_ui_browser_widget_class(cls) -> _Type[_widget.misc.DataTable]:
        return _widget.misc.BootstrapTable

    def odm_ui_browser_setup(self, browser):
        """Setup ODM UI browser hook.

        :type browser: odm_ui.Browser
        """
        pass

    def odm_ui_browser_setup_finder(self, finder: _odm.SingleModelFinder, args: _routing.ControllerArgs):
        search_query = args.get('search')
        if search_query:
            if self.has_text_index:
                finder.text(search_query)
            else:
                for name, field in self.fields.items():
                    if isinstance(field, _odm.field.String):
                        finder.or_regex(name, search_query, True)

    def odm_ui_browser_row(self) -> _Union[tuple, list, dict]:
        """Get single UI browser row.
        """
        return ()

    @classmethod
    def odm_ui_browser_mass_action_buttons(cls) -> _Tuple[_Dict, ...]:
        """Get toolbar mass actions buttons data.
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

    def odm_ui_browser_entity_actions(self, browser) -> _List[_Dict]:
        """Get actions buttons data for single data row.
        """
        r = []

        if self.odm_ui_modification_allowed() and self.odm_auth_check_entity_permissions(PERM_MODIFY):
            r.append({
                'url': _router.rule_url(browser.m_form_rule, {
                    'model': self.model,
                    'eid': str(self.id),
                    '__redirect': _router.rule_url(browser.browse_rule, {'model': self.model}),
                }),
                'title': _lang.t('odm_ui@modify'),
                'icon': 'fa fas fa-fw fa-fw fa-edit',
            })

        if self.odm_ui_deletion_allowed() and self.odm_auth_check_entity_permissions(PERM_DELETE):
            r.append({
                'url': _router.rule_url(browser.d_form_rule, {
                    'model': self.model,
                    'ids': str(self.id),
                    '__redirect': _router.rule_url(browser.browse_rule, {'model': self.model}),
                }),
                'title': _lang.t('odm_ui@delete'),
                'icon': 'fa fas fa-fw fa-fw fa-remove fa-times',
                'color': 'danger',
            })

        return r

    def odm_ui_mass_action_entity_description(self) -> str:
        """Get entity description on mass action forms.
        """
        if hasattr(self, 'id'):
            return str(self.id)

    @classmethod
    def odm_ui_browse_rule(cls) -> str:
        """Get browse router's rule name
        """
        return cls._get_rule('browse')

    def odm_ui_browse_url(self, args: dict = None, **kwargs):
        """Get browse URL
        """
        if args is None:
            args = {}

        args.update({
            'model': self.model
        })

        return _router.rule_url(self.odm_ui_browse_rule(), args, **kwargs)

    @classmethod
    def odm_ui_m_form_rule(cls) -> str:
        """Get modify form router's rule name
        """
        return cls._get_rule('m_form')

    def odm_ui_m_form_url(self, args: dict = None, **kwargs):
        """Get modify form URL
        """
        if args is None:
            args = {}

        args.setdefault('__redirect', 'ENTITY_VIEW')

        args.update({
            'model': self.model,
            'eid': '0' if self.is_new else str(self.id),
        })

        return _router.rule_url(self.odm_ui_m_form_rule(), args, **kwargs)

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
                    required=field.is_required,
                    default=field.default,
                    value=field.get_val(),
                ))
            elif isinstance(field, _odm.field.Integer):
                frm.add_widget(_widget.input.Integer(
                    uid=uid,
                    weight=weight,
                    label=self.t(uid),
                    required=field.is_required,
                    default=field.default,
                    value=field.get_val(),
                ))
            elif isinstance(field, _odm.field.Decimal):
                frm.add_widget(_widget.input.Decimal(
                    uid=uid,
                    weight=weight,
                    label=self.t(uid),
                    required=field.is_required,
                    default=field.default,
                    value=field.get_val(),
                ))
            elif isinstance(field, _odm.field.Email):
                frm.add_widget(_widget.input.Email(
                    uid=uid,
                    weight=weight,
                    label=self.t(uid),
                    required=field.is_required,
                    default=field.default,
                    value=field.get_val(),
                ))
            elif isinstance(field, _odm.field.String):
                frm.add_widget(_widget.input.Text(
                    uid=uid,
                    weight=weight,
                    label=self.t(uid),
                    required=field.is_required,
                    default=field.default,
                    value=field.get_val(),
                ))
            elif isinstance(field, _odm.field.Enum):
                frm.add_widget(_widget.select.Select(
                    uid=uid,
                    weight=weight,
                    label=self.t(uid),
                    required=field.is_required,
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
        return cls._get_rule('d_form')

    def odm_ui_d_form_url(self, args: dict = None, **kwargs) -> str:
        if args is None:
            args = {}

        args.update({
            'model': self.model,
            'eids': str(self.id)
        })

        return _router.rule_url(self.odm_ui_d_form_rule(), args, **kwargs)

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

    def odm_ui_view_url(self, args: dict = None, **kwargs) -> str:
        if self.is_new:
            raise RuntimeError("Cannot generate view URL for non-saved entity of model '{}'".format(self.model))

        if args is None:
            args = {}

        args.update({
            'model': self.model,
            'eid': str(self.id),
        })

        return _router.rule_url(self.odm_ui_view_rule(), args, **kwargs)

    def odm_ui_widget_select_search_entities(self, f: _odm.MultiModelFinder, args: dict):
        """Hook
        """
        pass

    def odm_ui_widget_select_search_entities_is_visible(self, args: dict) -> bool:
        """Hook
        """
        return True

    def odm_ui_widget_select_search_entities_title(self, args: dict) -> str:
        """Hook
        """
        return self.ref

    @property
    def url(self) -> str:
        """Shortcut
        """
        return self.odm_ui_view_url()

    def as_jsonable(self, **kwargs) -> dict:
        r = super().as_jsonable(**kwargs)

        try:
            r['urls'] = {
                'view': self.url,
                'modify': self.modify_url,
            }
        except NotImplementedError:
            pass

        return r
