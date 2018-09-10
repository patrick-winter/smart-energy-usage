import csv
import datetime
import math
import tkinter as tk
from collections import OrderedDict
from enum import Enum
from ntpath import basename
from os import path
from tkinter import *
from tkinter import filedialog
from tkinter import scrolledtext

import plotly
import plotly.graph_objs as go


# We have an enum defined here so we can use it instead of the strings 'gas' and 'electricity'
# Enums essentially reserve a few named types that are bound to fixed values. They are useful
# as they can be compared reliably, and the list of values in the Enum can be looped over as well
class FuelType(Enum):
    electricity = 1
    gas = 2


MONTHS = ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')

def round_1sf(number):
    return round(number, -int(math.floor(math.log10(number))))

def is_num(string):
    for i in range(len(string)):
        if not (string[i:i+1].isnumeric() or string[i:i+1] == "."):
            return False
    return True


def merge(list1, list2):
    i1 = 0
    i2 = 0
    output = []
    while i1 < len(list1) and i2 < len(list2):
        if list1[i1] < list2[i2]:
            output.append(list1[i1])
            i1 += 1
        else:
            output.append(list2[i2])
            i2 += 1
    while i1 < len(list1):
        output.append(list1[i1])
        i1 += 1
    while i2 < len(list2):
        output.append(list2[i2])
        i2 += 1
    return output

def merge_sort(data):
    if len(data) == 1:
        return data
    list1 = data[0:int(len(data)/2)]
    list2 = data[int(len(data)/2):(len(data))]
    return merge(merge_sort(list1), merge_sort(list2))

def mean(data):
    total = 0
    for i in data:
        total += i
    return total / len(data)

def quartiles(data):
    data = merge_sort(data)
    size = len(data)
    indices = [(size-3)/4, (size-1)/2, (3*size-1)/4]
    output = []
    for i in indices:
        lower = int(i)
        output.append(data[lower] + (i-lower) * (data[lower + 1] - data[lower]))
    return output

def std_dev(data):
    avg = mean(data)
    total = 0
    for i in data:
        total += math.pow(i - avg, 2)
    return math.sqrt(total / len(data))

def skew(data):
    n = len(data)
    if n<=2:
        return 0
    avg = mean(data)
    std = std_dev(data)
    total = 0
    for i in data:
        total += math.pow((i - avg) / std, 3)
    return total * n / (n - 1) / (n - 2)

def kurtosis(data):
    n = len(data)
    if n<=3:
        return 0
    avg = mean(data)
    std = std_dev(data)
    total = 0
    for i in data:
        total += math.pow((i-avg)/std, 4)
    total *= n*(n+1)/(n-1)/(n-2)/(n-3)
    total -= 3*(n-1)*(n-1)/(n-2)/(n-3)
    return total

'''
This file is written as a class, meaning it is defined using the 'class' keyword. Practically, 
the file is a fairly linear collection of functions, so this doesn't differ much from a linear
script. The main difference is that variables are prefixed with 'self.' and are referred to
as 'fields'. Functions are referred to as 'methods', and are called using an instance of the 
class they belong to, in this case EnergyMonitor. Methods are also prefixed with 'self.' 
when called inside other methods in the class. 
'''


