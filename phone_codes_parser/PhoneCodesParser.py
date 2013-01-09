#!-*- encoding: utf-8 -*-
from bs4 import BeautifulSoup
import urllib
import sys
import re
import csv


class PhoneCodesParser(object):
    def __init__(self):
        self.URL = "http://www.ukrtelecom.ua/reference/trunkline_code/code"
        self.HOST = "http://www.ukrtelecom.ua"
        self.PATH_PATTERN = "/reference/trunkline_code/code\?qa=%\w{1,2}"
        self.urls = []

    #TODO: Connect for every url and parse data to csv

    def connect(self, url):
        file = None
        try:
            file = urllib.urlopen(url)
        except Exception as e:
            print e
            sys.exit(1)
        return file


    def search_urls(self):
        pattern =  re.compile(self.PATH_PATTERN)
        parsed = BeautifulSoup(self.connect(self.URL).read())

        links = parsed.findAll("a")
        if len(links):
            for link in links:
                href = link.attrs['href']
                if re.match(pattern, href):
                    self.urls.append(self.HOST+href)
        self.hidden_urls()



    def hidden_urls(self):
        urls = []
        urls.extend(self.urls)
        for url in urls:
            print "search ", url
            parsed = BeautifulSoup(self.connect(url).read())
            container = parsed.find(True,"pager")
            if container:
                links = container.findAll("a")
                for link in links:
                    self.urls.append(self.HOST+link['href'])
        self.urls = set(self.urls)

    def address_parser(self):
        data = []
        self.search_urls()
        print len(self.urls)
        i=1
        for url in self.urls:
            import pdb
#            pdb.set_trace()
            requested = url #self.HOST+url
            print i, requested
            i +=1
            parsed = BeautifulSoup(self.connect(requested).read())
            res = parsed.find(id="content")
            try:
                table = res.findChildren("table")[1]
            except :
                pass
            trs = table.findChildren("tr")
            ommited_words = [u"Довідковий телефон", u"Область", u"Місто", u"Код"]

            for tr in trs:
                row_data = []
                for td in tr.findChildren("td"):
                    if td.text in ommited_words:
                        continue
                    row_data.append(td.text.encode("utf-8"))
                if len(row_data):
                    data.append(row_data)
            self.csv_writer(data)


    def csv_writer(self, rows):
        with open("ukraine_phone_codes.csv", "wb") as file:
            receiver = csv.writer(file, dialect="excel")
            receiver.writerows(rows)

if __name__ == "__main__":
    fcp = PhoneCodesParser()
    fcp.address_parser()