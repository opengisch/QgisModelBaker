from projectgenerator.libili2pg.ili2pg_config import BaseConfiguration

try:
    import qgis
    from qgis.testing import unittest, start_app
    start_app()
    from projectgenerator.libili2pg import ilicache
except ImportError:
    # As long as we don't deploy qgis on travis, there's nothing we can do... sorry
    from nose2.compat import unittest
    pass

import os
import nose2


import tempfile

class IliCacheTest(unittest.TestCase):
    @unittest.skipIf('TRAVIS' in os.environ, 'Enable this test as soon as qgis is available on travis')
    def test_refresh(self):
        config = BaseConfiguration()
        ic = ilicache.IliCache(config)
        ic.cache_path = tempfile.mkdtemp()
        ic.refresh()

if __name__ == '__main__':
    nose2.main()
