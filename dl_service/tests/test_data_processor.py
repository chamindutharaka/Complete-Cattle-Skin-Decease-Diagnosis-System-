import unittest
from your_module import DataProcessor

class TestDataProcessor(unittest.TestCase):
    def test_process_data(self):
        input_data = "sample input"
        expected_output = "expected output"
        processor = DataProcessor()
        self.assertEqual(processor.process(input_data), expected_output)

if __name__ == '__main__':
    unittest.main()