#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unicodedata
import requests
from elsapy.elsclient import ElsClient
from elsapy.elsprofile import ElsAuthor, ElsAffil
from elsapy.elsdoc import FullDoc, AbsDoc
from elsapy.elssearch import ElsSearch
import json
import csv
import d2b

discipline = 'matematyka'

letters = {'ł': 'l', 'ą': 'a', 'ń': 'n', 'ć': 'c', 'ó': 'o', 'ę': 'e', 'ś': 's', 'ź': 'z', 'ż': 'z'}
trans = str.maketrans(letters)

con_file = open("config.json")
config = json.load(con_file)
con_file.close()

client = ElsClient(config['apikey'])
client.inst_token = config['insttoken']

Uczelnie = []

list_publications_19_21 = []
with open('Wykaz_czasopism_2019_2021.csv', encoding="utf8") as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=';')
    for row in csv_reader:
        list_publications_19_21.append(row)
    csv_file.close()

column_discipline = list_publications_19_21[0].index(discipline)

list_publications_17_18 = []
with open('Wykaz_czasopism_2017_2018.csv', encoding="utf8") as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=';')
    for row in csv_reader:
        list_publications_17_18.append(row)
    csv_file.close()


class Publication:
    def __init__(self,year, allAuthors, title, type, publisherOrJournal, m, k, ifInDiscipline,Pc):
        self.allAuthors = allAuthors
        self.title = title
        self.type = type
        self.publisherOrJournal = publisherOrJournal
        self.k = k
        self.m = m
        self.ifInDiscipline = ifInDiscipline
        self.Pc = Pc
        self.year = year

    def __str__(self):
        return 'Rok: %s\tCzy: %s\tTyp: %s\tPc: %i\tm: %s\tk: %s\tTytul: %s\tAutorzy: %s' % (self.year,self.ifInDiscipline,
            self.type,self.Pc, self.m, self.k, self.title, self.allAuthors)


class Author:
    def __init__(self, firstName, secondName, numberOfDisciplines=1, primaryJob=True):
        self.firstName = firstName
        self.secondName = secondName
        self.publications = []
        self.disciplines = numberOfDisciplines
        self.N = 1 / self.disciplines
        self.slots = 4 * self.N
        self.primaryJob = primaryJob

    def addPublication(self, publication):
        self.publications.append(publication)

    def __str__(self):
        return '------------------------\nImie: %s\t Nazwisko: %s\t N: %s\t Podstawowe: %s' % (
            self.firstName, self.secondName, self.N, self.primaryJob)


class University:
    def __init__(self, name):
        self.name = name
        self.employer = []

    def addEmployer(self, author):
        self.employer.append(author)

    def showPublications(self):
        for author in self.employer:
            print(author)
            for publications in author.publications:
                print(publications)

    def showEmployer(self):
        for author in self.employer:
            print(author)


# j = json.dumps(r, indent=2)
# print(j)

r = requests.get(
    "https://radon.nauka.gov.pl/opendata/polon/employees?resultNumbers=100&employingInstitutionName=Politechnika%20Pozna%C5%84ska&disciplineName=matematyka").json()
j = json.dumps(r, indent=2, ensure_ascii=False)

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
                uczelnia.addEmployer(Author(element['personalData']['firstName'], element['personalData']['lastName'],
                                            numberOfDiscipline, primary))

for uczelnia in Uczelnie:
    uni_name = ' and '.join(uczelnia.name.translate(trans).split(' '))
    aff_srch = ElsSearch('affil(' + uni_name + ')', 'affiliation')
    aff_srch.execute(client)
    uni_id = aff_srch.results[0]['dc:identifier'].split(':')[-1]

    for author in uczelnia.employer:
        author_name = author.secondName.split('-')[0] + ' and ' + author.firstName
        doc_srch = ElsSearch("AUTH(" + author_name + ") AND AF-ID(" + uni_id + ") AND PUBYEAR > 2016", 'scopus')
        doc_srch.execute(client, get_all=True)

        if doc_srch.tot_num_res == 0:
            author_name = author.secondName.split('-')[0] + ' and ' + author.firstName[0]
            doc_srch = ElsSearch("AUTH(" + author_name + ") AND AF-ID(" + uni_id + ") AND PUBYEAR > 2016", 'scopus')
            doc_srch.execute(client, get_all=True)

        if doc_srch.tot_num_res > 0:
            for doc in doc_srch.results:
                ifInDiscipline = 0
                #try:
                Pc=0
                print(doc)
                issn = doc['prism:issn'][:4] + '-' + doc['prism:issn'][4:]

                for record in list_publications_19_21:
                    if record[3] == issn or record[6] == issn:
                        Pc = int(record[8])
                        break
                if record[column_discipline] == 'x':
                    ifInDiscipline = 1

                if doc['prism:coverDate'][:4] in ['2017','2018']:
                    for record in list_publications_17_18:
                        if len(record)>1:
                            if record[1] == issn:
                                Pc = int(record[3])
                                break

                try:
                    bibtex = d2b.get_bibtex_entry(doc['prism:doi'])
                    authors = [y for y in [x.split(' and')[0] for x in bibtex['author'].split(' and ')] if len(y) > 2]
                except:
                    authors = [author.firstName+' '+author.secondName,doc['dc:creator']]

                numberOfAuthors = len(authors)
                numberOfAuthorsWithAffil = 0
                for author_s in authors:
                    for second_author in uczelnia.employer:
                        firName = second_author.firstName.translate(trans).lower()
                        secName = second_author.secondName.translate(trans).lower()
                        auth = author_s.translate(trans).lower()
                        if (firName in auth and secName in auth) or (firName[0] in auth and secName in auth):
                            numberOfAuthorsWithAffil += 1
                # except:
                #
                #     numberOfAuthors = 1
                #     authors = doc['dc:creator']
                #     numberOfAuthorsWithAffil = 1
                if numberOfAuthorsWithAffil == 0:
                    numberOfAuthorsWithAffil = 1
                publication = Publication(doc['prism:coverDate'][:4],authors, doc['dc:title'], doc['subtypeDescription'],
                                          doc['prism:publicationName'], numberOfAuthors, numberOfAuthorsWithAffil,ifInDiscipline,Pc)
                if Pc==0:
                    print("TUTAJ")
                    print(publication)
                    print(doc)

                author.addPublication(publication)
    uczelnia.showPublications()
    """r = requests.get("https://radon.nauka.gov.pl/opendata/polon/publications?resultNumbers=100&firstName="+element['personalData']['firstName']+"&lastName="+element['personalData']['lastName']+"&yearFrom=2016").json()
                        for pozycja in r['results']:
                            autorzy = ""
                            for x in pozycja['authors']:
                                autorzy += x['name'] + ' ' + x['lastName'] + ','
                            publikacja = Publication(allAuthors=autorzy[:-1],title=pozycja['title'],type=pozycja['type'],publisherOrJournal='',k='')
                            autor.addPublication(publikacja)"""
