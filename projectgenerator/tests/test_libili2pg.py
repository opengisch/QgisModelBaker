import qgis
import nose2
import os
from qgis.testing import unittest, start_app

start_app()

from projectgenerator.libili2pg import ilicache
import tempfile

class IliCacheTest(unittest.TestCase):
    @unittest.skipIf('TRAVIS' in os.environ)
    def test_refresh(self):
        ic = ilicache.IliCache()
        ic.cache_path = tempfile.mkdtemp()
        ic.refresh()

if __name__ == '__main__':
    nose2.main()
