import nose2
from qgis.testing import unittest
import yaml

from QgisModelBaker.yamltools.loader import InheritanceLoader


class YamlInheritanceTest(unittest.TestCase):

    def test_inheritance(self):
        document = """
          base_object: &base_object
            list:
              - map1: x
                map2: b
              - def
              - ghi
            base: 4

          project:
            <<<: *base_object
            list:
              - zzz: 5
            extra: 7
        """

        data = yaml.load(document, Loader=InheritanceLoader)
        expected = {
            'base': 4,
            'extra': 7,
            'list': [
                {'zzz': 5},
                {'map1': 'x',
                 'map2': 'b'},
                'def',
                'ghi'
            ]
        }

        self.assertEqual(expected, data['project'])


if __name__ == '__main__':
    nose2.main()
