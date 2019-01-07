"""PytSite Object Document Mapper UI Plugin Widgets
"""
__author__ = 'Oleksandr Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from typing import List as _List, Callable as _Callable, Union as _Union, Iterable as _Iterable
from pyuca import Collator as _Collator
from json import dumps as _json_dumps
from pytsite import lang as _lang, html as _html
from plugins import widget as _widget, odm as _odm, http_api as _http_api, odm_http_api as _odm_http_api

_pyuca_col = _Collator()


def _sanitize_kwargs_exclude(kwargs: dict):
    if not ('exclude' in kwargs and kwargs['exclude']):
        return

    if isinstance(kwargs['exclude'], _odm.Entity):
        kwargs['exclude'] = [kwargs['exclude'].ref] if not kwargs['exclude'].is_new else []
    elif isinstance(kwargs['exclude'], str):
        kwargs['exclude'] = [kwargs['exclude']]
    elif isinstance(kwargs['exclude'], (list, tuple)):
        ex = []
        for item in kwargs['exclude']:
            if isinstance(item, _odm.Entity):
                if not item.is_new:
                    ex.append(item.ref)
            elif isinstance(item, str):
                ex.append(item)
            else:
                raise TypeError('Unsupported type: {}'.format(type(item)))

        kwargs['exclude'] = ex

    if kwargs.get('exclude_descendants', True):
        for ref in kwargs['exclude'].copy():
            for descendant in _odm.get_by_ref(ref).descendants:
                kwargs['exclude'].append(descendant.ref)


class EntitySelect(_widget.select.Select2):
    """Entity Select
    """

    @property
    def model(self) -> _List[str]:
        return self._model

    @model.setter
    def model(self, value: _List[str]):
        self._model = value

    @property
    def entity_title_args(self) -> bool:
        return self._entity_title_args

    @entity_title_args.setter
    def entity_title_args(self, value: bool):
        self._entity_title_args = value

    @property
    def ignore_missing_entities(self) -> bool:
        return self._ignore_missing_entities

    @ignore_missing_entities.setter
    def ignore_missing_entities(self, value: bool):
        self._ignore_missing_entities = value

    @property
    def ignore_invalid_refs(self) -> bool:
        return self._ignore_invalid_refs

    @ignore_invalid_refs.setter
    def ignore_invalid_refs(self, value: bool):
        self._ignore_invalid_refs = value

    @property
    def sort_by(self) -> str:
        return self._sort_by

    @sort_by.setter
    def sort_by(self, value: str):
        self._sort_by = value

    @property
    def sort_order(self) -> int:
        return self._sort_order

    @sort_order.setter
    def sort_order(self, value: int):
        self._sort_order = value

    def __init__(self, uid: str, **kwargs):
        self._model = kwargs.get('model')
        if not self._model:
            raise ValueError('Model is not specified')

        if not isinstance(self._model, list):
            self._model = [self._model]

        _sanitize_kwargs_exclude(kwargs)

        kwargs.setdefault('minimum_input_length', 3)
        kwargs.setdefault('ajax_url', _http_api.url('odm_ui@widget_entity_select'))
        kwargs.setdefault('linked_select_ajax_query_attr', self._model)

        self._limit = kwargs.get('limit', 10)
        self._sort_by = kwargs.get('sort_by')
        self._sort_order = kwargs.get('sort_order', _odm.I_ASC)
        self._entity_title_args = kwargs.get('entity_title_args', {})
        self._depth_indent = kwargs.get('depth_indent', '-')
        self._ignore_missing_entities = kwargs.get('ignore_missing_entities', False)
        self._ignore_invalid_refs = kwargs.get('ignore_invalid_refs', False)

        super().__init__(uid, **kwargs)

        self._ajax_url_query.update({
            'model': _json_dumps(self._model),
            'limit': self._limit,
            'sort_by': self._sort_by,
            'sort_order': self._sort_order,
            'entity_title_args': _json_dumps(self._entity_title_args),
            'depth_indent': self._depth_indent,
        })

    def set_val(self, value):
        try:
            if self._multiple:
                value = [_odm.get_by_ref(v).ref for v in value if v]
            else:
                value = _odm.get_by_ref(value).ref if value else None
            super().set_val(value)
        except _odm.error.InvalidReference as e:
            if not self._ignore_invalid_refs:
                raise e
        except _odm.error.EntityNotFound as e:
            if not self._ignore_missing_entities:
                raise e

        return self

    def _get_element(self, **kwargs):
        self._ajax_url_query.update(self._entity_title_args)

        # In AJAX-mode Select2 doesn't contain any items, but here is a selected item, it is necessary to append it
        if self._ajax_url and self._value:
            try:
                for ref in self._value if self._multiple else [self._value]:
                    entity = _odm.get_by_ref(ref)
                    title = entity.odm_ui_widget_select_search_entities_title(self._entity_title_args)
                    if entity.depth:
                        title = '{} {}'.format(self._depth_indent * entity.depth, title)
                    self._items.append([entity.ref, title])
            except _odm.error.InvalidReference as e:
                if not self._ignore_invalid_refs:
                    raise e
            except _odm.error.EntityNotFound as e:
                if not self.ignore_missing_entities:
                    raise e

        return super()._get_element()


