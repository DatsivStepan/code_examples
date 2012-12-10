#!/usr/bin/env python
#! encoding: utf-8

# description: SEO optimiser - add links from xls-file to entities from given tables
# version: 0.1
# date: 2012-11-23
from random import randint
import re
import sys
import psycopg2
import xlrd
from ecommerce.ecommerce.prod_settings import DATABASES
import logging

logging.basicConfig(filename="seo_link_creation.log", level=logging.INFO)

class SEO_Optimiser(object):

    def __init__(self, file, tables = [], *args, **kwargs):

        self.file = file
        self.search_string_list = []    #comprise all search strings
        self.optimisation_data = {}     #comprise all data from xls stylesheet
        self.db_ids_data = {}           #comprise ids of entities which has search word in description
        self.used_once_ids = []         #list for used ones ids
        self.used_twice_ids = []        #list for used twice ids

        if len(tables)>0:
            self.tables = tables
        else:
            logging.info("[ERROR in constructor]: You didn`t specified any table for parsing")
            sys.exit(1)



    def connect_db(self):
        try:
            self.conn = psycopg2.connect("dbname='%s' user='%s' host='localhost' password='%s'" % (
                            DATABASES["default"]["NAME"],
                            DATABASES["default"]["USER"],
                            DATABASES["default"]["PASSWORD"] ))
            cur = self.conn.cursor()
        except Exception as e:
            logging.info("[ERROR IN connect_db ]: %s" % e)
            sys.exit(1)
        return cur



    def stop_db_connection(self, cur):
        try:
            if self.conn:
                self.conn.close()
        except Exception as e:
            logging.info("[CLOSING DB ERROR]: %s" % e )




    def search_string_composer(self):
        try:
            book = xlrd.open_workbook(self.file)
            sh = book.sheet_by_index(0)
        except Exception as ex:
            logging.info("[XLS READING ERROR]: %s" % ex)
            sys.exit(1)

        for i in range(1, sh.nrows):
            row_dict = {}
            row_dict['counter'] = int((unicode(sh.row(i)[2].value).split(".")[0]).encode("utf-8"))
            row_dict['url'] = sh.row(i)[0].value
            optimisation_string  = unicode(sh.row(i)[1].value)
            self.optimisation_data[optimisation_string]= row_dict
            self.search_string_list.append(optimisation_string)



    def query(self):
        cur = self.connect_db()
        for search_string in self.search_string_list:
            tables_dict = {}
            search_string = re.sub("[`';]","_", search_string, re.U)
#            search_string = re.sub("\A\w","_", search_string, re.U)
            for table in self.tables:
                ids_list = []
                query_command_all = "SELECT id FROM %s WHERE description LIKE '%%%s%%'" % (table, search_string)
                query_command_news = u"SELECT id FROM news WHERE body LIKE '%%%s%%'" % search_string
                if table == 'news':
                    query_command_all = query_command_news
                cur.execute(query_command_all)
                rows = cur.fetchall()
                for row in rows:
                    ids_list.append(row[0])
                if len(ids_list)>0:
                    tables_dict[table] = ids_list
            if tables_dict.values():
                self.db_ids_data[search_string] = tables_dict.copy()
#        print self.db_ids_data

        with open("optim_2.txt","w") as file:
            i = 0
            for key, value in self.db_ids_data.iteritems() :
#                    print key, value
                file.write("%i)\t%s\t%s\n\n" % (i,(u"".join(key)).encode("utf-8"), value))
                i += 1
        cur.close()



    def link_finder(self,  string_to_parse, start_search_string):
        # Control that search expression not inside <a href=''></a>
        # params:
            # string_to_parse - string in which we looking for link tags
            # start_search_string - index (int) of beginning  of search expression in the string_to_parse
        # return values:
            # True - not inside <a href=""></a>
            # False - search expression is inside link tag

        last_link_start_index = None
        last_link_close_index = None
        start_link_pattern = re.compile("(?uim)<\s{0,3}a\s{1,3}href\s{0,3}=")
        close_link_pattern = re.compile("(?uim)<\s{0,3}/\s{0,3}a\s{0,3}>")
        processed_string = string_to_parse[0:start_search_string]
        res_start = re.finditer(start_link_pattern, processed_string)
        if res_start:
            end_pos = 0
            for item in res_start:
                item_end_pos = item.endpos
                if item_end_pos > end_pos:
                    end_pos = item_end_pos
            last_link_start_index = end_pos
        res_end = re.finditer(close_link_pattern, processed_string)
        if res_end:
            end_pos = 0
            for item in res_end:
                item_end_pos = item.endpos
                if item_end_pos > end_pos:
                    end_pos = item_end_pos
            last_link_close_index = end_pos
        if not last_link_start_index and not last_link_close_index:
