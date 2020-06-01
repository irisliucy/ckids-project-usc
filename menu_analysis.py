import csv
import sys
import itertools
import numpy as np
import matplotlib.pyplot as plt
import requests
import pprint
import json
import glob
from usda import UsdaClient

client = UsdaClient('ohrJBZWi8Ggdf00mMWbax5fTBFc4mRm0i8kFGu6D')
CITY = 'Los Angeles'
CLIENT_ID = 'WB4STVV0BKOZGPDTSYPOKL1PCMN2ENFIE0UEJQF4PIMJPCGU' #Foursquare ID
CLIENT_SECRET = 'SNGR2XVXL4BTDRQBQJHLEYYE2ZXDCAQADNMOILCU34ZCGO4H' #Foursquare Secret
VERSION = '20181201'
#CATEGORY_ID = '4bf58dd8d48988d14e941735' #Main Food category

#foodcategory_ids={"burgers":"4bf58dd8d48988d16c941735","american":"4bf58dd8d48988d14e941735","mexican":"4bf58dd8d48988d1c1941735","fastfood":"4bf58dd8d48988d16e941735","salad":"4bf58dd8d48988d1bd941735"}
venuenames_ids={}

def calculate_dailyvalue(nut1,nut, nutrient_name, nutrient,portion):
    nut[nutrient_name]=(nutrient.value/portion)*100
    if nutrient.name.lower() in nut1:
        nut1[nutrient_name]=nut1[nutrient_name]+((nutrient.value/portion)*100)
    else:
        nut1[nutrient_name]=((nutrient.value/portion)*100)


#1. Read the 5 category venues and get a list of all restaurants under those categories.
for i in foodcategory_ids:
    url = 'https://api.foursquare.com/v2/venues/search?client_id={}&client_secret={}&v={}&categoryId={}&near={}'.format(
        CLIENT_ID, 
        CLIENT_SECRET,
        VERSION, 
        foodcategory_ids[i], 
        CITY)
    results = requests.get(url).json()
    with open('venuedata_'+i+'.json', 'w') as f:
        json.dump(results, f)

#2. Get all venue id in order to get menu's for all the venues found in the above.
all_venues_files=['/Users/spoortinidagundi/Desktop/GRIDS/MD/venuedata_american.json','/Users/spoortinidagundi/Desktop/GRIDS/MD/venuedata_burgers.json','/Users/spoortinidagundi/Desktop/GRIDS/MD/venuedata_fastfood.json','/Users/spoortinidagundi/Desktop/GRIDS/MD/venuedata_mexican.json','/Users/spoortinidagundi/Desktop/GRIDS/MD/venuedata_salad.json']
all_venues={}

for i in all_venues_files:
    with open(i,'r') as results:
        data=json.load(results)
    venue=data['response']['venues']
    for i in venue:
        name=i['name']
        all_venues[name]=i['id']


#2. Get menu's for all the above venue id's
for venue in all_venues.values():
	url = 'https://api.foursquare.com/v2/venues/'+all_venues[venue]+'/menu?client_id={}&client_secret={}&v={}'.format(
    CLIENT_ID, 
    CLIENT_SECRET,
    VERSION
    )
	results = requests.get(url).json()
	with open('/Users/spoortinidagundi/Desktop/GRIDS/MD/data_'+venue+'.json', 'w') as f:
		json.dump(results, f)


#4. Analyse each menu item for a venue and analyze the nutrional content for each using usda nutrient database
nut={}
main_nut=["energy","protein","total lipid (fat)","carbohydrate","iron","sodium","cholesterol"]

for f in menu_items:
    foods_search = client.search_foods(f.lower(), 1)
    food = next(foods_search)
    print(food)

    report = client.get_food_report(food.id)

    for nutrient in report.nutrients:
        #print(nutrient.name, nutrient.value, nutrient.unit)

        nutrient_name=nutrient.name.lower().split(',')[0]
        if any(key.startswith(nutrient_name) for key in main_nut):
            if nutrient.name.lower() in nut:
                nut[nutrient_name]=nut[nutrient_name]+nutrient.value
            else:
                nut[nutrient_name]=nutrient.value

menu_analysis="/Users/spoortinidagundi/Desktop/GRIDS/MD/Menus/menu_data_nutrient.csv"
csvfile=open(menu_analysis,'w')
obj = csv.writer(csvfile)
obj.writerow(["Location","Menu_Item","Energy","Protein","Total lipid(fat)","Carbohydrate","Fiber","Sodium","Cholesterol"])