class EntityCheckboxes(_widget.select.Checkboxes):
    """Select Entities with Checkboxes Widget.
    """

    def __init__(self, uid: str, **kwargs):
        """Init.
        """
        self._model = kwargs.get('model')
        if not self._model:
            raise ValueError('Model is not specified')

        self._caption_field = kwargs.get('caption_field')  # type: _Union[str, _Callable[[_odm.Entity], None]]
        if not self._caption_field:
            raise ValueError('Caption field is not specified')

        self._sort_field = kwargs.get('sort_field')  # type: str
        if not self._sort_field and isinstance(self._caption_field, str):
            self._sort_field = self._caption_field

        self._translate_captions = kwargs.get('translate_captions', False)

        self._exclude = []  # type: _List[_odm.model.Entity]
        for e in kwargs.get('exclude', ()):
            self._exclude.append(_odm.get_by_ref(e))

        self._sort_order = kwargs.get('sort_order', _odm.I_ASC)  # type: int
        self._finder_adjust = kwargs.get('finder_adjust')  # type: _Callable[[_odm.Finder], None]
        self._ignore_missing_entities = kwargs.get('ignore_missing_entities', False)
        self._ignore_invalid_refs = kwargs.get('ignore_invalid_refs', False)

        super().__init__(uid, **kwargs)

        # Available items will be set during call to self._get_element()
        self._items = []

    @property
    def ignore_missing_entities(self) -> bool:
        return self._ignore_missing_entities

    @ignore_missing_entities.setter
    def ignore_missing_entities(self, value: bool):
        self._ignore_missing_entities = value

    @property
    def ignore_invalid_refs(self) -> bool:
        return self._ignore_invalid_refs

    @ignore_invalid_refs.setter
    def ignore_invalid_refs(self, value: bool):
        self._ignore_invalid_refs = value

    @property
    def sort_field(self) -> str:
        """Get sort field
        """
        return self._sort_field

    @sort_field.setter
    def sort_field(self, value: str):
        """Set sort field
        """
        self._sort_field = value

    @property
    def sort_order(self) -> int:
        return self._sort_order

    @sort_order.setter
    def sort_order(self, value: int):
        self._sort_order = value

    def set_val(self, value):
        """Set value of the widget.

        :param value: list[odm.model.ODMModel] | list[DBRef] | list[str]
        """

        # Single string can be received from HTML form
        if isinstance(value, str) or value is None:
            value = [value] if value else []

        if not isinstance(value, (list, tuple)):
            raise TypeError("List of entities expected as a value of the widget '{}'".format(self.name))

        clean_val = []
        for v in value:
            if not v:
                continue

            try:
                clean_val.append(_odm.get_by_ref(v).ref)
            except _odm.error.InvalidReference as e:
                if not self._ignore_invalid_refs:
                    raise e
            except _odm.error.EntityNotFound as e:
                if not self._ignore_missing_entities:
                    raise e

        return super().set_val(clean_val)

    def _get_element(self, **kwargs):
        f = _odm.find(self._model)

        if self._sort_field:
            f.sort([(self._sort_field, self._sort_order)])

        if self._finder_adjust:
            self._finder_adjust(f)

        entities = []
        for e in f:
            if str(e) not in self._exclude:
                entities.append(e)

        # Do additional sorting of string fields, because MongoDB does not sort properly all languages
        if self._sort_field and isinstance(_odm.dispense(self._model).get_field(self._sort_field), _odm.field.String):
            rev = True if self._sort_order == _odm.I_DESC else False
            entities = sorted(entities, key=lambda ent: _pyuca_col.sort_key(ent.f_get(self._sort_field)), reverse=rev)

        for e in entities:
            caption = self._caption_field(e) if callable(self._caption_field) else e.get_field(self._caption_field)
            if self._translate_captions:
                caption = _lang.t(caption)

            self._items.append((str(e), str(caption)))

        return super()._get_element()


