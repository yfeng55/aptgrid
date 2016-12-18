import json
from pymongo import MongoClient
import math

#with open('sample_formatted.json') as data_file:    
#    listings = json.loads(data_file.read())

#with open('test.json') as data_file:    
#    test_listings = json.loads(data_file.read())

MIN_PRICE=200
SCAM_POSTERS=[]

def getSpamScore(listing, zscore):
    if listing["price"]<MIN_PRICE:
        return 0
    elif listing["listed_by"] in SCAM_POSTERS:
        return 0
    else:
        return max(0,(2.5*math.log(listing["num_photos"]+1)/1.39794000867)+(4.5*math.log(zscore+7))+(len(listing["description"])/500))

def get_db():
    connection = MongoClient('ds023654.mlab.com', 23654)
    db = connection['apartmentdb']
    db.authenticate('admin', 'craigslistsucks')
    return db

def main(listings, test_listings):
    #-------------------finding avg data for each neighborhood--------------------------------
    totalPrices={}
    counts={}
    avgPrice={}
    std_numerator={}
    std_deviataion={}
    db=get_db();
    dbtotal={}

    for listing in listings:
        key=listing["neighborhood"]+"_"+str(listing["num_beds"])
        if key in totalPrices:
            totalPrices[key]+=listing["price"]
            counts[key]+=1
        else:
            totalPrices[key]=listing["price"]
            counts[key]=1
        
    for key in totalPrices:
        temp_listing=db.neighborhoods.find("{name:"+key+"}")
        db_total_prices[key]=temp_listing["avg_price"]*temp_listing["count"]
        avgPrice[key]=(totalPrices[key]+db_total_prices[key])/(counts[key]+temp_listing["count"])
        db.neighborhoods.update_one({
            '_id': temp_listing["_id"]
            },{
              '$set': {
                "avg_price":avgPrice[key], 
                "count":existing + counts[key]

              }
            },upsert = False)

    #logging
    #print avgPrice

    for listing in listings:
        key=listing["neighborhood"]+"_"+str(listing["num_beds"])
        if key in std_numerator:
            std_numerator[key]+=pow(listing["price"]-avgPrice[key],2)
        else:
            std_numerator[key]=pow(listing["price"]-avgPrice[key],2)
        
    for key in std_numerator:
        std_deviataion[key]=(std_numerator[key]/counts[key])**0.5

    #logging
    #print std_deviataion


    #---------------------spam detection----------------------------------------------------------
    zscore={}
    spamScore={}

    for listing in test_listings:
        key=listing["neighborhood"]+"_"+str(listing["num_beds"])
        if std_deviataion[key]==0:
            zscore[listing["link"]]=0
        else:
            zscore[listing["link"]]=(listing["price"]-avgPrice[key])/std_deviataion[key]

        spamScore[listing["link"]]=getSpamScore(listing,zscore[listing["link"]])
        #print spamScore[listing["link"]]
        