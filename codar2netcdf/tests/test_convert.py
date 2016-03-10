import os
import logging
import unittest
from decimal import Decimal
from datetime import datetime

import pytz
from codar2netcdf import CodarAsciiTotals

logger = logging.getLogger('codar2netcdf')
logger.addHandler(logging.StreamHandler())


class TestConvertTotals(unittest.TestCase):

    def setUp(self):
        self.resource = os.path.join(os.path.dirname(__file__), 'resources', 'totals.txt')
        self.empty = os.path.join(os.path.dirname(__file__), 'resources', 'empty.txt')
        self.grid_path = os.path.join(os.path.dirname(__file__), 'resources', 'totals.grid')
        self.output_path = os.path.join(os.path.dirname(__file__), 'resources', 'totals.nc')

    def test_import_ascii(self):
        w = CodarAsciiTotals(self.resource)
        assert not w.data.empty
        assert w.origin_time == datetime(2016, 2, 12, 17, 0, tzinfo=pytz.utc)
        assert w.origin_x == Decimal('-83.0045167')
        assert w.origin_y == Decimal('26.8332500')
        assert w.grid_spacing == 10000

    def test_import_empty(self):
        w = CodarAsciiTotals(self.empty)
        assert w.is_valid() is False
        assert w.data.empty

    def test_export_netcdf(self):
        w = CodarAsciiTotals(self.resource)
        w.export(self.output_path, ascii_grid=self.grid_path)
