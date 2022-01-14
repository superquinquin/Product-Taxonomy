import os
import  requests
from bs4 import BeautifulSoup
import pandas as pd
import re




class watcher:
  def __init__(self):
    self.EAN_list = None
    self.df = None


  def parse_EAN_list(self, EAN_list):
    """input list of EAN directly"""
    self.EAN_list = EAN_list


  def get_EAN_from_df(self, path):
    """input df containing EAN column.
    return ean columns as EAN_list"""
    self.df = pd.read_excel(path)

    for col in list(self.df.columns):
      if ('code' in col and 'barre' in col) or 'barcode' in col:
        barcode_col_name = col
    
    self.EAN_list = self.df[barcode_col_name].values.tolist()



  def openfoodfacts_extractor(self, EAN):

    product_off = {'brand': None, 'labels':None, 'quantity':None, 'name':None, 'keywords':None,
                  'cat':None, 'eco_score':None, 'eco_grade':None, 'nova_score':None,
                  'nutri_grade': None, 'nutri_score':None, 'origins': None, 'packaging':None}


    api = f'https://world.openfoodfacts.org/api/v0/product/{EAN}.json'
    request = requests.get(api, headers={'User-Agent': 'Mozilla/5.0'}).json()

    # inconsistent result of the api, implies to conditionnaly search for each elements

    if 'product' in list(request.keys()):
      for key in list(request['product'].keys()):
        if key == 'brands':
          product_off['brand'] = request['product']['brands']

        if key == 'labels':
          product_off['labels'] = request['product']['labels']

        if key == 'quantity':
          product_off['quantity'] = request['product']['quantity']

        if key == 'product_quantity' and product_off['quantity'] == None:
          product_off['quantity'] = request['product']['product_quantity']

        if key == 'product_name':
          product_off['name'] = request['product']['product_name']

        if key == '_keywords':
          product_off['keywords'] = request['product']['_keywords']

        if key == 'categories':
          product_off['cat'] = request['product']['categories']

        if key == 'ecoscore_score':
          product_off['eco_score'] = request['product']['ecoscore_score']

        if key == 'ecoscore_grade':
          product_off['eco_grade'] = request['product']['ecoscore_grade']

        if key == 'nova_group':
          product_off['nova_score'] = request['product']['nova_group']

        if key == 'nutriscore_grade':
          product_off['nutri_grade'] = request['product']['nutriscore_grade']

        if key == 'nutriscore_score':
          product_off['nutri_score'] = request['product']['nutriscore_score']

        if key == 'origins':
          product_off['origins'] = request['product']['origins']

        if key == 'packaging': 
          product_off['packaging'] = request['product']['packaging']
    
    else:
      pass

    return product_off
  


  def food_watching_extractor(self, EAN):

    product_fw = {'brand': None, 'labels':'', 'quantity':None, 'name':None,
                  'cat':'', 'nova_score':None, 'transformation_place':None,
                  'nutri_score':None, 'comp_origins': None, 'packaging':None}


    site = f'https://www.food-watching.com/produits/{EAN}.php'
    request =  requests.get(site, headers={'User-Agent': 'Mozilla/5.0'}).content.decode('utf-8','ignore')
    soup = BeautifulSoup(request,'html.parser')
    
    ## informations
    product_fw['name'] = soup.find('h1').text
    ean = soup.find('div',{'class':'int'}).text.split(',')[0].split(':')[1].strip()
    product_fw['cat'] = soup.find('div',{'class':'int'}).text.split(',')[1].strip()

    for div in soup.find('tr',{'class':'score'}).find_all('div'):
      if 'nutriscore' in div.text.lower():
        product_fw['nutri_score'] = div.text.split(':')[1].strip()
      if 'nova score' in div.text.lower():
        product_fw['nova_score'] = div.text.split(':')[0].split()[-1]

    for elm in soup.find('tr',{'class':'produit'}):
      if re.findall(r'marque?(.*)', elm.text.lower()):
        product_fw['brand'] = re.findall(r'marque?(.*)', elm.text.lower())[0].split(':')[-1].strip()

      if re.findall(r'quantité?(.*)', elm.text.lower()):
        product_fw['quantity'] = re.findall(r'quantité?(.*)', elm.text.lower())[0].split(':')[-1].strip()
        
      if re.findall(r'catégorie?(.*)', elm.text.lower()):
        for c in re.findall(r'catégorie?(.*)', elm.text.lower()):
          if product_fw['cat'] != '':
            product_fw['cat'] += ', ' + c.split(':')[-1].strip()
          else:
            product_fw['cat'] += c.split(':')[-1].strip()
      
      if re.findall(r'emballage?(.*)', elm.text.lower()):
        product_fw['packaging'] = re.findall(r'emballage?(.*)', elm.text.lower())[0].split(':')[-1].strip()

      if re.findall(r'classification?(.*)', elm.text.lower()):
        for c in re.findall(r'classification?(.*)', elm.text.lower()):
          if product_fw['labels'] != '':
            product_fw['labels'] += ', ' + c.split(':')[-1].strip()
          else:
            product_fw['labels'] += c.split(':')[-1].strip()

    for elm in soup.find('tr',{'class':'allergens'}):
      if re.findall(r'origine?(.*)', elm.text.lower()):
        product_fw['comp_origins'] = re.findall(r'origine?(.*)', elm.text.lower())[0].split(':')[-1].strip()
      
      if re.findall(r'transformation?(.*)', elm.text.lower()):
        product_fw['transformation_place'] = re.findall(r'transformation?(.*)', elm.text.lower())[0].split(':')[-1].strip()
    
    return product_fw

  
  def run(self):
    for EAN in self.EAN_list:
      product_off = self.openfoodfacts_extractor(EAN)
      product_fw = self.food_watching_extractor(EAN)

    

  
if __name__ == '__main__':
  fw = watcher()
  fw.get_EAN_from_df(path)
  fw.run()

  