import re
import json
import linecache
import sys
import pprint as pp
from tqdm import tqdm, trange
from colorama import Fore
from multiprocessing import Pool, RLock, freeze_support
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client.acedbv2
coll_st = db.states_state
coll_co = db.counties_county
coll_ci = db.cities_city
coll_ra = db.registeredagents_registeredagent
coll_tel = db.registeredagents_telecom

def add_to_map(ob):
    return ob

res = coll_ra.aggregate( [{"$group": { "_id": { 'state': "$state", 'city': "$city" } } }])
result = list(map(add_to_map, res))
pp.pprint(result)
print(len(result))


states = coll_ra.find().distinct('state')
cities = coll_ra.find().distinct('city')
stl = len(states)
ctl = len(cities)
tot = stl*ctl
results = []

with tqdm(total=tot) as pbar:
    for i in states:
        s = coll_st.find_one({'statename': f"{i}".lower()})
        for n in cities:
            try:
                c = coll_ci.find({'stateid': s['id'], 'cityname': f"{n}".lower()})
                for k in c:
                    try:
                        results.append(f"{k['cityname']}".capitalize()+", "+f"{k['statename']}".capitalize())
                    except Exception as e:
                        pass
                pbar.update(1)
            except Exception as e:
                pbar.update(1)
                

print(results)
            


print(agent)
print(f"""<li class="othertradenames">Other Trade Names: {agent['othertradenames1']}</li>""" if agent['othertradenames1'] else "")



#  sitemap_urls.append(
#      "".join(
#          list(
#              map(
#                  lambda k: "".join(
#                      [
#                          f"""<url><loc>https://www.{s.sitename}.com""",
#                          urllib.parse.quote(
#                              f"""/registered-agents/search/{n}/{k.lower()}"""),
#                          "</loc></url>"
#                      ]
#                  ),
#                  coll_ra.find().distinct(n)
#              )
#          )
#      )
#  )