path='/Desktop/GRIDS/MD/Menus/'
menu_files = [f for f in glob.glob(path + "**/*.json", recursive=True)]
total_nutrient_data={}

for f in menu_files:
    menu_items=[]
    total_nutrient_d={}
    location_name=f.split('/')[-1:][0].split('_')[1].split('.')[0]
    with open(f,'r') as results:
        data=json.load(results)
    if(len(data['response']['menu']['menus']['items'])==1):
        menuData=data['response']['menu']['menus']['items'][0]['entries']['items']
    else:
        menuData=data['response']['menu']['menus']['items'][1]['entries']['items']

    for i in menuData:
        if(i['entries']['items']):
            for j in i['entries']['items']:
                menu_items.append(j['name'])
        else:
            menu_items.append(i['name'])
    nut={}
    nut1={}
    count=0
    d={}
    main_nut=["energy","protein","total lipid (fat)","carbohydrate","fiber","sodium","cholesterol"]
    for f in menu_items:
        #To get the nutrient decomposition for each.
        nut={"energy":0,"protein":0,"total lipid (fat)":0,"carbohydrate":0,"fiber":0,"sodium":0,"cholesterol":0}
        try:
            foods_search = client.search_foods(f.lower(), 1)
            food = next(foods_search)
            report = client.get_food_report(food.id)
            for nutrient in report.nutrients:
                nutrient_name=nutrient.name.lower().split(',')[0]
                ''' 
                    Based on the DV information, a person who eats 2,000 calories per day should consume:
                        less than 65 grams or 585 calories from fat
                        less than 20 grams or 180 calories from saturated fat
                        at least 300 grams or 1200 calories from carbohydrates
                        approximately 50 grams or 200 calories from protein
                        less than 2,400 milligrams of sodium
                        less than 300 milligrams of cholesterol
                        about 25 grams of dietary fiber
                '''
                
                if nutrient_name.startswith("energy"):
                    nut[nutrient_name]=(nutrient.value/2000)*100
                    #Based on daily value composition
                    calculate_dailyvalue(nut1,nut, nutrient_name, nutrient,2000)

                elif nutrient_name.startswith("protein"):
                    #Based on daily value composition
                    calculate_dailyvalue(nut1,nut, nutrient_name, nutrient,50)

                elif nutrient_name.startswith("total lipid (fat)"):
                    #Based on daily value composition
                    calculate_dailyvalue(nut1,nut, nutrient_name, nutrient,65)

                elif nutrient_name.startswith("carbohydrate"):
                    #Based on daily value composition
                    calculate_dailyvalue(nut1,nut, nutrient_name, nutrient,300)

                elif nutrient_name.startswith("fiber"):
                    #Based on daily value composition
                    calculate_dailyvalue(nut1,nut, nutrient_name, nutrient,25)

                elif nutrient_name.startswith("sodium"):
                     #Based on daily value composition
                    calculate_dailyvalue(nut1,nut, nutrient_name, nutrient,2400)

                elif nutrient_name.startswith("cholesterol"):
                    nut[nutrient_name]=(nutrient.value/300)*100
                    #Based on daily value composition
                    calculate_dailyvalue(nut1,nut, nutrient_name, nutrient,300)
        except:
            continue
        obj.writerow([location_name,food,nut["energy"],nut["protein"],nut["total lipid (fat)"],nut["carbohydrate"],nut["fiber"],nut["sodium"],nut["cholesterol"]])
        count=count+1

    nut1_new={}
    for i in nut1:
        #take average
        nut1_new[i]=nut1[i]/count
    
    if(nut1_new):
        fig=plt.figure()
        plt.style.use('ggplot')
        nutrients=['energy', 'protein', 'fat', 'carbohydrate', 'fiber','sodium','cholesterol']
        nutrients_pos = [i for i, _ in enumerate(nutrients)]
        composition=list(nut1_new.values())
        plt.bar(nutrients_pos, composition, color='blue')
        plt.xlabel("Nutrient")
        plt.ylabel("% Daily Value")
        plt.title(location_name)
        plt.xticks(nutrients_pos, nutrients)
        plt.savefig(location_name+'.png')
    total_nutrient_data[location_name]=nut1_new

















