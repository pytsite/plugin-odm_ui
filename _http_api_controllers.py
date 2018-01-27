"""PytSite Object Document Mapper UI Plugin HTTP API Controllers
"""
__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from pytsite import routing as _routing
from . import _browser


class GetRows(_routing.Controller):
    """Get browser rows
    """

    def exec(self) -> dict:
        offset = int(self.arg('offset', 0))
        limit = int(self.arg('limit', 0))
        sort_field = self.arg('sort')
        sort_order = self.arg('order')
        search = self.arg('search')
        browser = _browser.Browser(self.arg('model'))
        rows = browser.get_rows(offset, limit, sort_field, sort_order, search)

        return rows
