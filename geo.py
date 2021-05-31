#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 10 12:49:40 2021

@author: nickj
"""

import csv
import numpy as np

# r = csv.reader('/home/nickj/Dokumente/GitHub/ebay-notify/PLZ.csv')

coordines = {}
with open('PLZ.csv', newline='') as csvfile: # source: https://launix.de/launix/launix-gibt-plz-datenbank-frei/
    spamreader = csv.reader(csvfile, delimiter=';', quotechar='"')
    for row in spamreader:
        # print(', '.join(row))
        coordines[int(row[0])] = [float(row[2]), float(row[3]), ]
        # print(row[0])
        
def getDistance(plz1, plz2):
    try:
        lon1, lat1 = coordines[int(plz1)]
    except Exception as e:
        print('Unknown PLZ: '+plz1)
        return 0

    try:
        lon2, lat2 = coordines[int(plz2)]
    except Exception as e:
        print('Unknown PLZ: '+plz2)
        return 0


    R = 6371.; # kilometres
    phi1 = lat1 * np.pi/180; # phi, lamda in radians
    phi2 = lat2 * np.pi/180;
    d_phi = (lat2-lat1) * np.pi/180;
    d_lamda = (lon2-lon1) * np.pi/180;
    
    a = np.sin(d_phi/2) * np.sin(d_phi/2) + np.cos(phi1) * np.cos(phi2) * np.sin(d_lamda/2) * np.sin(d_lamda/2);
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a));
    
    d = R * c; # in metres
    return d
    
# print(getDistance('81477', '07743'))