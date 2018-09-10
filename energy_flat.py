from os import path
import tkinter as tk
from tkinter import scrolledtext
from tkinter import filedialog
from ntpath import basename
import re
import csv
import plotly
import plotly.graph_objs as go
import datetime
import math

'''
 This method will set up all of the data structures we need to run this script correctly.
 It also creates the UI components that are used to create the interface seen when the
 script is launched.
 '''

def init(parent):

    global data_container
    global loaded_ids
    global loaded_fuels
    global data_metrics
    loaded_ids, loaded_fuels = [], []

    # The variable data_container is a 2D list, meaning a list that contains more lists
    # as its elements. In the code below, I am first setting data_container to be an empty list
    # Then, I am appending three empty lists (the '[]' stands for an empty list in Python) to it.
    # Once the data_container has these lists created inside it, they can be populated
    # later with the values from the loaded file.
    data_container = [[], []]

    #TODO When adding both fuel file support, this metrics dictionary won't be enough
    #TODO to store metrics for both types of fuel. You could add another dictionary and then
    #TODO then rename this one, so that there are two dictionaries for the two types.
    data_metrics = {"mean": 0, "stdev": 0, "min": 0, "max": 0}

    global btn_graph_annual, scrolled_text

    welcome_label = tk.Label(parent, text='Welcome to the Energy Monitor!', font=('Calibri', 32))
    welcome_label.configure(background='#c6e2ff')
    welcome_label.pack()

    message_label = tk.Label(parent, text='Please use the dialog below to load a CSV file, which will be displayed ' +
                                      'in the box below.', font=('Calibri', 14), wraplength=540)
    message_label.configure(background='#c6e2ff')
    message_label.pack(pady=20)

    btn_file = tk.Button(parent, text="Load file", command=load_file)
    btn_file.pack(pady=20)

    scrolled_text = tk.scrolledtext.ScrolledText(parent, width=40, height=10)
    scrolled_text.pack()

    btn_graph_annual = tk.Button(parent, text='Annual Usage',
                                      command=generate_annual_graph_singlehouse)
    btn_graph_annual.pack_forget()

# This method handles the loading of a simple file, and processing the data in it into a data storage
# It will be called every time you click the 'Load' button on the main page of the application.
# Each time the button is clicked, the data loaded from the previous file is discarded
def load_file(file=None):

    if file is None:
        file = filedialog.askopenfilename(initialdir=path.dirname(__file__))
    elif not path.isfile(file):
        raise ValueError("This file does not exist or is not readable.")

    print("File name is '%s'" % file)

    # This is a regular expression, essentially a form of pattern-matching that will
    # allow us to check that the file name of the loaded file is in the correct format.
    # For more information about regular expressions, see https://www.learnpython.org/en/Regular_Expressions
    re_single_house = re.compile('^(.*?)_(.*?)_daily$')

    filename = str(basename(file).split('.')[0])
    single_match = re_single_house.search(filename)

    #TODO When loading both fuels, how will this part need to change? The file name of a file
    #TODO with both fuels will contain 'both' instead of a fuel name, so can you use this
    #TODO to decide how to set the loaded fuels?
    loaded_fuel = single_match.group(2)
    print("Loaded fuel is: '%s'" % loaded_fuel)

    # TODO You should add here some validation to check that the fuel name is correct

    if single_match is not None:
        process_single_file(file, single_match.group(1))
    else:
        raise ValueError("File format is not correct, must be '{house-id}_both_daily.csv'")

    btn_graph_annual.pack(pady=5)

    #TODO Now that the file has been fully loaded into the script, you should generate
    #TODO and display some metrics for the loaded data. The metrics you need to calculate
    #TODO are: Maximum value, minimum value, mean value and standard deviation. You can
    #TODO use the scrolled_text widget in the UI to display the metrics.


