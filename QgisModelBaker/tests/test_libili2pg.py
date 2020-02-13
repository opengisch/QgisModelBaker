import qgis
from qgis.testing import unittest, start_app
start_app()
from QgisModelBaker.libili2db import ilicache
from QgisModelBaker.libili2db.ili2dbconfig import BaseConfiguration

import os
import tempfile


class IliCacheTest(unittest.TestCase):

    @unittest.skipIf('TRAVIS' in os.environ, 'Enable this test as soon as qgis is available on travis')
    def test_refresh(self):
        config = BaseConfiguration()
        ic = ilicache.IliCache(config)
        ic.cache_path = tempfile.mkdtemp()
        ic.refresh()
