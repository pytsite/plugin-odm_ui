# PytSite Object Document Mapper UI Plugin


## Changelog


### 4.1 (2018-10-12)

Support of `assetman-4.x`.


### 4.0 (2018-10-11)

Support of `pytsite-8.x`, `assetman-3.x`, `widget-3.x`.


### 3.24.2 (2018-09-21)

Processing empty results in entities browser fixed.


### 3.24.1 (2018-09-14)

Processing values in widgets fixed.


### 3.24 (2018-09-14)

Support of `odm-4.0`.


### 3.23 (2018-09-09)

Support of `form-4.14`.


### 3.22.1 (2018-09-07)

Form change watchdog behaviour fixed.


### 3.22 (2018-09-03)

New constructor's argument `entity_title_args` added in
`widget.EntitySelectSearch`.


### 3.21 (2018-09-02)

New public property `widget.EntitySelectSearch.model`.


### 3.20 (2018-09-01)

Support of `widget-2.15`.


### 3.19.1 (2018-08-29)

Forms names fixed.


### 3.19 (2018-08-28)

- Support of `widget-2.13` in `widget.EntitySelectSearch` added.
- Property `UIEntity.odm_ui_widget_select_search_entities_title` is a
method now.


### 3.18.1 (2018-08-15)

Processing arguments in `Browser` fixed.


### 3.18 (2018-08-10)

Meta titles is now set by forms setup code.


### 3.17 (2018-08-09)

Support for `Browser`'s constructor arguments to specify router's rules
names.


### 3.16 (2018-08-09)

Support of `odm_auth-1.9`.


### 3.15 (2018-08-08)

Support of `form-4.12`.


### 3.14 (2018-07-30)

Support of `form-4.8`.


### 3.13 (2018-07-29)

- Changed form closing confirmation added.
- Support of `form-4.7`.


### 3.12.3 (2018-07-22)

Form icons fix.


### 3.12.2 (2018-07-22)

Form icons fix.


### 3.12.1 (2018-07-21)

Support of Twitter Bootstrap 4 fixed.


### 3.12 (2018-07-07)

Support of `form-4.4`.


### 3.11 (2018-06-24)

Support of `odm_auth-1.8`.


### 3.10 (2018-06-07)

Support of `auth_ui-3.5`.


### 3.9 (2018-06-03)

`EntitySelect` and `EntityCheckboxes` widgets refactored.


### 3.8.1 (2018-05-31)

`widget.EntitySelectSearch` fixed.


### 3.8 (2018-05-30)

New widget `EntitySelectSearch`.


### 3.7 (2018-05-28)

Support of `pytsite-7.22`.


### 3.6 (2018-05-28)

Support of `odm-3.6`.


### 3.5.2 (2018-05-26)

Sorting issues fixed in `widget.EntitySelect`.


### 3.5.1 (2018-05-26)

Type hinting fixed.


### 3.5 (2018-05-26)

Support `caption_field` as a callable in `widget.EntitySelect`.


### 3.4.1 (2018-05-13)

Forms titles issue fixed.


### 3.4 (2018-05-06)

Support of `form-4.0` and `pytsite-7.17`.


### 3.3.1 (2018-04-26)

Forms title setting fixed.


### 3.3 (2018-04-25)

Support of `form-3.0`.


### 3.2.5 (2018-04-15)

Removed unecessary redirect in modify form initialization.


### 3.2.4 (2018-04-15)

Processing of request args by mass action forms fixed.


### 3.2.3 (2018-04-15)

Browser's toolbar's delete button presense fixed.


### 3.2.2 (2018-04-15)

Router rules argument names fixed.


### 3.2.1 (2018-04-15)

- Router rules argument names fixed.
- Metatags set fixed.


### 3.2 (2018-04-15)

- Previously added properties removed.
- Minor issues fixed.


### 3.1 (2018-04-14)

Three properties added to `Browser`.


### 3.0.2 (2018-04-14)

Exception detals fixed.


### 3.0.1 (2018-04-14)

`plugin.json` fixed.


### 3.0 (2018-04-14)

- Admin router's rules renamed.
- Entities forms and browser refactored.
- `UIEntity`'s methods mess eliminated.


### 2.3 (2018-04-12)

- New API functions: `dispense_entity()`, `get_browser()`.
- Entities browser rendering fixed.


### 2.2.1 (2018-04-10)

Forms processing issues fixed.


### 2.2 (2018-04-10)

Way of processing modify forms changed.


### 2.1.1 (2018-04-09)

Performance issue fixed.


### 2.1 (2018-04-09)

New constructor's argument in `widget.EntitySelect`: `advanced_sort`.


### 2.0 (2018-04-06)

Support for `odm-2.0`.


### 1.10 (2018-04-04)

Support for `form-2.3`.


### 1.9.1 (2018-03-18)

Permissions checking fixed.


### 1.9 (2018-03-15)

Support for `form-2.0` and `widget-1.6`.


### 1.8.9 (2018-03-09)

- Improper code in `Browser.default_sort_field` property fixed.
- Form's `redirect` property improper usage fixed.


### 1.8.8 (2018-03-07)

"Actions' column visibility conditions fixed.


### 1.8.7 (2018-03-05)

Entity state checking fixed in `widget.EntitySelect`.


### 1.8.6 (2018-03-05)

Typo fixed.


### 1.8.5 (2018-03-05)

Entity state checking fixed in `widget.EntitySelect`.


### 1.8.4 (2018-03-05)

Argument `exclude_descendants` of `widget.EntitySelect`'s constructor
is now `True` by default.


### 1.8.3 (2018-02-27)

`Browser.remove_data_field()` method restored.


### 1.8.2 (2018-02-27)

Version number fixed.


### 1.8.1 (2018-02-27)

Rows count checking issue fixed.


### 1.8 (2018-02-27)

Support for entity trees.


### 1.7.1 (2018-02-13)

Fixed browser's permissions issue.


### 1.7 (2018-02-12)

- Support for dictionary-based data fields in `Browser`.
- New event `'odm_ui@browser_row.{model}` added.
- JS and CSS fixed.


### 1.6.1 (2018-02-12)

Typo fixed.


### 1.6 (2018-02-11)

- Support for `pytsite-7.9`.
- New event `odm_ui@browser_setup.{model}` added.


### 1.5.1 (2018-01-29)

Missing authentication step fixed.


### 1.5 (2018-01-27)

Support for `admin-1.3`, `auth-1.8`.


### 1.4 (2018-01-12)

Support for `odm-1.4`.


### 1.3 (2018-01-02)

Events names refactoring.


### 1.2.2 (2017-12-21)

Init code refactored.


### 1.2.1 (2017-12-20)

Init code refactored.


### 1.2 (2017-12-13)

Support for `pytsite-7.0`.


### 1.1 (2017-12-02)

Support for `pytsite-6.1`.


### 1.0.1 (2017-11-27)

Fixed import.


### 1.0 (2017-11-25)

First release.
