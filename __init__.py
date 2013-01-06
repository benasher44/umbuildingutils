import re
from urllib import urlencode
import urllib2

# base urls for doing building-related searches
# some have a param in the url and some use POST params
BASE_URLS = {
        'BUILDING_ID_SEARCH' : "http://uuis.umich.edu/cic/buildingProject/process_search.cfm?action=process&kw=%s",
        'BUILDING_INFO_SEARCH' : "http://uuis.umich.edu/cic/buildingProject/index.cfm?BuildingID=%s",
        'BUILDING_ACRONYM_SEARCH' : "http://uuis.umich.edu/cic/acronyms/index.cfm",
        }

# building request regular expressions
BUILDING_RES = {
        'ID' : re.compile("BuildingID=(\d+)"),
        'INFO' : re.compile("<div id=\"address\">\s*(.+)<br />\s*(.+)<br />"),
        'ACRONYM_LOOKUP' : re.compile("<p class=\"largeText\">.+>(.*)<.+</p>"),
        'ACRONYM_DICT_KEY' : re.compile('<span class="listMiddle">(.+)</span>'),
        'ACRONYM_DICT_VAL' : re.compile('<span class="acronymText"><a.+\s*.+>(.+)</a></span>|<span class="acronymText">(.+)</span>'),
        }

# very basic object to contain a building name and address
# could be extended to include its acronym as well
class UMBuildingLocation:
    buildingName = ""
    address = ""
    city = ""
    state = ""
    zipcode = ""

    # buildingInfoTup example: ('1301 Beal', 'Ann Arbor, MI 48109')
    def __init__(self, buildingInfoTup):
        self.address = buildingInfoTup[0]
        regionInfoParts = buildingInfoTup[1].split(",")
        self.city = regionInfoParts[0]
        self.state, self.zipcode = [regionPart.strip() for regionPart in regionInfoParts[1].split()]

    def __repr__(self):
        return "address: " + self.address + " | city: " + self.city + " | state: " + self.state + " | zipcode: " + self.zipcode

# useful function for fetching data
# important/convenient for closing the connection as soon as its read all of the data
def fetch_data(url, post_params={}):
    if len(post_params) > 0:
        conn = urllib2.urlopen(url, urlencode(post_params))
    else:
        conn = urllib2.urlopen(url)
    data = conn.read()
    conn.close()
    return data

# gets an acronym dictionary
# e.g. EECS : Electrical Engineering and Computer Science Building
def getAcronymDict():
    resultStr = fetch_data(BASE_URLS['BUILDING_ACRONYM_SEARCH'], {'getAll':'Get a list of UM acronyms'})
    keys = BUILDING_RES['ACRONYM_DICT_KEY'].findall(resultStr)
    values = BUILDING_RES['ACRONYM_DICT_VAL'].findall(resultStr)
    values = map(lambda v: ''.join(v).split(',')[0], values)
    return dict(zip(keys, values))

# gets the building ID to use to do the buliding location lookup
def getBuildingId(building):
    resultStr = fetch_data(BASE_URLS['BUILDING_ID_SEARCH'] % building)
    return BUILDING_RES['ID'].search(resultStr).group(1)

# uses the building ID to do the build location lookup
# return tuple in the form ('1301 Beal', 'Ann Arbor, MI 48109')
def getBuildingInfo(buildingId):
    resultStr = fetch_data(BASE_URLS['BUILDING_INFO_SEARCH'] % buildingId)
    m = BUILDING_RES['INFO'].search(resultStr)
    return (m.group(1).strip().replace("&nbsp;"," "),m.group(2).strip().replace("&nbsp;"," "))

# takes a building name like EECS and returns a UMBuildingLocation object
def getBuildingLocation(building):
    buildingInfo = getBuildingInfo(getBuildingId(building))
    return UMBuildingLocation(buildingInfo)

# returns the full buliding name for an acronym like EECS
# you have to use this if getBuildingLocation fails because the search didn't understand the acronym
def getFullBuildingName(building):
        resultStr = fetch_data(BASE_URLS['BUILDING_ACRONYM_SEARCH'], {'decode': '1','acronymLookup': building})
        m = BUILDING_RES['ACRONYM_LOOKUP'].search(resultStr)
        return m.group(1).split(",")[0]