# This method has been split off from the above one, in order to keep the above method from
# becoming too long and complex. It will handle all the processing of the file selected above.
# Processing this file essentially means that its data will be read into the script from the file
# you loaded before, and will then be examined and stored into an array. Once there, it can be
# used later on to calculate graphs or metrics for the loaded data
def process_single_file(file, house_id):
    print("This file is a single house with both fuel types. The house id is '%s'." % house_id)
    print("Deleting old data")

    # This line resets the data_container so it can be used to store the loaded data
    # It is important that these lists are cleared instead of being re-assigned to new empty
    # lists. This is because they are global variables, and using clear() preserves the changes
    # made in other functions.
    data_container[0].clear()
    data_container[1].clear()
    loaded_ids.clear()
    loaded_fuels.clear()
    scrolled_text.delete(1.0, tk.END)

    #TODO Before the file can be opened, we should check that it ends in '.csv'
    #TODO This means that it is safe to open using the built-in CSV reader
    #TODO functionality in Python. How can we check what a string ends with?
    #TODO If the filename is invalid, we should raise an error, like this:
    # raise ValueError('I've found an error!')

    '''
    This next line acts as opening the file, so that the data inside it can be read by the 
    script. Within this code, the file is being actively used by the script, so it
    shouldn't be modified or deleted.
    '''
    with open(file, 'r') as file_contents:
        reader = csv.reader(file_contents)
        header = next(reader, None)

        #TODO How will you check the header is correct? Add some checks here to ensure the data
        #TODO in the file matches the column names 'gas', 'electricity' or both when adding two fuels
        #TODO In a both fuel file, the electricity will always be in the second column, and the
        #TODO gas data will be in the third column.
        #TODO This code is complete but doesn't quite work right - there's something wrong with
        #TODO what we're checking for in the header values. Look at the data file - what are the
        #TODO headers called? Are they different from what we have here?
        if header[1] != 'electricity' and header[1] != 'gas':
            raise ValueError('File is not in correct format. Second column header must be either "Electricity" or "Gas"')

        loaded_fuels.append(header[1].lower())
        print("Loaded fuel type is: %s" % header[1])

        for row in reader:
            print(row)

            # This generates a DateTime object that represents the date in each row
            # DateTime objects can be used within Python to do date calculations and
            # are much more accurate than trying to use integers or strings
            this_date = datetime.datetime.strptime(row[0], '%Y%m%d').date()

            # TODO If you wanted to check here that each value in the current row was a valid
            # TODO float value, how would you do this? What other checks could you do on this data?
            #TODO There is a function defined in this script called isNumber, which will return
            #TODO True if the value passed in is a valid number, and False if not. Could you use that
            #TODO to check the data being read in from the file here?


            #TODO How will this part change when both fuels are loaded?
            data_container[0].append(this_date)
            data_container[1].append(row[1])

        # Since we have only loaded one file, set the id directly
        loaded_ids.append(house_id)


def validate_data():
    print('Validating loaded fuel data')

    #TODO This method needs to do some validation on the data stored in data_container
    #TODO One thing we know for sure is that the list should have a certain number of elements
    #TODO How can we find out what this number is? And what should we do if this is incorrect?


'''
This function takes one argument, and checks to see if it can be converted to a floating point number
or not. You could use this elsewhere in your code to check if certain read in fields are valid.
'''
def isNumber(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


def getStandardDeviation(values, mean):

    stdev = 0

    for value in values:

        stdev += (value - mean) ** 2

    stdev = math.sqrt(stdev / len(values))

    return stdev


# We are passing in a list of values here so that when the code is expanded to
# use multiple fuels it can be re-used
def generate_metrics(values):
    print("Metrics")

    # You should use float_values when generating the metrics, essentially this will force the
    # values passed in to be actual float values, instead of string versions of the same values
    # For example, '0.75' becomes 0.75, which changes how Python will process the value.
    # noinspection PyUnusedLocal
    float_values = list(map(lambda x: float(x), values))



# This method uses plotly to generate graphs, which open in a browser window.
def generate_annual_graph_singlehouse():

    date_range = list(data_container[0])

    fuel_trace = go.Scatter(
        x=date_range,
        y=data_container[1],
        name='fuel trace'
    )

    #TODO Here we have a single trace, but when both fuels are loaded you will need a
    #TODO second trace to represent both gas and electricity data. You will need to modify the code
    #TODO to support two traces for the different fuels, but I have included the layout code below

    graph_data = [fuel_trace]

    layout = go.Layout(
        title="Single House %s Usage" % str(loaded_fuels[0]).capitalize(),
        yaxis=dict(
            title='Usage (kWh)'
        )
    )

    #TODO Use this layout with two traces for both fuel types.
    '''
    layout = go.Layout(
            title='Single House Both Fuels',
            yaxis=dict(
                title='Usage (kWh)'
            ),
            yaxis2=dict(
                title='yaxis2 title',
                titlefont=dict(
                    color='rgb(148, 103, 189)'
                ),
                tickfont=dict(
                    color='rgb(148, 103, 189)'
                ),
                overlaying='y',
                side='right'
            )
        )
    '''

    fig = go.Figure(data=graph_data, layout=layout)
    plotly.offline.plot(fig, auto_open=True)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Energy Monitor")
    root.geometry('600x750')
    root.configure(background='#c6e2ff')

    plotly.tools.set_credentials_file(username='josh.power', api_key='0R0G5rbmFrvqIqeTsHhG')
    print(plotly.__version__)

    init(root)
    root.mainloop()
