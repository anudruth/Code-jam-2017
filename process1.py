#!/usr/bin/env python
import googlemaps
import gmplot
import csv
import sys
import itertools
import math
import copy
import webbrowser, os

from datetime import datetime

import cgi
import cgitb

form = cgi.FieldStorage()

print ("Content-type:text/html\r\n\r")