class EntitySlots(_widget.Abstract):
    @property
    def ignore_missing_entities(self) -> bool:
        return self._ignore_missing_entities

    @ignore_missing_entities.setter
    def ignore_missing_entities(self, value: bool):
        self._ignore_missing_entities = value

    @property
    def ignore_invalid_refs(self) -> bool:
        return self._ignore_invalid_refs

    @ignore_invalid_refs.setter
    def ignore_invalid_refs(self, value: bool):
        self._ignore_invalid_refs = value

    @property
    def sort_by(self) -> str:
        return self._sort_by

    @sort_by.setter
    def sort_by(self, value: str):
        self._sort_by = value

    @property
    def sort_order(self) -> int:
        return self._sort_order

    @sort_order.setter
    def sort_order(self, value: int):
        self._sort_order = value

    @property
    def entity_title_field(self) -> str:
        return self._entity_title_field

    @entity_title_field.setter
    def entity_title_field(self, value: str):
        self._entity_title_field = value

    @property
    def entity_url_field(self) -> str:
        return self._entity_url_field

    @entity_url_field.setter
    def entity_url_field(self, value: str):
        self._entity_url_field = value

    @property
    def entity_thumb_field(self) -> str:
        return self._entity_thumb_field

    @entity_thumb_field.setter
    def entity_thumb_field(self, value: str):
        self._entity_thumb_field = value

    @property
    def search_by(self) -> str:
        return self._search_by

    @search_by.setter
    def search_by(self, value: str):
        self._search_by = value

    @property
    def search_minimum_input_length(self) -> int:
        return self._search_minimum_input_length

    @search_minimum_input_length.setter
    def search_minimum_input_length(self, value: int):
        self._search_minimum_input_length = value

    @property
    def search_delay(self) -> int:
        return self._search_delay

    @search_delay.setter
    def search_delay(self, value: int):
        self._search_delay = value

    @property
    def modal_title(self) -> str:
        return self._modal_title

    @modal_title.setter
    def modal_title(self, value: str):
        self._modal_title = value

    @property
    def empty_slot_title(self) -> str:
        return self._empty_slot_title

    @empty_slot_title.setter
    def empty_slot_title(self, value: str):
        self._empty_slot_title = value

    @property
    def modal_ok_button_caption(self) -> str:
        return self._modal_ok_button_caption

    @modal_ok_button_caption.setter
    def modal_ok_button_caption(self, value: str):
        self._modal_ok_button_caption = value

    @property
    def exclude(self) -> _List[str]:
        return self._exclude

    @exclude.setter
    def exclude(self, value: _List):
        self._exclude = value

    def __init__(self, uid: str, **kwargs):
        super().__init__(uid, **kwargs)

        self._model = kwargs.get('model')
        if not self._model:
            raise TypeError("'model' argument is not specified")

        model_cls = _odm.get_model_class(self._model)
        if not (issubclass(model_cls, _odm_http_api.HTTPAPIEntityMixin) and model_cls.odm_http_api_enabled()):
            raise TypeError("Model '{}' does not support transfer via HTTP API".format(self._model))

        exclude = kwargs.get('exclude', [])
        if not isinstance('exclude', (list, tuple)):
            exclude = [exclude]

        self._ignore_missing_entities = kwargs.get('ignore_missing_entities', False)
        self._ignore_invalid_refs = kwargs.get('ignore_invalid_refs', False)
        self._sort_by = kwargs.get('sort_by')
        self._sort_order = kwargs.get('sort_order', _odm.I_ASC)
        self._entity_title_field = kwargs.get('entity_title_field', 'title')
        self._entity_url_field = kwargs.get('entity_url_field', 'url')
        self._entity_thumb_field = kwargs.get('entity_thumb_field', 'thumbnail')
        self._exclude = [_odm.get_by_ref(v).ref for v in exclude if v]
        self._search_by = kwargs.get('search_by')
        self._search_delay = kwargs.get('search_delay', 250)
        self._search_minimum_input_length = kwargs.get('search_minimum_input_length', 1)
        self._modal_title = kwargs.get('modal_title', _lang.t('odm_ui@search'))
        self._modal_ok_button_caption = kwargs.get('modal_ok_button_caption', _lang.t('odm_ui@add'))
        self._empty_slot_title = kwargs.get('empty_slot_title', _lang.t('odm_ui@add'))

        self._css += ' widget-odm-ui-entity-slots'

    def get_val(self, **kwargs) -> _Iterable[str]:
        return super().get_val(**kwargs)

    def set_val(self, value: _Union[_Iterable[_odm.Entity], _Iterable[str]]):
        try:
            super().set_val([_odm.get_by_ref(v).ref for v in value if v] if value else [])
        except _odm.error.InvalidReference as e:
            if not self._ignore_invalid_refs:
                raise e
        except _odm.error.EntityNotFound as e:
            if not self._ignore_missing_entities:
                raise e

        return self

    def _get_element(self, **kwargs) -> _html:
        self.data.update({
            'enabled': self._enabled,
            'empty_slot_title': self._empty_slot_title,
            'entity_thumb_field': self._entity_thumb_field,
            'entity_title_field': self._entity_title_field,
            'entity_url_field': self._entity_url_field,
            'exclude': _json_dumps(self._exclude),
            'modal_ok_button_caption': self._modal_ok_button_caption,
            'modal_title': self._modal_title,
            'model': self._model,
            'search_by': self._search_by,
            'search_delay': self._search_delay,
            'search_minimum_input_length': self._search_minimum_input_length,
            'sort_by': self._sort_by,
            'sort_order': self._sort_order,
            'value': _json_dumps(self.get_val()),
        })

        return _html.Div(css='widget-component')
