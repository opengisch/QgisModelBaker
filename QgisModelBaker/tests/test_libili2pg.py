from qgis.testing import start_app, unittest

start_app()
import os
import tempfile

from QgisModelBaker.libs.modelbaker.iliwrapper import ilicache
from QgisModelBaker.libs.modelbaker.iliwrapper.ili2dbconfig import BaseConfiguration


class IliCacheTest(unittest.TestCase):
    @unittest.skipIf(
        "TRAVIS" in os.environ,
        "Enable this test as soon as qgis is available on travis",
    )
    def test_refresh(self):
        config = BaseConfiguration()
        ic = ilicache.IliCache(config)
        ic.cache_path = tempfile.mkdtemp()
        ic.refresh()
