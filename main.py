#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unicodedata
import requests
from elsapy.elsclient import ElsClient
from elsapy.elsprofile import ElsAuthor, ElsAffil
from elsapy.elsdoc import FullDoc, AbsDoc
from elsapy.elssearch import ElsSearch
import json

letters={'ł':'l', 'ą':'a', 'ń':'n', 'ć':'c', 'ó':'o', 'ę':'e', 'ś':'s', 'ź':'z', 'ż':'z'}
trans=str.maketrans(letters)

con_file = open("config.json")
config = json.load(con_file)
con_file.close()

client = ElsClient(config['apikey'])
client.inst_token = config['insttoken']

Uczelnie = []
class Publication:
    def __init__(self,allAuthors,title,type,publisherOrJournal,k):
        self.allAuthors = allAuthors
        self.title = title
        self.type = type
        self.publisherOrJournal = publisherOrJournal
        self.k = k
        self.m = len(self.allAuthors.split(','))

    def __str__(self):
        return 'Tytul: %s\nAutorzy: %s\nTyp: %s\nm: %s\n' % (self.title,self.allAuthors,self.type,self.m)


class Author:
    def __init__(self, firstName, secondName, numberOfDisciplines=1, primaryJob=True):
        self.firstName = firstName
        self.secondName = secondName
        self.publications = []
        self.disciplines = numberOfDisciplines
        self.N = 1/self.disciplines
        self.slots = 4*self.N
        self.primaryJob = primaryJob


    def addPublication(self,publication):
        self.publications.append(publication)


    def __str__(self):
        return 'Imie: %s\t Nazwisko: %s\t N: %s\t Podstawowe: %s'%(self.firstName,self.secondName,self.N,self.primaryJob)

class University:
    def __init__(self,name):
        self.name = name
        self.employer = []


    def addEmployer(self,author):
        self.employer.append(author)


    def showPublications(self):
        for author in self.employer:
            for publications in author.publications:
                print(publications)


    def showEmployer(self):
        for author in self.employer:
            print(author)

# j = json.dumps(r, indent=2)
# print(j)

r = requests.get("https://radon.nauka.gov.pl/opendata/polon/employees?resultNumbers=100&employingInstitutionName=Politechnika%20Pozna%C5%84ska&disciplineName=matematyka").json()
j = json.dumps(r, indent=2,ensure_ascii=False)

Uczelnie.append(University('Politechnika Poznańska'))

for element in r['results']:
    for uczelnia_ele in element['employments']:
        for uczelnia in Uczelnie:
            if uczelnia.name in uczelnia_ele['employingInstitutionName']:
                numberOfDiscipline = 1
                primary = True
                if uczelnia_ele['basicPlaceOfWork'] == 'Nie':
                    primary = False
                if element['employments'][0]['declaredDisciplines']['secondDisciplineName'] != None:
                    numberOfDiscipline = 2
                uczelnia.addEmployer(Author(element['personalData']['firstName'],element['personalData']['lastName'],numberOfDiscipline,primary))

for uczelnia in Uczelnie:
    uczelnia.showEmployer()
    uni_name = ' and '.join(uczelnia.name.translate(trans).split(' '))
    aff_srch = ElsSearch('affil('+uni_name+')','affiliation')
    aff_srch.execute(client)
    uni_id = aff_srch.results[0]['dc:identifier'].split(':')[-1]

    for author in uczelnia.employer:
        author_name = author.secondName.split('-')[0] + ' ' +author.firstName
        print(author_name.translate(trans))
        doc_srch = ElsSearch("AUTH("+author_name+") AND AF-ID("+uni_id+") AND PUBYEAR > 2016", 'scopus')
        doc_srch.execute(client, get_all=True)
        if len(doc_srch.results) == 1:
            author_name = author.secondName.split('-')[0] + ' ' + author.firstName[0]
            doc_srch = ElsSearch("AUTH(" + author_name + ") AND AF-ID(" + uni_id + ") AND PUBYEAR > 2016", 'scopus')
            doc_srch.execute(client, get_all=True)

        """r = requests.get("https://radon.nauka.gov.pl/opendata/polon/publications?resultNumbers=100&firstName="+element['personalData']['firstName']+"&lastName="+element['personalData']['lastName']+"&yearFrom=2016").json()
                        for pozycja in r['results']:
                            autorzy = ""
                            for x in pozycja['authors']:
                                autorzy += x['name'] + ' ' + x['lastName'] + ','
                            publikacja = Publication(allAuthors=autorzy[:-1],title=pozycja['title'],type=pozycja['type'],publisherOrJournal='',k='')
                            autor.addPublication(publikacja)"""