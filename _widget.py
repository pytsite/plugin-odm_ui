"""PytSite Object Document Mapper UI Plugin Widgets
"""
__author__ = 'Oleksandr Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from typing import List as _List, Tuple as _Tuple, Callable as _Callable, Iterable as _Iterable, Union as _Union, \
    Optional as _Optional
from bson.dbref import DBRef as _DBRef
from pyuca import Collator as _Collator
from pytsite import lang as _lang
from plugins import widget as _widget, odm as _odm, http_api as _http_api

_pyuca_col = _Collator()


class EntitySelect(_widget.select.Select):
    """Select Entity with Select Widget.
    """

    def __init__(self, uid: str, **kwargs):
        """Init
        """
        if 'exclude' in kwargs and kwargs['exclude']:
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

        super().__init__(uid, **kwargs)

        self._model = kwargs.get('model')
        if not self._model:
            raise ValueError('Model is not specified')

        self._caption_field = kwargs.get('caption_field')  # type: _Union[str, _Callable[[_odm.Entity], None]]
        if not self._caption_field:
            raise ValueError('Caption field is not specified')

        self._sort_field = kwargs.get('sort_field')  # type: str
        if not self._sort_field and isinstance(self._caption_field, str):
            self._sort_field = self._caption_field

        self._sort_order = kwargs.get('sort_order', _odm.I_ASC)  # type: int
        self._finder_adjust = kwargs.get('finder_adjust')  # type: _Callable[[_odm.Finder], None]
        self._ignore_missing_entities = kwargs.get('ignore_missing_entities', False)
        self._ignore_invalid_refs = kwargs.get('ignore_invalid_refs', False)

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
        return self._sort_field

    @sort_field.setter
    def sort_field(self, value: str):
        self._sort_field = value

    @property
    def sort_order(self) -> int:
        return self._sort_order

    @sort_order.setter
    def sort_order(self, value: int):
        self._sort_order = value

    def set_val(self, value):
        """Set value of the widget.
        """
        if value == '':
            value = None
        elif isinstance(value, _odm.model.Entity):
            value = value.ref
        elif isinstance(value, _DBRef):
            try:
                value = _odm.get_by_ref(value).ref
            except _odm.error.InvalidReference as e:
                if not self._ignore_invalid_refs:
                    raise e
            except _odm.error.EntityNotFound as e:
                if not self._ignore_missing_entities:
                    raise e

        return super().set_val(value)

    def _get_finder(self) -> _odm.Finder:
        finder = _odm.find(self._model)
        if self._sort_field:
            finder.sort([(self._sort_field, self._sort_order)])

        if self._finder_adjust:
            self._finder_adjust(finder)

        return finder

    def _get_caption(self, entity: _odm.model.Entity) -> str:
        if isinstance(self._caption_field, str):
            caption = str(entity.f_get(self._caption_field))
        elif callable(self._caption_field):
            caption = self._caption_field(entity)
        else:
            raise TypeError('Caption field must be a string or a callable, got {}'.format(type(self._caption_field)))

        if entity.depth:
            caption = '-' * entity.depth + ' ' + caption

        return caption

    def _build_items_tree(self, root_entities: _Iterable[_odm.Entity], _result: list = None) -> _List[_Tuple[str, str]]:
        if _result is None:
            _result = []

        for entity in root_entities:
            _result.append((entity.ref, self._get_caption(entity)))
            self._build_items_tree(entity.children, _result)

        return _result

    def _get_element(self, **kwargs):
        """Render the widget
        """
        root_items = [entity for entity in self._get_finder().eq('_parent', None)]

        # Do additional sorting of string fields, because MongoDB does not sort properly all languages
        if self._sort_field and isinstance(_odm.dispense(self._model).get_field(self._sort_field), _odm.field.String):
            root_items = sorted(root_items, key=lambda e: _pyuca_col.sort_key(e.f_get(self._sort_field)),
                                reverse=True if self._sort_order == _odm.I_DESC else False)

        for item in self._build_items_tree(root_items):
            self._items.append((item[0], item[1]))

        return super()._get_element()


class EntityCheckboxes(_widget.select.Checkboxes):
    """Select Entities with Checkboxes Widget.
    """

    def __init__(self, uid: str, **kwargs):
        """Init.
        """
        super().__init__(uid, **kwargs)

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

        :param value: list[odm.models.ODMModel] | list[DBRef] | list[str]
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


class EntitySelectSearch(_widget.select.Select2):
    """Entity Select
    """

    def __init__(self, uid: str, **kwargs):
        self._model = kwargs.get('model')
        if not self._model:
            raise ValueError('Model is not specified')

        kwargs.setdefault('ajax_url', _http_api.url('odm_ui@widget_entity_select_search', {'model': self._model}))
        kwargs.setdefault('linked_select_ajax_query_attr', self._model)

        self._entity_title_args = kwargs.get('entity_title_args', {})
        self._ignore_missing_entities = kwargs.get('ignore_missing_entities', False)
        self._ignore_invalid_refs = kwargs.get('ignore_invalid_refs', False)

        super().__init__(uid, **kwargs)

    @property
    def model(self) -> str:
        return self._model

    @model.setter
    def model(self, value: str):
        self._model = value

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

    def set_val(self, value):
        return super().set_val(_odm.get_by_ref(value).ref if value else None)

    def get_val(self) -> _Optional[_odm.Entity]:
        return _odm.get_by_ref(self._value) if self._value else None

    def _get_element(self, **kwargs):
        self._ajax_url_query.update(self._entity_title_args)

        # In AJAX-mode Select2 doesn't contain any items,
        # but if we have selected item, it is necessary to append it
        if self._ajax_url and self._value:
            try:
                entity = _odm.get_by_ref(self._value)
                if hasattr(entity, 'odm_ui_widget_select_search_entities_title'):
                    self._items.append([
                        self._value,
                        entity.odm_ui_widget_select_search_entities_title(self._entity_title_args),
                    ])
                else:
                    raise ValueError("Entity '{}' does not support this operation".format(type(entity)))
            except _odm.error.InvalidReference as e:
                if not self._ignore_invalid_refs:
                    raise e
            except _odm.error.EntityNotFound as e:
                if not self.ignore_missing_entities:
                    raise e

        return super()._get_element()
