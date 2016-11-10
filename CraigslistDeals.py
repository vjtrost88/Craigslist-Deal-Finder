import requests
from bs4 import BeautifulSoup

# make HTTP request to craigslist listings page
url = "https://pittsburgh.craigslist.org/search/cta"
r = requests.get(url)

# transform HTML content into bs4 object
soup = BeautifulSoup(r.content, 'lxml')

# initialize listings and append listing where link is a listing
listings = []
for link in soup.find_all('a'):
    if ".html" in link.get('href'):
        listings.append("https://pittsburgh.craigslist.org" + link.get('href'))
del(listings[::2])    # first or last couple links are irrelevant, can't really remember what this does...

# initialize lists we're going to need...
prices = []
car_list = []
cars = []

# rather than do for listing in listings, create an iterator for more flexibility
myiter = iter(range(len(listings)))

for i in myiter:    # for each individual listing...

    # make the request and create bs4 object
    r = requests.get(listings[i])
    bsObj = BeautifulSoup(r.content, 'lxml')

    # there are 2 attrgroups on good listings- first contains year make model, second contains mileage (mong other things)
    lst_data = bsObj.find_all('p', {'class': 'attrgroup'})

    try:    # price is listed next to the listing title in the regular html code
        price = bsObj.find('span', {'class': 'price'}).get_text()
        prices.append(price.replace('$', ''))    # get rid of the dollar sign
    except AttributeError:    # if we don't find price in the html code...
        prices.append('NO PRICE')

    try:    # try to get the year, make, and model
        car_info = lst_data[0].get_text()    # first attrgroup object (so it's at pos 0)
        car_list = car_info.split()    # split string into [year, make, model]
    except IndexError:    # if we don't find anything here, the page has been flagged for removal for sure.
        car_list.append('PAGE REMOVED')

    try:    # try to get the mileage
        broad = lst_data[1].get_text()    # odometer is buried in the middle of the second attrgroup object
        blist = []
        if 'odometer: ' in broad:    # broad meaning the big long mess of a string in the second attrgroup
            blist = broad.split()    # splits it into multple messes-- gasodometer:, 95340paint: (for ex)
            for j in range(len(blist)):    # searches each mess for odometer
                if 'odometer' in blist[j]:    # if odometer in the one object, the number for mileage is in the next
                    car_list.insert(1, blist[j+1][:-5]) # luckily, 99.9% of the time, title or paint follow the mileage-
                                                        # both are len(5) strings so we can rig it
        else:
            car_list.insert(1, 'NO MILEAGE')    # nothing found in the string? NO MILEAGE
    except IndexError:
        car_list.append('PAGE REMOVED')  # no second attrgroup object? shits gone fam. Page has been flagged for removal

    # since car_list has most of what we want already, might as well add
    # the stragglers to it instead of doing something new
    car_list.insert(0, prices[i])    # add price to the front
    car_list.insert(1, listings[i])    # add listing after price, and now we have-
                                       # a complete car record!
    # add this record to the list of cars
    cars.append(car_list)
    # whala, we're done with one. repeat for as many listings as we have

# initialize good_cars list
good_cars = []
for car in cars:
    if car[0] != 'NO PRICE' and car[3] != 'NO MILEAGE' and len(car) > 5:    # if it has no price or mileage,
        # it's trash. If it has neither, good!
        good_cars.append(car)

for i in range(len(good_cars)):
    if(good_cars[i][4] == 'Chevy'):
	good_cars[i][4] = 'Chevrolet'
    print good_cars[i]
print len(good_cars)
print('--------------------')

# POS0- PRICE
# POS1- LINK
# POS2- YEAR
# POS3- MILEAGE
# POS4- MAKE
# POS5- MODEL
# POS6- MODEL(part2)
# POS7*- MODEL(part3 and beyond...)



"""
Edmunds API Documentation: http://developer.edmunds.com/

"""

from edmunds.edmunds import Edmunds


def get_style_id(api, make, model, year):
    """
    Get style ID from make, model, year

    See endpoint documentation: http://developer.edmunds.com/api-documentation/vehicle/spec_model_year/v2/02_year_details/api-response.html

    :param api: The Edmunds api object with API key
    :type api: Edmunds object
    :param make:
    :type make: str
    :param model:
    :type model: str
    :param year:
    :type year: str
    :returns: Style ID or None if error
    :rtype: str or None
    """
    endpoint = '/api/vehicle/v2/' + make + '/' + model + '/' + year
    response = api.make_call(endpoint)

    # error checking
    if (not response or 'error' in response or
                'errorType' in response or not 'styles' in response):
        print "Error in get_style_id"
        if 'error' in response:
            if 'message' in response['error']:
                print
                "Error message:", response['error']['message']
        elif 'errorType' in response:
            print
            "errorType:", response['errorType']
            if 'message' in response:
                print
                "message:", response['message']
        return None

        # return first style ID
        # be careful, respoonse['id'] is the Edmunds ID, not the style ID
    return response['styles'][0]['id']


def get_price(api, style_id, condition, mileage, zipcode):
    """
    Get price of a vehicle by its style ID, condition, mileage, and zipcode

    :param api: The Edmunds api object with API key
    :type api: Edmunds object
    :param style_id: Style ID of vehicle
    :type style_id: str
    :returns: Dictionary of lists, where each key is the type (subType, shotType) of photo, and each value is a list of photo urls
    :rtype: Dictionary {tuple: list} ({(subType, shotType): list_of_url_strings})
        ex: { ('exterior', 'RQ'): ['URL1', 'URL2', ...], ('interior', 'G'): ['URL1', 'URL2', ...] }
    """
    endpoint = '/v1/api/tmv/tmvservice/calculateusedtmv?styleid=' + style_id + '&condition=' + condition + '&mileage=' + mileage + '&zip=' + zipcode
    response = api.make_call(endpoint, styleId=style_id)

    return response


def get_model_price(api, make, model, year, price, mileage):
    """
Gets price of the Car after adding style_id, condition, mileage, and zipcode

:returns: Car price object
:rtype: dict or None
    """
    style_id = get_style_id(api, make, model, year)
    style_id = str(style_id)
    car_price_obj = None
    if style_id != 'None':
        car_price_obj = get_price(api, style_id, 'Average', mileage, '27514')
        price_usedPrivateParty = (car_price_obj.get('tmv').get('totalWithOptions').get('usedPrivateParty'))
        price_difference = price_usedPrivateParty - float(price)
    else:
        return 'Car not worth it'
            
    if (price_difference > 1000):
        return "Take a look"
    else:
        return "Car not worth it"
   

for i in range(len(good_cars)):
    if __name__ == "__main__":
        api = Edmunds('znkuas8cm9yvk35q5d45f9rd', True)  # True indicates debug mode is ON
        decision = None
        make = good_cars[i][4]
        model = good_cars[i][5]
        year = good_cars[i][2]
        price = good_cars[i][0]
        mileage = good_cars[i][0]
        link = good_cars[i][1]

        decision = get_model_price(api, make, model, year, price, mileage)
    
        if (decision == "Take a look"):

            Message = 'Price: $' + str(good_cars[i][0]) + ' ' + str(good_cars[i][2]) + ' ' + str(good_cars[i][4]) + ' ' + str(good_cars[i][1])










