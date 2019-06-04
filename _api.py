"""PytSite Object Document Mapper UI Plugin API Functions
"""
__author__ = 'Oleksandr Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from typing import Iterable, Type
from pytsite import router
from plugins import odm, odm_auth, form
from . import _model, _forms, _browser


def get_model_class(model: str) -> Type[_model.UIEntity]:
    """Get ODM UI model class
    """
    model_class = odm.get_model_class(model)
    if not issubclass(model_class, odm_auth.model.OwnedEntity):
        raise TypeError('{} must extend {}'.format(model_class, odm_auth.model.OwnedEntity))

    if not issubclass(model_class, _model.UIEntity):
        raise TypeError('{} must extend {}'.format(model_class, _model.UIEntity))

    return model_class


def dispense_entity(model: str, entity_id: str = None) -> _model.UIEntity:
    """Dispense entity.
    """
    entity = odm.dispense(model, entity_id)

    if not isinstance(entity, _model.UIEntity):
        raise TypeError("Model '{}' must extend 'odm_ui.model.UIEntity'".format(model))

    return entity


def get_browser(model: str, **kwargs) -> _browser.Browser:
    """Get entities browser
    """
    return _browser.Browser(model, **kwargs)


def get_m_form(model: str, eid: str = None, **kwargs) -> _forms.Modify:
    """Get entity modification form
    """
    return _forms.Modify(router.request(), model=model, eid=eid, **kwargs)


def get_d_form(model: str, eids: Iterable, **kwargs) -> form.Form:
    """Get entities delete form
    """
    return _forms.Delete(router.request(), model=model, eids=eids, **kwargs)
