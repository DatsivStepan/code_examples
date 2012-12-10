#!/usr/bin/env python
#! encoding: utf-8

# description: goods parser - creates new items of Products in database parsing xls files
# version: 0.1
# date: 2012-11-30


import csv
import decimal
from django.template.defaultfilters import slugify
from django.core.files.images import ImageFile
import os
import re
import simplejson as json
import sys
import time
import xlrd
import logging
import zipfile

from ecommerce.categories.models import Category
from ecommerce.products.models import Product, Brand, ProductImage
from utils.tools.aromart_tools import price_splitter, slugger
from ecommerce.settings import TEMP_DIR



logging.basicConfig(filename="", level=logging.INFO)
class GoodsParser(object):
    #   variables:
        #   file - csv file with parsed data
        #   brand - string, brand name
        #   brand_categories - xls file with mapped to our category tree category names

    def __init__(self,file, brand,brand_categories_file, flag=False):
        self.file = file
        self.flag = flag  # values: True (new) or False (old)
        self.images_archive = None
        self.brand = brand
        self.brand_categories = brand_categories_file
        self.categories_map = {}
        self.categories_ids = {}

        self.images_archive_finder()

        if self.brand_categories:
            brand_file_name = "%s_%s.xls" % (self.brand, int(round(time.time())))
            temp_path = os.path.join(TEMP_DIR, brand_file_name)
            with open(temp_path, "wb") as destination:
                for chunk in self.brand_categories.chunks():
                    destination.write(chunk)
            self.brand_categories.close()
            self.brand_categories = temp_path


    def images_archive_finder(self):
        pattern = "(%s_\d+)(\.\w+){0,3}\.zip" % slugger(self.brand.lower().strip())
        pattern = re.compile(pattern)
        for file in os.listdir(TEMP_DIR):
            if re.match(pattern, file):
                if zipfile.is_zipfile(os.path.join(TEMP_DIR, file)):
                    self.images_archive = file
                    break


    def processor(self):
        try:
            reader = csv.reader(self.file, delimiter="\t")
            rownum = 0
            total_dict = {}
            for row in reader:
                item_dict = {}
                # Save header row.
                if rownum == 0:
                    header = row
                else:
                    colnum = 0
                    for col in row:
                        item_dict[header[colnum]] = col
                        colnum += 1
                total_dict[rownum] = item_dict
                rownum += 1
        except Exception as e:
            error_str = "[ERROR in processor]: %s" % e
            logging.info(error_str)
#        for item in total_dict.values():
#            print [(key, value) for  key, value in item.items() if re.match("v_categories_name_\d_\d", str(key)) ]

        self.mapper(total_dict)
        # This step is optional
