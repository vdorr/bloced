
import unittest
import core

class TestBasics(unittest.TestCase):

#	def setUp(self):
#		pass

	def test_create_block_factory(self) :
		factory_instance = core.create_block_factory(scan_dir="library")
		factory_instance2 = core.create_block_factory(scan_dir="library")
		self.assertEqual(factory_instance, factory_instance2)#is singleton
#		self.assertRaises(TypeError, random.shuffle, (1,2,3))


if __name__ == '__main__':
	unittest.main()

