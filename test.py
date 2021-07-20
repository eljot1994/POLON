from elsapy.elsclient import ElsClient
from elsapy.elsprofile import ElsAuthor, ElsAffil
from elsapy.elsdoc import FullDoc, AbsDoc
from elsapy.elssearch import ElsSearch
import json


# con_file = open("config.json")
# config = json.load(con_file)
# con_file.close()
#
# client = ElsClient(config['apikey'])
# client.inst_token = config['insttoken']
#
# doc_srch = ElsSearch("AUTH(John and Min) AND AF-ID(60008555) AND PUBYEAR > 2016", 'scopus')
# doc_srch.execute(client, get_all=True)
#
# print(doc_srch.tot_num_res)
#
#
# doc_srch = ElsSearch("AUTH(John and M) AND AF-ID(60008555) AND PUBYEAR > 2016", 'scopus')
# doc_srch.execute(client, get_all=True)
# print(doc_srch.tot_num_res)
tab = [1,2,3,4,5]
tab_2 = [tab] * 10
print([x[0] for x in tab_2])