#            print "links not found in text"
            return True
        elif last_link_start_index < last_link_close_index:
#            print "Founded last link closed before search expression"
            return True
        elif not last_link_start_index and last_link_close_index:
#            print "Founded only close link tag before. Please correct the text"
            return True
        else:
#            print "It seams to be search expression inside link"
            return False



    def parser(self):
        for key in self.db_ids_data.keys():
            url = self.optimisation_data [key]['url']
            counter = self.optimisation_data[key]["counter"]
            table_name = None
            # Choose table and list of entity ids
            while (True):
                table_name = self.tables[randint(0,len(self.tables)-1)]
                try:
                    selected_table_ids_list = self.db_ids_data[key][table_name]
                    break
                except Exception:
                    pass
            # Randomly selected id
            selected_id = selected_table_ids_list[randint(0,len(selected_table_ids_list)-1)]
#            print table_name,  selected_id
            try:
                cur = self.connect_db()
            except Exception as ex:
                logging.info("[DB ERROR in parser]: %s" % ex)
            if table_name == "news":
                query = "SELECT body FROM news WHERE id = %s" % selected_id
            else:
                query = "SELECT description FROM %s WHERE id = %s" % (table_name, selected_id)
            try:
                cur.execute(query)
                row = cur.fetchone()

            except Exception as e:
                logging.info("[DB ERROR in parser]: %s" % e)
            if row:
#                print row[0]
                string = row[0].decode("utf-8")
            else:
                logging.info("[ERROR IN QUERY (parser)]: %s" % query)
                continue
            # Search for keyword in text
            key_pattern = "(?ium)%s" % key
            pattern = re.compile(key_pattern)
#            print key
            start_search_string = None
            end_search_string = None
            if re.search(pattern,string):
                start_search_string = re.search(pattern,string).start()
                end_search_string = re.search(pattern,string).end()
            else:
                continue
            # Testing search string if not seized by link tags
            result = self.link_finder(string, start_search_string)
            if not result:
                continue
            #Found expression serrounded by link and decreased 1 from total amount,
            #if total amount equal zero - delete note(key) from dictionary (self.optimisation_data)
            link = "<a href='%s'>" % url
            string = string[0:start_search_string] + link + string[start_search_string:end_search_string]+ \
                     "</a> "+ string[end_search_string+1:]
#            print string
            counter = countr - 1
            if counter>0:
                self.optimisation_data[key]["counter"] = counter
            else:
                del self.optimisation_data[key]
#                print "item deleted"
            # Altering table with a modified string
            query = "UPDATE TABLE %s set description='%s' WHERE id=%s " % (table_name, string, selected_id)
            if table_name == "news":
                query = "UPDATE TABLE news set body=%s WHERE id=%s" %(string, selected_id)
            try:
                cur.execute(query)
            except Exception as e:
                logging.info("[ERROR WHILE SAVING DATA TO DB]: %s" % e)
                continue
            # Saving used id to list
            if selected_id not in self.used_once_ids:
                self.used_once_ids.append(selected_id)
            if selected_id not in self.used_twice_ids and selected_id in self.used_once_ids:
                self.used_twice_ids.append(selected_id)
        #TODO: пропоную створити таблиць БД seo_used_ids(cols: used_ones, used_twice)
        #TODO: записувати данні з кожного виклику парсера в дану таблицю
        cur.close()
        self.stop_db_connection(cur)


if __name__ == "__main__":
    file = "perelinkowka.xls"
    tables = ["product",'brand','category', 'news']
    o = SEO_Optimiser(file, tables)
    o.search_string_composer()
    o.query()
    o.parser()


