"""PytSite Object Document Mapper UI Plugin Widgets
"""
__author__ = 'Alexander Shepetko'
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
                kwargs['exclude'] = [kwargs['exclude'].manual_ref] if not kwargs['exclude'].is_new else []
            elif isinstance(kwargs['exclude'], str):
                kwargs['exclude'] = [kwargs['exclude']]
            elif isinstance(kwargs['exclude'], (list, tuple)):
                ex = []
                for item in kwargs['exclude']:
                    if isinstance(item, _odm.Entity):
                        if not item.is_new:
                            ex.append(item.manual_ref)
                    elif isinstance(item, str):
                        ex.append(item)
                    else:
                        raise TypeError('Unsupported type: {}'.format(type(item)))

                kwargs['exclude'] = ex

            if kwargs.get('exclude_descendants', True):
                for ref in kwargs['exclude'].copy():
                    for descendant in _odm.get_by_ref(ref).descendants:
                        kwargs['exclude'].append(descendant.manual_ref)

        super().__init__(uid, **kwargs)

        self._model = kwargs.get('model')
        if not self._model:
            raise ValueError('Model is not specified')

        self._mock = _odm.dispense(self._model)

        self._caption_field = kwargs.get('caption_field')  # type: _Union[str, _Callable[[_odm.Entity], None]]
        if not self._caption_field:
            raise ValueError('Caption field is not specified')

        self._sort_field = kwargs.get('sort_field')  # type: str
        if not self._sort_field and isinstance(self._caption_field, str):
            self._sort_field = self._caption_field

        self._sort_order = kwargs.get('sort_order', _odm.I_ASC)  # type: int
        self._finder_adjust = kwargs.get('finder_adjust')  # type: _Callable[[_odm.Finder], None]
        self._caption_adjust = kwargs.get('caption_adjust')  # type: _Callable[[str], None]
        self._advanced_sort = kwargs.get('advanced_sort', True)  # type: bool

    @property
    def sort_field(self) -> str:
        return self._sort_field

    @sort_field.setter
    def sort_field(self, value: str):
        self._sort_field = value

    def set_val(self, value):
        """Set value of the widget.
        """
        if value == '':
            value = None
        elif isinstance(value, _odm.model.Entity):
            value = value.model + ':' + str(value.id)
        elif isinstance(value, _DBRef):
            value = _odm.get_by_ref(value)
            value = value.model + ':' + str(value.id)

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

        if self._caption_adjust:
            caption = self._caption_adjust(caption)

        if entity.depth:
            caption = '-' * entity.depth + ' ' + caption

        return caption

    def _build_items_tree(self, root_entities: _Iterable[_odm.Entity], _result: list = None) -> _List[_Tuple[str, str]]:
        if _result is None:
            _result = []

        for entity in root_entities:
            _result.append((entity.manual_ref, self._get_caption(entity)))
            self._build_items_tree(entity.children, _result)

        return _result

    def _get_element(self, **kwargs):
        """Render the widget
        """
        root_items = [entity for entity in self._get_finder().eq('_parent', None)]

        if self._advanced_sort and isinstance(self._mock.get_field(self._sort_field), _odm.field.String):
            rev = True if self._sort_order == _odm.I_DESC else False
            root_items = sorted(root_items, key=lambda e: _pyuca_col.sort_key(e.f_get(self._sort_field)), reverse=rev)

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
        self._caption_field = kwargs.get('caption_field')
        self._sort_field = kwargs.get('sort_field', self._caption_field)
        self._translate_captions = kwargs.get('translate_captions', False)

        if not self._model:
            raise ValueError('Model is not specified.')
        if not self._caption_field:
            raise ValueError('Caption field is not specified.')

        self._exclude = []  # type: _List[_odm.model.Entity]
        for e in kwargs.get('exclude', ()):
            self._exclude.append(_odm.get_by_ref(_odm.resolve_ref(e)))

        # Available items will be set during call to self._get_element()
        self._items = []

    @property
    def sort_field(self) -> str:
        """Get sort field.
        """
        return self._sort_field

    @sort_field.setter
    def sort_field(self, value: str):
        """Set sort field.
        """
        self._sort_field = value

    def set_val(self, value):
        """Set value of the widget.

        :param value: list[odm.models.ODMModel] | list[DBRef] | list[str]
        """

        # Single string can be received from HTML form
        if isinstance(value, str) or value is None:
            value = [value] if value else []

        if not isinstance(value, (list, tuple)):
            raise TypeError("List of entities expected as a value of the widget '{}'.".format(self.name))

        clean_val = []
        for v in value:
            if not v:
                continue

            # Check entity for existence
            entity = _odm.get_by_ref(_odm.resolve_ref(v))

            # Append entity reference as string
            if entity:
                clean_val.append(str(entity))

        return super().set_val(clean_val)

    def _get_element(self, **kwargs):
        finder = _odm.find(self._model).sort([(self._sort_field, _odm.I_ASC)])
        for entity in finder.get():
            k = str(entity)
            if k not in self._exclude:
                caption = str(entity.get_field(self._caption_field))
                if self._translate_captions:
                    caption = _lang.t(caption)
                self._items.append((k, caption))

        return super()._get_element()


class EntitySelectSearch(_widget.select.Select2):
    """Entity Select
    """

    def __init__(self, uid: str, **kwargs):
        model = kwargs.get('model')
        if not model:
            raise ValueError('Model is not specified')

        kwargs['ajax_url'] = _http_api.url('odm_ui@widget_entity_select_search', {'model': model})

        super().__init__(uid, **kwargs)

    def set_val(self, value):
        if value in (None, ''):
            return super().set_val(None)

        e = _odm.get_by_ref(value)
        if not isinstance(e, _odm.Entity):
            raise TypeError('Instance of {} expected, got {}'.format(_odm.Entity, type(e)))

        return super().set_val(e.manual_ref)

    def get_val(self) -> _Optional[_odm.Entity]:
        if not self._value:
            return None

        e = _odm.get_by_ref(self._value)
        if not isinstance(e, _odm.Entity):
            raise TypeError('Instance of {} expected, got {}'.format(_odm.Entity, type(e)))

        return e

    def _get_element(self, **kwargs):
        # In AJAX-mode Select2 doesn't contain any items,
        # but if we have selected item, it is necessary to append it
        if self._ajax_url and self._value:
            entity = _odm.get_by_ref(self._value)
            if hasattr(entity, 'odm_ui_widget_select_search_entities_title'):
                self._items.append((self._value, entity.odm_ui_widget_select_search_entities_title))
            else:
                raise ValueError("Entity '{}' does not support this operation".format(type(entity)))

        return super()._get_element()
