import csv
import random
import datetime
import math

houses = int(input("Enter number of houses: "))
headers = []
if houses == 1:
    headers = ["date", "electricity", "gas"]
else:
    headers = ["date"]
    for i in range(houses):
        headers.append(input("Enter house name: "))
data = {}
startdate = datetime.datetime.strptime(str(input("Enter start date (yyyymmdd): ")), '%Y%m%d').date()
enddate = datetime.datetime.strptime(str(input("Enter end date (yyyymmdd): ")), '%Y%m%d').date()
d = startdate
while d <= enddate:
    data[d] = []
    d += datetime.timedelta(days=1)
for h in headers:
    if h == "date":
        for d in list(data.keys()):
            data[d].append(str(d.year) + '{num:02d}'.format(num=d.month) + '{num:02d}'.format(num=d.day))
    else:
        base = float(input("Enter base usage for first date: "))
        increase = float(input("Enter percentage to increase by each year: "))
        randcomponent = float(input("Enter size of random component: "))
        randdistr = int(input("Enter number of separate rolls to use (more = closer to normal distribution): "))
        randmulti = int(input("Multiply by random? (makes distribution peakier): "))
        randdiv = int(input("Divide by random? (makes distribution very peaky): "))
        season = float(input("Enter strength of seasonal effect (0-1): "))
        min = base
        max = base
        avg = base
        if randcomponent != 0 and randdistr != 0:
            avg += randcomponent * 0.5
            max += randcomponent
        if randmulti >= 1:
            min = 0
            avg *= pow(0.5, randmulti)
        if randdiv >= 1:
            max /= pow(0.1, randdiv)
            avg /= pow(0.55, randdiv)
        min *= 1 - season
        avg *= 1 - (season / 2)
        avg *= math.pow(increase / 100 + 1, (enddate - startdate).days / 730)
        if increase >= 0:
            max *= math.pow(increase / 100 + 1, (enddate - startdate).days / 365)
        else:
            min *= math.pow(increase / 100 + 1, (enddate - startdate).days / 365)
        print("Minimum value: " + str(min))
        print("Average value: " + str(avg))
        print("Maximum value: " + str(max))
        final = float(input("Enter final multiplier: "))
        for d in list(data.keys()):
            val = base
            if randdistr != 0:
                for i in range(randdistr):
                    val += random.random() * randcomponent / randdistr
            if randmulti >= 1:
                for i in range(randmulti):
                    val *= random.random()
            if randdiv >= 1:
                for i in range(randdiv):
                    val /= 0.9 * random.random() + 0.1
            seasonal = (5.5-abs(d.month - 6.5)) / 5.5
            val *= (1-seasonal * season) * final * math.pow(increase / 100 + 1, (d - startdate).days / 365)
            data[d].append(val)
print("Data generated")
csvfile = input("Enter file name to write to: ")
with open(csvfile, "w") as output:
    writer = csv.writer(output, lineterminator='\n')
    writer.writerow(headers)
    for d in list(data.keys()):
        writer.writerow(data[d])
print("File writing successful")
input()

'''This CSV writer generates realistic-looking electricity and/or gas consumption for any number of houses and writes
it to a CSV in a way that is readable by the main program.

If the number of houses to generate for is 1, both gas and electricity data will be generated. For multiple houses,
only one of the two fuels will be written. Start and end dates are inclusive and there is very little restriction on
the date range.

When generating the data for each house or fuel, the user is prompted for several parameters which affect the
final data set:
* Base usage: Flat consumption amount
* Percentage increase: The amount that consumption increases each year. Negative values are supported. The multipler is
    only applied at the end.
* Random component: This is added to the base usage and uses the random number generator. For example, if the base usage
    is 5 and the random component is 10, the resulting data will lie between 5 and 15.
* Number of separate rolls: Increasing this number makes the resulting random numbers "smoother" and form something
    closer to a bell-curve distribution. For example, counting the total number of heads from 6 coin tosses will result
    in more 3s and fewer 1s and 6s than rolling a 6-sided die.
* Multiply by random: This multiplies the entire data set by a random number from 0 to 1. This means there is a chance
    of a data point being zero (or close to zero). This can be repeated as many times as wished.
* Divide by random: This divides the entire set by a random number from 0.1 to 1 which will cause sharp peaks to appear.
    This can be repeated as many times as wished.
* Final multiplier: After all transformations have been applied, a minimum possible, maximum possible and crude average
    (obtained by setting all random numbers to 0.5) are displayed. A flat multipler can be used to change the values if
    they are not what is desired.
'''