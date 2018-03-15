"""PytSite Object Document Mapper UI Plugin API Functions
"""
__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from typing import Iterable as _Iterable, Type as _Type
from plugins import odm as _odm, odm_auth as _odm_auth, form as _form
from . import _model, _forms


def get_m_form(model: str, eid=None, update_meta_title: bool = True, **kwargs) -> _forms.Modify:
    """Get entity modification form.
    """
    return _forms.Modify(attr_model=model, attr_eid=eid if eid != '0' else None,
                         attr_update_meta_title=update_meta_title, **kwargs)


def get_d_form(model: str, ids: _Iterable, **kwargs) -> _form.Form:
    """Get entities delete form.
    """
    return _forms.Delete(attr_model=model, attr_eids=ids, **kwargs)


def get_model_class(model: str) -> _Type[_model.UIEntity]:
    """Get ODM UI model class.
    """
    model_class = _odm.get_model_class(model)
    if not issubclass(model_class, _odm_auth.model.OwnedEntity):
        raise TypeError('{} must extend {}'.format(model_class, _odm_auth.model.OwnedEntity))

    if not issubclass(model_class, _model.UIEntity):
        raise TypeError('{} must extend {}'.format(model_class, _model.UIEntity))

    return model_class


def dispense_entity(model: str, entity_id: str = None) -> _model.UIEntity:
    """Dispense entity.
    """
    if not entity_id or entity_id == '0':
        entity_id = None

    entity = _odm.dispense(model, entity_id)

    if not isinstance(entity, _model.UIEntity):
        raise TypeError("Model '{}' must extend 'odm_ui.model.UIEntity'".format(model))

    return entity
