from ceph_salt.salt_utils import GrainsManager
from . import SaltMockTestCase


class GrainsManagerTest(SaltMockTestCase):

    def setUp(self):
        super(GrainsManagerTest, self).setUp()
        GrainsManager.set_grain('test', 'key', 'value')

    def test_grains_set(self):
        self.assertGrains('test', 'key', 'value')

    def test_grains_get(self):
        value = GrainsManager.get_grain('test', 'key')
        self.assertDictEqual(value, {'test': 'value'})