# noinspection PyTypeChecker,PyUnusedLocal
class EnergyMonitor:

    """
    The init method is called when a class is instantiated. In this case the init method
    is creating some data structures, and creating the Tkinter widgets needed to display the
    UI correctly.
    """
    def __init__(self, parent):
        self.parent = parent

        '''
        These two data structures are a special Python type called OrderedDict. In a normal Python
        dict, the keys accessed from this structure can be in any order, however an OrderedDict
        remembers the order in which keys are added. This will be important later on, since these
        two structures may hold keys that are dates in order, meaning that the order needs to be
        maintained. These structures can be accessed from anywhere within the class, similar to
        global variables, but without the need to declare them 'global'.
        '''
        self.data_container = OrderedDict()
        self.monthly_data = OrderedDict()
        self.supplier_data = OrderedDict()
        self.metrics = OrderedDict()
        self.annual_costs = OrderedDict()
        self.monthly_costs = OrderedDict()
        self.loaded_ids = []
        self.loaded_fuels = []
        self.loaded_ids_sup = []

        self.welcome_label = tk.Label(self.parent, text='Welcome to the Energy Monitor!', font=('Calibri', 32))
        self.welcome_label.configure(background='#c6e2ff')
        self.welcome_label.pack()

        self.message_label = tk.Label(self.parent, text='Please use the dialog below to load a CSV file, which will be displayed ' +
                                          'in the box below.', font=('Calibri', 14), wraplength=540)
        self.message_label.configure(background='#c6e2ff')
        self.message_label.pack(pady=5)

        self.btn_file = tk.Button(self.parent, text="Load file", command=self.load_file)
        self.btn_file.pack(pady=5)

        self.scrolled_text = tk.scrolledtext.ScrolledText(self.parent, width=110, height=10)
        self.scrolled_text.pack()

        self.metric_text = tk.scrolledtext.ScrolledText(self.parent, width = 110, height = 7)

        self.btn_graph = tk.Button(self.parent, text='Plot Graph', command=self.plot_graph)
        self.btn_graph.forget()
        self.chart_type = StringVar(self.parent)
        self.chart_type.set('bar')
        self.chart_menu = OptionMenu(self.parent, self.chart_type, 'bar', 'scatter')
        self.chart_scope = StringVar(self.parent)
        self.chart_scope.set('daily')
        self.scope_menu = OptionMenu(self.parent, self.chart_scope, 'daily', 'monthly')
        self.house_selected = StringVar(self.parent)
        self.house_selected.set('one')
        self.metric_label = tk.Label(self.parent, text='Select a data set to view metrics for:', font=('Calibri', 10), wraplength=540)
        self.metric_label.configure(background='#c6e2ff')
        self.dropdown = OptionMenu(self.parent, self.house_selected, 'one', 'two', 'three')
        self.status_label = tk.Label(self.parent, text="", font=('Calibri', 8))
        self.costs_checked = StringVar(self.parent)
        self.costs_checked.set('Show usage')
        self.costs_menu = tk.OptionMenu(self.parent, self.costs_checked, 'Show usage', 'Show costs')
        self.costs_menu.forget()
        self.btn_distr_graph = tk.Button(self.parent, text='Distribution Graph',
                                          command=self.distribution_graph_multi)
        self.graph_size = StringVar(self.parent)
        self.graph_size.set('10,000 points')
        self.graph_size_menu = OptionMenu(self.parent, self.graph_size, '1,000 points', '10,000 points', '50,000 points', '100,000 points', '200,000 points', '500,000 points', '1,000,000 points')
        self.graph_size_menu.forget()
        self.btn_distr_graph.forget()
        self.btn_pie = tk.Button(self.parent, text='Pie Chart',
                                          command=self.pie_chart)
        self.btn_pie.forget()
        self.total_mode = StringVar(self.parent)
        self.total_menu = tk.OptionMenu(self.parent, self.total_mode, 'Show fuels separately', 'Show totals')
        self.total_mode.set('Show fuels separately')
        self.total_menu.forget()

        self.start_year = IntVar()
        self.end_year = IntVar()
        self.start_month = IntVar()
        self.end_month = IntVar()
        self.start_day = IntVar()
        self.end_day = IntVar()
        self.start_year_text = tk.Entry(self.parent, textvariable=self.start_year)
        self.end_year_text = tk.Entry(self.parent, textvariable=self.end_year)
        self.start_month_text = tk.Entry(self.parent, textvariable=self.start_month)
        self.end_month_text = tk.Entry(self.parent, textvariable=self.end_month)
        self.start_day_text = tk.Entry(self.parent, textvariable=self.start_day)
        self.end_day_text = tk.Entry(self.parent, textvariable=self.end_day)
        self.date_label = tk.Label(self.parent, text="Enter start and end dates for graphs(dd/mm/yyyy):")

# Displays an error message in the GUI to notify the user.
    def display_error(self, error_message):
        self.status_label.place_forget()
        self.status_label = tk.Label(self.parent, text=error_message, font=('Calibri', 8))
        self.status_label.configure(foreground='#ff0000', background='#c6e2ff')
        self.status_label.place(x=300, y=700)
        raise ValueError(error_message)

# Displays a status message in the GUI (as opposed to in the console)
    def display_status(self, status):
        self.status_label.place_forget()
        self.status_label = tk.Label(self.parent, text=status, font=('Calibri', 8))
        self.status_label.configure( background='#c6e2ff')
        self.status_label.place(x=300, y=700)