#        self.save_to_JSON(total_dict)
#        self.get_categories_names(total_dict)


    def get_categories_names(self,  total_dict):
        # Makes set of all parsed categories
        # for mapping purpose
        categories = []
        key_p = re.compile("v_categories_name_\d_\d")
        keys = [key for key in total_dict[1].iterkeys() if re.match(key_p,key)]
        for entity in total_dict.values():
            for key in keys:
                if key in entity.keys():
                    categories.append(entity[key])
        categories = set(categories)
        for category in categories:
            print category


    def save_to_JSON(self, total_dict):
        to_json = json.dumps(total_dict, sort_keys=True, indent=4, encoding="utf-8")
        with open("parsed.json", "w") as pj:
            pj.write(to_json)


    def _categories_xls_parser(self):
        # Parses xls file, creates categories mapping
        # return: two dictionaries
        # Attention: in xls file
                                #   first column - parsed site categories
                                #   second column - Aromart categories
        categories_map = {}
        categories_ids = {}
        try:
            book = xlrd.open_workbook(self.brand_categories)
            sh = book.sheet_by_index(0)
        except Exception as e:
            logging.info("[ERROR]: %s" % e)
            sys.exit(1)
        for i in range(1, sh.nrows):
            key = sh.row(i)[0].value.strip()
            value = sh.row(i)[1].value.split("-->")[-1].strip() #value = sh.row(i)[1].value.strip()
            if value:
                categories_map[key] = value
        for key, value in categories_map.items():#
            try:
                cat = Category.objects.get(name = value)
                id = cat.id
                categories_ids[value] = id
            except Exception as e:
                logging.info("[ERROR] The caterory: %s doesn't exist. Can't find it id" % value)
                del categories_map[key]
        return categories_map, categories_ids


    def _category_checker(self, entity, total_dict):
        # return Aromart category name - id dict
        entity_aromart_category_ids = []
        if not self.categories_map and not self.categories_ids:
            self.categories_map, self.categories_ids = self._categories_xls_parser()
        key_p = re.compile("v_categories_name_\d_\d")
        keys = [key for key in total_dict[1].keys() if re.match(key_p,key)]
        aromart_category = ""
        for key in keys:
            if key in entity.keys():
                outer_cat = entity[key]
            if not outer_cat:
                continue
            outer_cat = u"".join(outer_cat.decode("utf-8"))
            if outer_cat in self.categories_map.keys():
                aromart_category = self.categories_map[outer_cat]
            if not aromart_category:
                continue
            aromart_category_id = self.categories_ids[aromart_category]
            entity_aromart_category_ids.append(aromart_category_id)
        entity_aromart_category_ids = set(entity_aromart_category_ids)
        return entity_aromart_category_ids



    def mapper(self, total_dict):
        if self.flag:
            brand = Brand.objects.create(
                                             name = self.brand,
                                             description = self.brand,
                                             slug = slugger(self.brand)
                                            )
        else:
            try:
                brand = Brand.objects.get(name = self.brand)
            except Exception as e:
                logging.info("[ERROR in MAPPER]: %s" % e )
                sys.exit(1)
        for entity in total_dict.values():
            if entity:
                entity_aromart_category_ids = self._category_checker(entity, total_dict)

                if not len(entity_aromart_category_ids):
                    continue

                slug = slugify(self.brand) + "-" + slugger(entity["v_products_name_1"].strip().decode("utf-8"))#.decode("utf-8"))
                slug = slug[0:250]
                name =  entity["v_products_name_1"].decode("utf-8")[0:250]
                short_name = entity["v_products_name_1"].decode("utf-8")[0:250]

                product, created  = Product.objects.get_or_create(
                    brand = brand,
                    name =  name,     # max_length=255)
                    sku = entity["v_products_model"],        # max_length=50
                    slug = slug,
                    short_name = short_name
                )
                if created:
    #                short_name = models.CharField(max_length=255)
                    product.description = entity["v_products_description_1"]
                    product.title = entity["v_products_meta_title_1"]
                    product.meta_keywords = entity["v_products_meta_keywords_1"].decode("utf-8")[0:250]
                    product.meta_description = entity["v_products_meta_description_1"].decode("utf-8")[0:250]

                    parsed_price = decimal.Decimal(price_splitter(str(entity["v_products_price"])))

                    product.base_price = decimal.Decimal(round(parsed_price * decimal.Decimal(0.6), 2))
                    product.price = parsed_price

                    categories = Category.objects.filter(pk__in = entity_aromart_category_ids)
                    for category in categories:
                        product.category.add(category)
                    #TODO: Прописати алгоритм для створення короткої назви товару
                    #TODO: Прописати алглритм збереження картинки "v_products_image"
                    if self.images_archive and "v_products_image" in entity.keys() and entity["v_products_image"]:
                        image_file_name = entity["v_products_image"]
                        zip_file = zipfile.ZipFile(os.path.join(TEMP_DIR, self.images_archive))
                        for filename in zip_file.namelist():
                            filename_splitted = filename.split("/")[-1]
                            if  filename_splitted == image_file_name:
#                                print filename_splitted
                                path = zip_file.extract(filename)
                                title = self.brand + " " + filename
                                with open(path, "rb") as i_f:
                                    file = ImageFile(i_f)
                                    pi = ProductImage.objects.create(
                                                                        title = product.name,
                                                                        product = product,
                                                                        image = file,
                                                                        primary = True
                                    )
                                    pi.save()
                else:
                    if product.description != entity["v_products_description_1"].decode("utf-8"):
                        product.description = entity["v_products_description_1"]
                    if product.title != entity["v_products_meta_title_1"].decode("utf-8"):
                        product.title = entity["v_products_meta_title_1"]
                    if product.meta_keywords != entity["v_products_meta_keywords_1"].decode("utf-8")[0:250]:
                        product.meta_keywords = entity["v_products_meta_keywords_1"]
                    if product.meta_description != entity["v_products_meta_description_1"].decode("utf-8")[0:250]:
                        product.meta_description = entity["v_products_meta_description_1"]
                    if product.price !=  decimal.Decimal(price_splitter(str(entity["v_products_price"]))):
                        product.price = decimal.Decimal(price_splitter(str(entity["v_products_price"])))
                    # TODO: Вибрати усі категорії перевірити з розпарсеними і скоригувати при потребі
                product.save()


if __name__ == "__main__":
    file = "ofra.csv"
    gp = GoodsParser(file,"ofra", "Сопоставление категорий.xls")
#    gp.processor()

