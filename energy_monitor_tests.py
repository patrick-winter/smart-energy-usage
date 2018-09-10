import unittest
from energy_monitor import EnergyMonitor, FuelType
import tkinter as tk
import datetime
from os import path

class TestBasicLoading(unittest.TestCase):

    def test_initial(self):
        print('Testing the loading methods')

        self.assertIsNotNone(self.gui)
        self.assertIsInstance(self.gui, EnergyMonitor)
        self.assertDictEqual(self.gui.data_container, {})
        self.assertDictEqual(self.gui.monthly_data, {})
        self.assertListEqual(self.gui.loaded_fuels, [])
        self.assertListEqual(self.gui.loaded_ids, [])


    def test_badfiles(self):
        print("Testing for bad file types")

        # Currently this test fails, because this file actually does exist. How could you change the
        # tests so they do actually test what they're supposed to?
        with self.assertRaises(ValueError):
            self.gui.load_file(self.working_dir + '\\resources\\thisfiledoesnotexist.csv')


    def test_correctload_single(self):
        print("Testing that when a correct single-house file is used the data is populated correctly")

        self.gui.load_file(self.working_dir + '\\resources\\test1_both_daily.csv')

        self.assertEqual(len(self.gui.loaded_ids), 1)
        self.assertEqual(self.gui.loaded_ids[0], 'test1')

        self.assertEqual(len(self.gui.loaded_fuels), 2)
        self.assertEqual(self.gui.loaded_fuels, [FuelType.electricity, FuelType.gas])

        self.assertEqual(len(list(self.gui.data_container.keys())), 4)
        first_date = datetime.date(2016, 1, 1)
        self.assertEqual(list(self.gui.data_container.keys())[0], first_date)
        self.assertEqual(self.gui.data_container[first_date], {FuelType.gas: 4.063200168,
                                                                         FuelType.electricity: 20.93194302})

    def test_badcolumn(self):
        print("Testing a file with a bad column")
        with self.assertRaises(ValueError):
            self.gui.load_file(self.working_dir + '\\resources\\houseH_both_daily_badcolumn.csv')

    def test_correctload_multiple(self):
        print("Testing that when a correct multiple-house file is used the data is populated correctly")

        self.gui.load_file(self.working_dir + '\\resources\\electricity_daily_test.csv')

        self.assertEqual(len(self.gui.loaded_ids), 4)
        self.assertEqual(self.gui.loaded_ids[0], 'house_a')

        self.assertEqual(len(self.gui.loaded_fuels), 1)
        self.assertEqual(self.gui.loaded_fuels[0], FuelType.electricity.name)

        self.assertEqual(len(list(self.gui.data_container.keys())), 4)
        first_date = datetime.date(2016, 1, 1)
        self.assertEqual(list(self.gui.data_container.keys())[0], first_date)
        self.assertEqual(self.gui.data_container[first_date], {'house_a': 5.778333712,
            'house_b': 9.80291645, 'house_c': 5.44345916, 'house_d': 8.46050336})

    def test_monthly(self):
        print("Testing that monthly data is calculated correctly")
        first_date = datetime.date(2016, 1, 1)
        self.gui.load_file(self.working_dir + '\\resources\\electricity_daily.csv')
        self.assertEqual(self.gui.monthly_data[first_date], {'house_a': 196.3179227,
            'house_b': 280.6373267, 'house_c': 205.915899, 'house_d': 326.6051785})

    def test_monthly_twoyears(self):
        print("Testing that monthly data is calculated correctly when using a file containing 2 years' worth of data")
        first_date = datetime.date(2017, 1, 1)
        self.gui.load_file(self.working_dir + '\\resources\\electricity_daily_twoyears.csv')
        self.assertEqual(self.gui.monthly_data[first_date], {'house_a': 196.3179227,
            'house_b': 280.6373267, 'house_c': 205.915899, 'house_d': 326.6051785})

    def test_monthly_partial(self):
        print("Testing that monthly data is calculated correctly when using a file containing part of a year of data")
        first_date = datetime.date(2016, 9, 1)
        self.gui.load_file(self.working_dir + '\\resources\\electricity_daily_partial.csv')
        self.assertEqual(self.gui.monthly_data[first_date], {'house_a': 206.0236047,
            'house_b': 271.7957174, 'house_c': 190.0440967, 'house_d': 321.2686383})

    def test_suppliers(self):
        print("Testing that supplier data is loaded properly")
        self.gui.load_file(self.working_dir + '\\resources\\suppliers.csv')
        self.assertEqual(self.gui.supplier_data['HouseC']['Electricity Usage Rate'], 30.55)

    def test_suppliers_extra(self):
        print("Testing that loading supplier data with an extra row throws an error")
        with self.assertRaises(ValueError):
            self.gui.load_file(self.working_dir + '\\resources\\suppliers_extrarows.csv')

    def test_suppliers_bad(self):
        print("Testing that loading supplier data with bad data throws an error")
        with self.assertRaises(ValueError):
            self.gui.load_file(self.working_dir + '\\resources\\suppliers_baddata.csv')

    def setUp(self):
        self.root = tk.Tk()
        self.gui = EnergyMonitor(self.root)
        self.working_dir = path.dirname(path.abspath(__file__))


if __name__ == '__main__':
    unittest.main()