# Sets the text to be displayed in the scroll window
    def scroll_text(self, scrtext):
        self.scrolled_text.insert(tk.INSERT, scrtext)
        self.scrolled_text.pack()


    '''
    This method is called when the button 'btn_file' in the init method is clicked. This is 
    achieved using the 'command=...' syntax used when defining the button.
    This method is designed to query the user for a file to load into the application. 
    This file is loaded into the application, it is checked for correct formatting, then to
    ensure that it contains valid data. If these checks are successful, the data in the file
    is then loaded into the data_storage dictionary defined in the 'init' method. The data is 
    inserted into this dictionary using the data of each entry as the key. Depending on how far
    through the project you are, the data being loaded will be for either one house or multiple
    houses. This means that the value stored into the 'data_container' dictionary for each date
    will most likely be another dictionary. This will store, for each date, the usage data 
    for every house in the file, or the type of fuel (if only loading a 1ouse file)
    '''

    # noinspection PyTypeChecker
    def load_file(self, file=None):
        if file is None:
            file = filedialog.askopenfilename(initialdir=path.dirname(__file__))
        elif not path.isfile(file):
            # Here we are raising an Error. Within Python this means that the application
            # cannot recover the state of the application, and it should not continue processing.
            # Since this application runs in a HUI loop, the program will not actually close,
            # but it will not be able to do further processing.
            self.display_error("This file does not exist or is not readable.")

        # This is a regular expression, essentially a form of pattern-matching that will
        # allow us to check that the file name of the loaded file is in the correct format.
        # For more information about regular expressions, see https://www.learnpython.org/en/Regular_Expressions
        re_single_house = re.compile('^(.*?)_both_daily')
        re_multiple_houses = re.compile('^(gas|electricity)_daily')
        re_suppliers = re.compile('suppliers')

        filename = basename(file).split('.')[0]
        single_match = re_single_house.search(filename)
        multiple_match = re_multiple_houses.search(filename)
        # noinspection PyTypeChecker
        supplier_match = re_suppliers.search(filename)

        '''
        Here we are checking whether or not the file is a single or multiple house file. 
        '''
        data = {}
        if single_match is not None:
            self.process_single_file(file, single_match.group(1))
        elif multiple_match is not None:
            self.process_multiple_file(file, FuelType[multiple_match.group(1)].name)
        elif supplier_match is not None:
            self.process_supplier_file(file)
        else:
            self.display_error("File format is not correct, must be one of {fuel-type}_daily.csv, {house-id}_both_daily.csv or suppliers.csv")
        if single_match is not None or multiple_match is not None:
            self.generate_monthly_data()
            self.btn_graph.place(x=300, y=400, width=80, height=30)
            self.chart_menu.place(x=400, y=400, width=80, height=30)
            self.scope_menu.place(x=500, y=400, width=80, height=30)
            start = list(self.data_container.keys())[0]
            end = list(self.data_container.keys())[len(list(self.data_container.keys())) - 1]
            self.start_year.set(start.year)
            self.start_month.set(start.month)
            self.start_day.set(start.day)
            self.end_year.set(end.year)
            self.end_month.set(end.month)
            self.end_day.set(end.day)
            self.date_label.place(x=100, y=330)
            self.date_label.configure(background='#c6e2ff')
            self.start_year_text.place(x=420, y=330, width=40)
            self.start_month_text.place(x=400, y=330, width=20)
            self.start_day_text.place(x=380, y=330, width=20)
            self.end_year_text.place(x=510, y=330, width=40)
            self.end_month_text.place(x=490, y=330, width=20)
            self.end_day_text.place(x=470, y=330, width=20)
        if len(self.loaded_fuels) == 1:
            self.generate_metrics()
        intersection = list(set(self.loaded_ids).intersection(self.loaded_ids_sup)) # Only calculate costs for houses with both supplier and usage data
        if len(intersection) != 0:
            self.calculate_costs(intersection)
            self.costs_menu.place(x=600, y=400, width=100, height=30)
        else:
            self.costs_menu.place_forget()

    def get_start(self):
        day = self.start_day.get()
        month = self.start_month.get()
        year = self.start_year.get()
        date = datetime.date(year, month, day)
        if date < list(self.data_container.keys())[0]:
            self.display_error("Start date is before the start of the data set!")
        return date

    def get_end(self):
        day = self.end_day.get()
        month = self.end_month.get()
        year = self.end_year.get()
        date = datetime.date(year, month, day)
        if date > list(self.data_container.keys())[len(list(self.data_container.keys()))-1]:
            self.display_error("End date is after the end of the data set!")
        if date < self.get_start():
            self.display_error("End date is before start date!")
        return date

    def calculate_costs(self, ids):
        self.annual_costs.clear()
        self.monthly_costs.clear()
        if len(self.loaded_fuels) > 1 and len(ids) == 1:
            i = ids[0]
            for d in list(self.data_container.keys()):
                self.annual_costs[d] = {}
                self.monthly_costs[d] = {}
                base = self.supplier_data[i]['Electricity Standing Charge']
                var = self.supplier_data[i]['Electricity Usage Rate']
                self.annual_costs[d][FuelType.electricity] = round(self.data_container[d][FuelType.electricity] * var + base, 0) / 100
                base = self.supplier_data[i]['Gas Standing Charge']
                var = self.supplier_data[i]['Gas Usage Rate']
                self.annual_costs[d][FuelType.gas] = round(self.data_container[d][FuelType.gas] * var + base, 0) / 100
                monthstart = datetime.date(d.year, d.month, 1)
                if d.day == 1:
                    self.monthly_costs[monthstart][FuelType.electricity] = self.annual_costs[d][FuelType.electricity]
                    self.monthly_costs[monthstart][FuelType.gas] = self.annual_costs[d][FuelType.gas]
                else:
                    self.monthly_costs[monthstart][FuelType.electricity] += self.annual_costs[d][FuelType.electricity]
                    self.monthly_costs[monthstart][FuelType.gas] += self.annual_costs[d][FuelType.gas]
        else:
            for d in list(self.data_container.keys()):
                self.annual_costs[d] = {}
                self.monthly_costs[d] = {}
                for i in ids:
                    base = 0
                    var = 0
                    if self.loaded_fuels[0] == 'electricity':
                        base = self.supplier_data[i]['Electricity Standing Charge']
                        var = self.supplier_data[i]['Electricity Usage Rate']
                    else:
                        base = self.supplier_data[i]['Gas Standing Charge']
                        var = self.supplier_data[i]['Gas Usage Rate']
                    self.annual_costs[d][i] = round(self.data_container[d][i] * var + base, 0) / 100
                    monthstart = datetime.date(d.year, d.month, 1)
                    if d.day == 1:
                        self.monthly_costs[monthstart][i] = self.annual_costs[d][i]
                    else:
                        self.monthly_costs[monthstart][i] += self.annual_costs[d][i]


    def process_supplier_file(self, file):
        self.scrolled_text.delete(1.0, tk.END)
        self.supplier_data.clear()
        with open(file, 'r') as file_contents:
            reader = csv.reader(file_contents)
            header = next(reader, None)
            if header[0].lower() != "data type":
                self.display_error("First heading should be 'Data Type'")
            for h in header:
                if h != "Data Type":
                    self.supplier_data[h] = {}
                    self.loaded_ids_sup.append(h)
                self.scroll_text("{:22.20}".format(h))
            count = 0
            for row in reader:
                count += 1
                self.scroll_text("\n" + "{:22.20}".format(row[0]))
                if len(row) - 1 != len(list(self.supplier_data.keys())):
                    self.display_error("Row contains wrong number of values")
                for i in range(0, len(list(self.supplier_data.keys()))):
                    if count == 1:
                        self.supplier_data[list(self.supplier_data.keys())[i]][row[0]] = row[i+1]
                    else:
                        if not is_num(row[i+1]):
                            self.display_error("Data not numeric")
                        self.supplier_data[list(self.supplier_data.keys())[i]][row[0]] = float(row[i+1])
                    self.scroll_text("{:22.20}".format(row[i+1]))
            if count != 5:
                self.display_error("File should contain header plus 5 rows of data")
    '''
    This method is a specific case from the above load method, which was capable of checking for different
    types of files. This method is specifically for dealing with one house files, which contain 
    both gas and electricity data for one house. The output of the method is to populate data_container
    with the relevant data, once it has been validated. 
    '''
    def process_single_file(self, file, house_id):

        '''
        Since this is a GUI application, the user can click the 'Load File' button as many
        times as they wish. So, when processing a new file, we need a way to clear out the data
        from any previous files.
        '''
        self.data_container.clear()
        self.loaded_ids.clear()
        self.loaded_fuels.clear()
        self.scrolled_text.delete(1.0, tk.END)

        with open(file, 'r') as file_contents:
            '''
            Here we open the user's file, then use it to create a CSV Reader object, which will
            be able to access rows in the file as if they were standard Python arrays. This 
            reduces the complexity of parsing the file significantly, and also allows checking for 
            invalid files, by easily checking the number of elements in each row, for example. 
            '''
            reader = csv.reader(file_contents)
            header = next(reader, None)

            # Since this method only deals with single house files, we can check for these values
            # But - could we use the enum defined at the top of this file somehow?
            if header[0].lower() != 'date' or header[1].lower() != FuelType(1).name or header[2].lower() != FuelType(2).name:
                self.display_error('File is not in correct format. First column must be electricity, second must be gas.')

            self.scroll_text("Date       Electricity         Gas\n")
            for row in reader:

                # This line creates a datetime object, which is a Python object containing
                # a valid date. It allows us to make date-aware calculations, such as evaluating
                # whether some dates are higher or lower than each other. It should also allow
                # us to use date arithemtic, if we need to.
                this_date = datetime.datetime.strptime(row[0], '%Y%m%d').date()

                # Here, we are inserting data into the data_container structure for the current
                # row. What this line is actually doing, using the '{}' notations, is creating
                # a 3-level dictionary. The first level is the data_container dictionary,
                # which uses a date as its key. The next level is a dictionary with a single key:
                # the house_id. This might seem more complex than needed, could this code be simplified?
                # What else would need to change? The 3rd level dictionary is the FuelType names.
                # These are used so that the different fuel types can be easily fetched, given a
                # date and a house_id.
                self.data_container[this_date] = {FuelType.electricity: float(row[1]),
                                                             FuelType.gas: float(row[2])}
                self.scroll_text("{:%Y/%m/%d}".format(this_date) + "{:12.5f}".format(float(row[1]))
                                                                 + "{:12.5f}".format(float(row[2])) + "\n")

            # Since we have only loaded one file, set the id directly
            self.loaded_ids.append(house_id)
            self.loaded_fuels.extend([FuelType.electricity, FuelType.gas])
            self.display_status("House loaded: " + house_id + ". Fuels loaded: " + FuelType.electricity.name + ", " + FuelType.gas.name + ".")
            self.btn_pie.place_forget()
            self.metric_label.place_forget()
            self.dropdown.place_forget()
            self.metric_text.place_forget()
            self.graph_size_menu.place_forget()
            self.btn_distr_graph.place_forget()
            self.total_menu.place(x=720, y=400, width=150, height=30)

    def process_multiple_file(self, file, fuel_id):
        self.data_container.clear()
        self.loaded_ids.clear()
        self.loaded_fuels.clear()
        self.scrolled_text.delete(1.0, tk.END)

        with open(file, 'r') as file_contents:
            reader = csv.reader(file_contents)
            header = next(reader, None)

            if header[0].lower() != 'date':
                self.display_error('File is not in correct format.')

            message = "Houses loaded: "
            self.scroll_text("Date      ")
            for i in range(1, len(header)):
                self.loaded_ids.append(header[i])
                if i > 1:
                    message += ", "
                message += header[i]
                self.scroll_text("{:>12}".format(header[i]))
            self.loaded_fuels.append(fuel_id)
            self.scroll_text("\n")

            for row in reader:
                this_date = datetime.datetime.strptime(row[0], '%Y%m%d').date()
                self.data_container[this_date] = {}
                self.scroll_text("{:%Y/%m/%d}".format(this_date))
                for i in range(1, len(header)): # The second index of the dictionary is the house
                    self.data_container[this_date][header[i]] = float(row[i])
                    self.scroll_text("{:12.5f}".format(float(row[i])))
                self.scroll_text("\n")

            self.display_status(message + ". Fuel loaded: %s." % fuel_id)
            self.btn_pie.place(x=300, y=430, width=80, heigh=30)
            self.total_menu.place_forget()

    def generate_monthly_data(self):
        self.monthly_data.clear()
        month_total = {}
        for date in list(self.data_container.keys()):
            if len(self.loaded_ids) == 1:
                for fuel in self.loaded_fuels:
                    if date.day == 1:
                        month_total[fuel] = self.data_container[date][fuel]
                    else:
                        month_total[fuel] = round(month_total[fuel] + self.data_container[date][fuel], 7)
            else:
                for house in self.loaded_ids:
                    if date.day == 1:
                        month_total[house] = self.data_container[date][house]
                    else:
                        month_total[house] = round(month_total[house] + self.data_container[date][house], 7)
            if date.month != (date + datetime.timedelta(days=1)).month:  # Last day of month
                self.monthly_data[datetime.date(date.year, date.month, 1)] = month_total
                month_total = {}

    def calc_metrics(self, data, key):
        self.metrics[key]['Mean usage: '] = round(mean(data), 5)
        qs = quartiles(data)
        self.metrics[key]['Lower Quartile: '] = round(qs[0], 5)
        self.metrics[key]['Median: '] = round(qs[1], 5)
        self.metrics[key]['Upper quartile: '] = round(qs[2], 5)
        self.metrics[key]['Interquartile range: '] = round(qs[2] - qs[0], 5)
        self.metrics[key]['Standard Deviation: '] = round(std_dev(data), 5)
        self.metrics[key]['Skewness: '] = round(skew(data), 5)
        self.metrics[key]['Kurtosis: '] = round(kurtosis(data), 5)
        self.metrics[key]['rawdata'] = data

    def generate_metrics(self):
        self.metrics.clear()
        keys = []
        alldata = []
        if len(self.loaded_fuels) == 1:
            keys = self.loaded_ids
            self.metrics['all'] = {}
            self.metrics['all']['Minimum usage: '] = sys.float_info.max
            self.metrics['all']['Minimum used on: '] = list(self.data_container.keys())[0]
            self.metrics['all']['Minimum used by: '] = self.loaded_ids[0]
            self.metrics['all']['Maximum usage: '] = 0
            self.metrics['all']['Maximum used on: '] = list(self.data_container.keys())[0]
            self.metrics['all']['Maximum used by: '] = self.loaded_ids[0]
        else:
            keys = self.loaded_fuels
        for i in keys:
            self.metrics[i] = {}
            data=[]
            self.metrics[i]['Minimum usage: '] = sys.float_info.max
            self.metrics[i]['Maximum usage: '] = 0
            self.metrics[i]['Minimum used on: '] = list(self.data_container.keys())[0]
            self.metrics[i]['Maximum used on: '] = list(self.data_container.keys())[0]
            for date in list(self.data_container.keys()):
                data.append(self.data_container[date][i])
                if self.data_container[date][i] > self.metrics[i]['Maximum usage: ']:
                    self.metrics[i]['Maximum usage: '] = round(self.data_container[date][i], 5)
                    self.metrics[i]['Maximum used on: '] = date
                if self.data_container[date][i] < self.metrics[i]['Minimum usage: ']:
                    self.metrics[i]['Minimum usage: '] = round(self.data_container[date][i], 5)
                    self.metrics[i]['Minimum used on: '] = date
                if len(self.loaded_fuels) == 1:
                    alldata.append(self.data_container[date][i])
                    if self.data_container[date][i] > self.metrics['all']['Maximum usage: ']:
                        self.metrics['all']['Maximum usage: '] = round(self.data_container[date][i], 5)
                        self.metrics['all']['Maximum used on: '] = date
                        self.metrics['all']['Maximum used by: '] = i
                    if self.data_container[date][i] < self.metrics['all']['Minimum usage: ']:
                        self.metrics['all']['Minimum usage: '] = round(self.data_container[date][i], 5)
                        self.metrics['all']['Minimum used on: '] = date
                        self.metrics['all']['Minimum used by: '] = i
            self.metrics[i]['Minimum monthly usage: '] = sys.float_info.max
            self.metrics[i]['Maximum monthly usage: '] = 0
            self.metrics[i]['Minimum month: '] = ""
            self.metrics[i]['Maximum month: '] = ""
            for month in list(self.monthly_data.keys()):
                if self.monthly_data[month][i] > self.metrics[i]['Maximum monthly usage: ']:
                    self.metrics[i]['Maximum monthly usage: '] = round(self.monthly_data[month][i], 5)
                    self.metrics[i]['Maximum month: '] = MONTHS[month.month - 1] + " " + str(month.year)
                if self.monthly_data[month][i] < self.metrics[i]['Minimum monthly usage: ']:
                    self.metrics[i]['Minimum monthly usage: '] = round(self.monthly_data[month][i], 5)
                    self.metrics[i]['Minimum month: '] = MONTHS[month.month - 1] + " " + str(month.year)
            self.calc_metrics(data, i)
        if len(self.loaded_fuels) == 1:
            self.calc_metrics(alldata, 'all')
        self.dropdown.place_forget()
        self.metric_label.place(x=300, y=460)
        self.dropdown = OptionMenu(self.parent, self.house_selected, *list(self.metrics.keys()), command=self.display_metrics)
        self.house_selected.set(list(self.metrics.keys())[0])
        self.dropdown.place(x=400, y=480)
        self.btn_distr_graph.place(x=300, y=650, width=120)
        self.graph_size_menu.place(x=450, y=650, width=120)

    def display_metrics(self, event):
        self.metric_text.delete(1.0, tk.END)
        key = self.house_selected.get()
        lines = []
        for m in list(self.metrics[key].keys()):
            if m != "rawdata":
                lines.append("{:35.35}".format(m + str(self.metrics[key][m])))
        rows = int(math.ceil(len(lines) / 3))
        for i in range(rows):
            line = lines[i] + lines[i+rows]
            if i+2*rows < len(lines):
                line += lines[i+2*rows]
            self.metric_text.insert(tk.INSERT, line + "\n")
        self.metric_text.place(x=50, y=520)

    def plot_graph(self):
        data = {}
        ids = []
        fuels = self.loaded_fuels
        traces = []
        title = ""
        start = self.get_start()
        end = self.get_end()
        if self.costs_checked.get() == 'Show costs':
            ids = list(set(self.loaded_ids).intersection(self.loaded_ids_sup))
            title = " Costs (£)"
            if self.chart_scope.get() == 'monthly':
                data = self.monthly_costs
            else:
                data = self.annual_costs
        else:
            ids = self.loaded_ids
            title = " Usage (kWh)"
            if self.chart_scope.get() == 'monthly':
                data = self.monthly_data
            else:
                data = self.data_container
        date_range = []
        for d in list(data.keys()):
            if d >= start and d <= end:
                date_range.append(d)
        if len(fuels) == 1: # Multiple houses
            graph_data = {}
            for house in ids:
                graph_data[house] = []
            if self.chart_scope.get() == 'monthly':
                x_axis = []
                for date in date_range:
                    if date.day == 1:
                        for house in ids:
                            graph_data[house].append(data[date][house])
                        x_axis.append(MONTHS[date.month - 1] + " " + str(date.year))

            else:
                x_axis = date_range
                for date in date_range:
                    for house in ids:
                        graph_data[house].append(data[date][house])

            for house in ids:
                if self.chart_type.get() == 'scatter':
                    traces.append(go.Scatter(x=x_axis,y=graph_data[house],name=house))
                else:
                    traces.append(go.Bar(x=x_axis,y=graph_data[house],name=house))

            layout = go.Layout(title='Multiple Houses ' + fuels[0] + ' only ' + self.chart_scope.get(), yaxis=dict(title=title))

        else: # Single house
            if self.chart_scope.get() == 'monthly':
                graph_data = {FuelType.gas: [], FuelType.electricity: []}
                x_axis = []
                totals = []
                for date in date_range:
                    if date.day == 1:
                        graph_data[FuelType.gas].append(data[date][FuelType.gas])
                        graph_data[FuelType.electricity].append(data[date][FuelType.electricity])
                        x_axis.append(MONTHS[date.month - 1] + " " + str(date.year))
                        if self.total_mode.get() == 'Show totals':
                            totals.append(data[date][FuelType.gas]+data[date][FuelType.electricity])
                if self.total_mode.get() == 'Show totals':
                    if self.chart_type.get() == 'scatter':
                        gas_trace = go.Scatter(x=x_axis,y=graph_data[FuelType.gas],name='gas trace')
                        electricity_trace = go.Scatter(x=x_axis,y=graph_data[FuelType.electricity],name='electricity trace')
                        total_trace = go.Scatter(x=x_axis,y=totals,name='total trace')
                        traces = [gas_trace, electricity_trace, total_trace]
                    else:
                        gas_trace = go.Bar(x=x_axis,y=graph_data[FuelType.gas],name='gas trace')
                        electricity_trace = go.Bar(x=x_axis,y=graph_data[FuelType.electricity],name='electricity trace')
                        traces = [gas_trace, electricity_trace]
                else:
                    if self.chart_type.get() == 'scatter':
                        gas_trace = go.Scatter(x=x_axis,y=graph_data[FuelType.gas],name='gas trace')
                        electricity_trace = go.Scatter(x=x_axis,y=graph_data[FuelType.electricity],name='electricity trace',yaxis='y2')
                    else:
                        gas_trace = go.Bar(x=x_axis,y=graph_data[FuelType.gas],name='gas trace', width=0.4)
                        electricity_trace = go.Bar(x=x_axis,y=graph_data[FuelType.electricity],name='electricity trace',yaxis='y2', offset=0.2, width=0.4)
                    traces = [gas_trace, electricity_trace]

            else:
                (gas_values, electricity_values, gas_average, electricity_average, total, total_average) = ([], [], [], [], [], [])
                datapoint = 0
                for date in date_range:
                    gas_values.append(data[date][FuelType.gas])
                    electricity_values.append(data[date][FuelType.electricity])
                    if self.total_mode.get() == 'Show totals':
                        total.append(data[date][FuelType.electricity] + data[date][FuelType.gas])
                    if datapoint < 29:
                        total_gas = 0
                        total_electricity = 0
                        for i in range(0, datapoint + 1):
                            total_gas += gas_values[i]
                            total_electricity += electricity_values[i]
                        gas_average.append(total_gas / (datapoint + 1))
                        electricity_average.append(total_electricity / (datapoint + 1))
                        if self.total_mode.get() == 'Show totals':
                            total_average.append((total_gas + total_electricity) / (datapoint + 1))
                    else:
                        total_gas = 0
                        total_electricity = 0
                        for i in range(0, 29):
                            total_gas += gas_values[datapoint - i]
                            total_electricity += electricity_values[datapoint - i]
                        gas_average.append(total_gas / 30)
                        electricity_average.append(total_electricity / 30)
                        if self.total_mode.get() == 'Show totals':
                            total_average.append((total_gas + total_electricity) / 30)
                    datapoint += 1
                if self.total_mode.get() == 'Show totals':
                    if self.chart_type.get() == 'scatter':
                        gas_trace = go.Scatter(x=date_range,y=gas_values,name='gas trace')
                        electricity_trace = go.Scatter(x=date_range,y=electricity_values,name='electricity trace')
                        gas_average_trace = go.Scatter(x=date_range,y=gas_average,name='gas (30 day moving average)')
                        electricity_average_trace = go.Scatter(x=date_range,y=electricity_average,name='electricity (30 day moving average)')
                        total_trace = go.Scatter(x=date_range,y=total,name='total trace')
                        total_average = go.Scatter(x=date_range,y=total_average,name='total (30 day moving average)')
                        traces = [gas_trace, electricity_trace, gas_average_trace, electricity_average_trace, total_trace, total_average]
                    else:
                        gas_trace = go.Bar(x=date_range,y=gas_values,name='gas trace')
                        electricity_trace = go.Bar(x=date_range,y=electricity_values,name='electricity trace')
                        traces = [gas_trace, electricity_trace]
                else:
                    if self.chart_type.get() == 'scatter':
                        gas_trace = go.Scatter(x=date_range,y=gas_values,name='gas trace')
                        electricity_trace = go.Scatter(x=date_range,y=electricity_values,name='electricity trace',yaxis='y2')
                        gas_average_trace = go.Scatter(x=date_range,y=gas_average,name='gas (30 day moving average)')
                        electricity_average_trace = go.Scatter(x=date_range,y=electricity_average,name='electricity (30 day moving average)',yaxis='y2')
                    else:
                        gas_trace = go.Bar(x=date_range,y=gas_values,name='gas trace')
                        electricity_trace = go.Bar(x=date_range,y=electricity_values,name='electricity trace',yaxis='y2')
                        gas_average_trace = go.Bar(x=date_range,y=gas_average,name='gas (30 day moving average)')
                        electricity_average_trace = go.Bar(x=date_range,y=electricity_average,name='electricity (30 day moving average)',yaxis='y2')
                    traces = [gas_trace, electricity_trace, gas_average_trace, electricity_average_trace]
            if self.total_mode.get() == 'Show totals':
                layout = go.Layout(title=ids[0] + ' Both Fuels ' + self.chart_scope.get(),yaxis=dict(title=title),
                    barmode='stack')
            else:
                layout = go.Layout(title=ids[0] + ' Both Fuels ' + self.chart_scope.get(),yaxis=dict(title='Gas ' + title),
                    yaxis2=dict(title='Electricity ' + title,overlaying='y',side='right'))

        fig = go.Figure(data=traces, layout=layout)
        plotly.offline.plot(fig, auto_open=True)

    def pie_chart(self):
        values = []
        start = self.get_start()
        end = self.get_end()
        if self.costs_checked.get() == 'Show costs':
            data = self.annual_costs
            ids = list(set(self.loaded_ids).intersection(self.loaded_ids_sup))
        else:
            data = self.data_container
            ids = self.loaded_ids
        for i in ids:
            value = 0
            for d in list(data.keys()):
                if d >= start and d <= end:
                    value += data[d][i]
            values.append(value)
        trace = go.Pie(labels=ids, values=values)
        if self.costs_checked.get() == 1:
            layout = go.Layout(title='Total ' + self.loaded_fuels[0] + ' costs (£)')
        else:
            layout = go.Layout(title='Total ' + self.loaded_fuels[0] + ' usage (kWh)')
        fig = go.Figure(data=[trace], layout=layout)
        plotly.offline.plot(fig, auto_open=True)


    def distribution_graph_multi(self):
        traces = []
        minval = self.metrics["all"]['Minimum usage: ']
        maxval = self.metrics["all"]['Maximum usage: ']
        sizes = [1000,10000,50000,100000,200000,500000,1000000]
        columns = [50,100,200,300,400,500,600]
        options = ['1,000 points', '10,000 points', '50,000 points', '100,000 points', '200,000 points', '500,000 points', '1,000,000 points']
        size = 1000
        columnc = 50
        for i in range(len(options)):
            if self.graph_size.get() == options[i]:
                size = sizes[i]
                columnc = columns[i]
        if minval != 0:
            if abs(maxval / minval > 5): #Start from zero if sensible
                minval = 0
            else:
                minval = round_1sf(minval)
        interval = round_1sf((maxval - minval) / columnc)
        for key in list(self.metrics.keys()):
            if key != "all":
                data = self.metrics[key]["rawdata"]
                currsize = len(data)
                while len(data) < size: # Expand data set to at least the minimum size
                    data = merge_sort(data)
                    for i in range(currsize - 1):
                        data.append((data[i] + data[i+1])/2)
                    currsize = len(data)
                traces.append(go.Histogram(
                    x=data,
                    opacity = 0.7,
                    name=key,
                    histnorm='probability',
                    xbins=dict(start=minval, end=maxval, size=interval),
                    autobinx = False
                ))
        layout = go.Layout(title='Distribution graph', xaxis=dict(title='Consumption (kWh)'), barmode='overlay')
        fig = go.Figure(data=traces, layout=layout)
        plotly.offline.plot(fig, auto_open=True)


'''
This is the entry point of the script. The code here will run first when the script is run,
and essentially all it does is establish a few constraints of the GUI window, setup the plotly
instance, and create the EnergyMonitor class. The mainloop() method is what allows the Tkinter
widgets to respond to user input, by entering a waiting loop to detect changes in the UI. 
'''
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Energy Monitor")
    root.geometry('1000x750')
    root.configure(background='#c6e2ff')

    plotly.tools.set_credentials_file(username='josh.power', api_key='0R0G5rbmFrvqIqeTsHhG')

    gui = EnergyMonitor(root)
    root.mainloop()
