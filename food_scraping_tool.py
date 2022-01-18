import os
import  requests
from bs4 import BeautifulSoup
import pandas as pd
import re




class watcher:
  
  def __init__(self):
    self.EAN_list = None
    self.df = None

    self.watchers_df = None
    self.watchers_data = []
    self.watchers_keys = []


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


  def string_cleaner(self, adict):
    for k,v in adict.items():
      if type(v) == str and v.strip() =='':
        adict[k] = None
      elif type(v) == str:
        adict[k] = v.strip().replace('non renseigné', 'None')
      elif type(v) == list:
        adict[k] = ', '.join(v)
    return adict



  def openfoodfacts_extractor(self, EAN):

    product_off = {'name_off':None, 'brand_off': None, 'quantity_off':None, 'labels_off':None, 'origins_off': None, 'packaging_off':None,
                   'cat_off':None, 'keywords_off':None, 
                   'eco_score_off':None, 'eco_grade_off':None, 'nutri_grade_off': None, 'nutri_score_off':None, 'nova_score_off':None}


    api = f'https://world.openfoodfacts.org/api/v0/product/{EAN}.json'
    request = requests.get(api, headers={'User-Agent': 'Mozilla/5.0'}).json()

    # inconsistent result of the api, implies to conditionnaly search for each elements

    if 'product' in list(request.keys()):
      for key in list(request['product'].keys()):
        if key == 'brands':
          product_off['brand_off'] = request['product']['brands']

        if key == 'labels':
          product_off['labels_off'] = request['product']['labels']

        if key == 'quantity':
          product_off['quantity_off'] = request['product']['quantity']

        if key == 'product_quantity' and product_off['quantity_off'] == None:
          product_off['quantity_off'] = request['product']['product_quantity']

        if key == 'product_name':
          product_off['name_off'] = request['product']['product_name']

        if key == '_keywords':
          product_off['keywords_off'] = request['product']['_keywords']

        if key == 'categories':
          product_off['cat_off'] = request['product']['categories']

        if key == 'ecoscore_score':
          product_off['eco_score_off'] = request['product']['ecoscore_score']

        if key == 'ecoscore_grade':
          product_off['eco_grade_off'] = request['product']['ecoscore_grade']

        if key == 'nova_group':
          product_off['nova_score_off'] = request['product']['nova_group']

        if key == 'nutriscore_grade':
          product_off['nutri_grade_off'] = request['product']['nutriscore_grade']

        if key == 'nutriscore_score':
          product_off['nutri_score_off'] = request['product']['nutriscore_score']

        if key == 'origins':
          product_off['origins_off'] = request['product']['origins']

        if key == 'packaging': 
          product_off['packaging_off'] = request['product']['packaging']
    
    else:
      pass

    product_off = self.string_cleaner(product_off)

    return product_off
  


  def food_watching_extractor(self, EAN):

    product_fw = {'name_fw':None, 'brand_fw': None, 'quantity_fw':None, 'labels_fw':'', 
                  'transformation_place_fw':None, 'comp_origins_fw': None, 'packaging_fw':None,
                  'cat_fw':'', 'nova_score_fw':None, 'nutri_score_fw':None }


    site = f'https://www.food-watching.com/produits/{EAN}.php'
    request =  requests.get(site, headers={'User-Agent': 'Mozilla/5.0'}).content.decode('utf-8','ignore')
    soup = BeautifulSoup(request,'html.parser')
    
    ## informations
    product_fw['name_fw'] = soup.find('h1').text
    ean = soup.find('div',{'class':'int'}).text.split(',')[0].split(':')[1].strip()
    product_fw['cat_fw'] = soup.find('div',{'class':'int'}).text.split(',')[1].strip()

    for div in soup.find('tr',{'class':'score'}).find_all('div'):
      if 'nutriscore' in div.text.lower():
        product_fw['nutri_score_fw'] = div.text.split(':')[1].strip()
      if 'nova score' in div.text.lower():
        product_fw['nova_score_fw'] = div.text.split(':')[0].split()[-1]

    for elm in soup.find('tr',{'class':'produit'}):
      if re.findall(r'marque?(.*)', elm.text.lower()):
        product_fw['brand_fw'] = re.findall(r'marque?(.*)', elm.text.lower())[0].split(':')[-1].strip()

      if re.findall(r'quantité?(.*)', elm.text.lower()):
        product_fw['quantity_fw'] = re.findall(r'quantité?(.*)', elm.text.lower())[0].split(':')[-1].strip()
        
      if re.findall(r'catégorie?(.*)', elm.text.lower()):
        for c in re.findall(r'catégorie?(.*)', elm.text.lower()):
          if product_fw['cat_fw'] != '':
            product_fw['cat_fw'] += ', ' + c.split(':')[-1].strip()
          else:
            product_fw['cat_fw'] += c.split(':')[-1].strip()
      
      if re.findall(r'emballage?(.*)', elm.text.lower()):
        product_fw['packaging_fw'] = re.findall(r'emballage?(.*)', elm.text.lower())[0].split(':')[-1].strip()

      if re.findall(r'classification?(.*)', elm.text.lower()):
        for c in re.findall(r'classification?(.*)', elm.text.lower()):
          if product_fw['labels_fw'] != '':
            product_fw['labels_fw'] += ', ' + c.split(':')[-1].strip()
          else:
            product_fw['labels_fw'] += c.split(':')[-1].strip()

    for elm in soup.find('tr',{'class':'allergens'}):
      if re.findall(r'origine?(.*)', elm.text.lower()):
        product_fw['comp_origins_fw'] = re.findall(r'origine?(.*)', elm.text.lower())[0].split(':')[-1].strip()
      
      if re.findall(r'transformation?(.*)', elm.text.lower()):
        product_fw['transformation_place_fw'] = re.findall(r'transformation?(.*)', elm.text.lower())[0].split(':')[-1].strip()
    
    product_fw = self.string_cleaner(product_fw)

    return product_fw


  def glob_data(self, product_off, product_fw):
    self.watchers_keys = list(product_off.keys()) + list(product_fw.keys())
    watchers_vals = list(product_off.values()) + list(product_fw.values())

    self.watchers_data.append(watchers_vals)



  def build_DataFrame(self, merge=False):
    """merge default= False. if merge=True, merge current df with watchers collected data"""
    if merge == True and isinstance(fw.df, pd.DataFrame):
      self.watchers_df = pd.concat([self.df, pd.DataFrame(self.watchers_data, columns=self.watchers_keys)],axis=1)
      
    elif merge == False:
      data = [[self.EAN_list[i]] + self.watchers_data[i] for i in range(len(self.EAN_list))]
      self.watchers_df = pd.DataFrame(data, columns=self.watchers_keys)
    
    else:
      raise ValueError('df has not been imported yet')


  def solver(self):
    """try to solve original df data innacuraries and mistakes.
    Required to be used on top of:
    get_EAN_from_df()"""
    df = self.watchers_df

    df['nutri_score_fw'] = df['nutri_score_fw'].str.lower()
    df['cat_off'] = df['cat_off'].str.lower()
    df['cat_fw'] = df['cat_fw'].str.lower()
    df['packaging_fw'] = df['packaging_fw'].str.lower().replace('none','None')
    df['packaging_off'] = df['packaging_off'].str.lower()
    df['origins_off'] = df['origins_off'].str.lower()
    df['comp_origins_fw'] = df['comp_origins_fw'].str.lower().replace('none','None')
    df['brand_off'] = df['brand_off'].str.lower()
    df['brand_fw'] = df['brand_fw'].str.lower().replace('none','None')
    df['quantity_off'] = df['quantity_off'].str.lower()
    df['quantity_fw'] = df['quantity_fw'].str.lower().replace('none','None')


    df = df.fillna('None')

    # labels
    df['labels'] = df.apply(lambda x:'%s, %s' % (x['labels_off'],x['labels_fw']),axis=1)

    # merging nova
    df['nova_score_fw'] = [int(x) if type(x)==float else x for x in df['nova_score_fw'].values.tolist()]
    df['nova_score_off'] = [int(x) if type(x)==float else x for x in df['nova_score_off'].values.tolist()]
    df['nova_score'] = df.apply(lambda x:'%s, %s' % (x['nova_score_off'],x['nova_score_fw']),axis=1)
    df['nova_score'] = df['nova_score'].apply(lambda x: ', '.join(list(set([elm.strip() for elm in x.split(',')]))))
    df['nova_score'] = df['nova_score'].apply(lambda x: min(x.split(', ')))

    #merging nutriscore
    df['nutri_score'] = df.apply(lambda x:'%s, %s' % (x['nutri_grade_off'],x['nutri_score_fw']),axis=1)
    df['nutri_score'] = df['nutri_score'].apply(lambda x: ', '.join(list(set([elm.strip() for elm in x.split(',')]))))
    df['nutri_score'] = df['nutri_score'].apply(lambda x: min(x.split(', ')))

    # dtype nutri_score
    df['nutri_score_off'] = [int(x) if type(x)==float else x for x in df['nutri_score_off'].values.tolist()]

    # cat merging
    df['cat_more'] = df.apply(lambda x:'%s, %s' % (x['cat_off'],x['cat_fw']),axis=1)
    df['cat_more'] = df['cat_more'].apply(lambda x: x.replace('None','').replace('none','') if len(x.split(',')) > 1 else x)
    df['cat_more'] = df['cat_more'].apply(lambda x: ', '.join(list(filter(None,[elm.strip() for elm in x.split(',')]))))

    #packaging
    df['packaging'] = df.apply(lambda x:'%s, %s' % (x['packaging_off'],x['packaging_fw']),axis=1)
    df['packaging'] = df['packaging'].apply(lambda x: ', '.join(list(set([elm.strip() for elm in x.split(',')]))))
    # df['packaging'] = df['packaging'].apply(lambda x: max(x.replace('None','').split(', ')) if len(x.split(', ')) > 1 else x)

    #origins
    df['origins'] = df.apply(lambda x:'%s, %s' % (x['origins_off'],x['comp_origins_fw']),axis=1)
    df['origins'] = df['origins'].apply(lambda x: ', '.join(list(set([elm.strip() for elm in x.split(',')]))))
    df['origins'] = df['origins'].apply(lambda x: max(x.replace('None','').split(', ')) if len(x.split(', ')) > 1 else x)

    # brand
    df['marque_verif'] = df.apply(lambda x:'%s, %s' % (x['brand_off'],x['brand_fw']),axis=1)
    df['marque_verif'] = df['marque_verif'].apply(lambda x: ', '.join(list(set([elm.strip() for elm in x.split(',')]))))
    # df['brand'] = df['brand'].apply(lambda x: max(x.replace('None','').split(', ')) if len(x.split(', ')) > 1 else x)

    #quantity
    df['poid_verif'] = df.apply(lambda x:'%s, %s' % (x['quantity_off'],x['quantity_fw']),axis=1)
    df['poid_verif'] = df['poid_verif'].apply(lambda x: ', '.join(list(set([elm.strip() for elm in x.split(',')]))))
    df['poid_verif'] = df['poid_verif'].apply(lambda x: max(x.replace('None','').split(', ')) if len(x.split(', ')) > 1 else x)

    #name
    df['nom_verif'] = df.apply(lambda x:'%s, %s' % (x['name_off'],x['name_fw']),axis=1)
    df['nom_verif'] = df['nom_verif'].apply(lambda x: ', '.join(list(set([elm.strip() for elm in x.split(',')]))))
    df['nom_verif'] = df['nom_verif'].apply(lambda x: max(x.replace('None','').split(', ')) if len(x.split(', ')) > 1 else x)


    # rename and drop
    df = df.rename(columns={'eco_score_off':'eco_score',
                            'eco_grade_off':'eco_grade',
                            'nutri_score':'nutri_grade',
                            'nutri_score_off':'nutri_score',
                            'keywords_off':'keywords',
                            'transformation_place_fw':'transformation_place'})
    

    df = df.drop(['nova_score_fw','nova_score_off', 'name_fw', 'name_off',
                  'quantity_off', 'quantity_fw', 'brand_off', 'brand_fw',
                  'origins_off', 'comp_origins_fw', 'packaging_off', 'packaging_fw',
                  'cat_off', 'cat_fw', 'labels_off', 'labels_fw', 'nutri_grade_off'], axis=1)

    self.watchers_df = df




  def to_excel(self, output_path):
    self.watchers_df.to_excel(output_path, index=False)


  def run(self):
    for EAN in self.EAN_list:
      product_off = self.openfoodfacts_extractor(EAN)
      product_fw = self.food_watching_extractor(EAN)
      self.glob_data(product_off, product_fw)


if __name__ == '__main__':
  path = r'C:\Users\rom88\Desktop\prog\SQQ\tables_pusher\tables\cat_11_Farine _ Levure.xlsx'
  fw = watcher()
  fw.get_EAN_from_df(path)
  fw.run()
  fw.build_DataFrame(merge=True)
