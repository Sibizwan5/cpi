#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Parse and prepare the Consumer Price Index (CPI) dataset.
"""
import os
import csv
import collections
from datetime import date
from .models import Index, Series, ObjectList


class BaseParser(object):
    THIS_DIR = os.path.dirname(__file__)

    def get_file(self, file):
        """
        Returns the CPI data as a csv.DictReader object.
        """
        # Open up the CSV from the BLS
        csv_path = os.path.join(self.THIS_DIR, "{}.csv".format(file))
        csv_file = open(csv_path, "r")
        return csv.DictReader(csv_file)


class ParseSeries(BaseParser):
    """
    Parses the raw list of CPI series from the BLS.
    """
    def parse(self):
        """
        Returns a list Series objects.
        """
        object_list = ObjectList()
        for row in self.get_file('cu.series'):
            obj = Series(
                row['series_id']
            )
            object_list.append(obj)
        return object_list


class ParseIndex(BaseParser):

    def __init__(self):
        self.by_year = collections.defaultdict(collections.OrderedDict)
        self.by_month = collections.defaultdict(collections.OrderedDict)

    def parse_periodtype(self, period):
        """
        Accepts a row from the raw BLS data. Returns a string classifying the period.
        """
        period_types = dict(("M{:02d}".format(i), "monthly") for i in range(1, 13))
        period_types["M13"] = "annual"
        period_types.update({
            "S01": "half",
            "S02": "half",
            "S03": "annual"
        })
        return period_types[period]

    def parse_date(self, row):
        """
        Accepts a row from the raw BLS data. Returns a Python date object based on its period.
        """
        # If it is annual data, return it as Jan. 1 of that year.
        if row['period'] in ['M13', 'S03']:
            return date(int(row['year']), 1, 1)
        # If it is month data, return it as the first day of the month.
        elif row['period'].startswith("M"):
            return date(int(row['year']), int(row['period'].replace("M", "")), 1)
        # If it's data for halves of the year...
        else:
            months = {
                "S01": 1,
                "S02": 7,
            }
            return date(int(row['year']), months[row['period']], 1)

    def parse(self):
        """
        Parse the raw BLS data into dictionaries for Python lookups.
        """
        for row in self.get_file("cu.data.1.AllItems"):
            # Create a series
            series = Series(row['series_id'])

            # Clean up the values
            period_type = self.parse_periodtype(row['period'])
            date = self.parse_date(row)

            # Create an object
            index = Index(
                series,
                date,
                date.year,
                period_type,
                float(row['value'])
            )

            # Sort it to the proper lookup
            if index.period_type == 'annual':
                self.by_year[series.id][index.year] = index
            elif index.period_type == 'monthly':
                self.by_month[series.id][index.date] = index
