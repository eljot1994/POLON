#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import unicodedata
import requests
from elsapy.elsclient import ElsClient
from elsapy.elsprofile import ElsAuthor, ElsAffil
from elsapy.elsdoc import FullDoc, AbsDoc
from elsapy.elssearch import ElsSearch
import json
import csv
import d2b
import os
import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.bibdatabase import BibDatabase
from bibtexparser.customization import convert_to_unicode

import unidecode

discipline = 'inżynieria mechaniczna'

ifN0 = 1

letters = {'ł': 'l', 'ą': 'a', 'ń': 'n', 'ć': 'c', 'ó': 'o', 'ę': 'e', 'ś': 's', 'ź': 'z', 'ż': 'z'}
trans = str.maketrans(letters)

con_file = open("config.json")
config = json.load(con_file)
con_file.close()

client = ElsClient(config['apikey'])
client.inst_token = config['insttoken']

download = False

output = []
Uczelnie = []
institutions = []
with open('Instytucje_Sumelka.csv', mode='r', encoding='utf-8-sig') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=';')
    for row in csv_reader:
        institutions.append(row)
    csv_file.close()

mdpi = []
with open('MDPI.csv',mode='r',encoding='utf-8-sig') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=';')
    for row in csv_reader:
        mdpi.append(row)
    csv_file.close()

authors = []
with open('Inz_mech_estawienie.csv', mode='r', encoding='utf-8-sig') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=';')
    for row in csv_reader:
        authors.append(row)
    csv_file.close()

list_publications_19_21 = []
with open('Wykaz_czasopism_2019_2021.csv', mode='r', encoding='utf-8-sig') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=';')
    for row in csv_reader:
        list_publications_19_21.append(row)
    csv_file.close()

column_discipline = list_publications_19_21[0].index(discipline)

list_publications_17_18 = []
with open('Wykaz_czasopism_2017_2018.csv', mode='r', encoding='utf-8-sig') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=';')
    for row in csv_reader:
        list_publications_17_18.append(row)
    csv_file.close()

publishers = []
with open('Wydawnictwa.csv', mode='r', encoding='utf-8-sig') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=';')
    for row in csv_reader:
        publishers.append(row)
    csv_file.close()


class Publication:
    def __init__(self, year, allAuthors, title, type, publisherOrJournal, m, k, ifInDiscipline, Pc):
        self.allAuthors = allAuthors
        self.title = title
        self.type = type
        self.publisherOrJournal = publisherOrJournal
        self.k = k
        self.m = m
        self.ifInDiscipline = ifInDiscipline
        self.mdpi=False
        self.Pc = Pc
        for m in mdpi:
            if m[1]==doc['prism:issn']:
                self.Pc = Pc/2
                self.mdpi = True
            break
        self.year = year
        if year in ['2017', '2018']:
            if Pc >= 30:
                self.P = Pc
            elif Pc >= 20:
                if (k / m) ** (1 / 2) < 1 / 10:
                    self.P = 1 / 10 * Pc
                else:
                    self.P = (k / m) ** (1 / 2) * Pc
            else:
                if (k / m) < 1 / 10:
                    self.P = 1 / 10 * Pc
                else:
                    self.P = (k / m) * Pc
        else:
            if Pc >= 100:
                self.P = Pc
            elif Pc >= 40:
                if (k / m) ** (1 / 2) < 1 / 10:
                    self.P = 1 / 10 * Pc
                else:
                    self.P = (k / m) ** (1 / 2) * Pc
            else:
                if (k / m) < 1 / 10:
                    self.P = 1 / 10 * Pc
                else:
                    self.P = (k / m) * Pc
        self.Pu = self.P / k
        if Pc != 0 and k != 0:
            self.U = self.P / Pc * 1 / k
        else:
            self.U = 0.0
        if self.U or self.Pu != 0:
            self.PuU = self.Pu / self.U
        else:
            self.PuU = 0

    def __str__(self):
        return 'Rok: %s\tTyp: %s\tPc: %i\tm: %s\tk: %s\tP: %.2f\tU: %.2f\tPu: %.2f\tTytul: %s\tAutorzy: %s\tCzy: %s' % (
        self.year,
        self.type, self.Pc, self.m, self.k, self.P, self.U, self.Pu, self.title, self.allAuthors, self.ifInDiscipline)


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
        return 'Imie: %s\t Nazwisko: %s\t N: %s\t Podstawowe: %s' % (
            self.firstName, self.secondName, self.N, self.primaryJob)

    def showPublications(self):
        for publication in self.publications:
            print(publication)


class University:
    def __init__(self, name, ID, dirName):
        self.name = name
        self.employer = []
        self.N = 0
        self.N0 = 0
        self.publications = []
        self.optimize = []
        self.scopusID = ID
        self.dirName = dirName

    def addEmployer(self, author):
        self.employer.append(author)
        self.N += author.N

    def showPublicationsAuthors(self):
        for author in self.employer:
            print(author)
            for publications in author.publications:
                print(publications)

    def showEmployer(self):
        for author in self.employer:
            print(author)
        print('---------------------------------------')

    def updatePublications(self):
        for author in self.employer:
            if len(author.publications) != 0:
                for row in author.publications:
                    self.publications.append([author, row])
            else:
                self.N0 += author.N
        self.publications = sorted(self.publications, key=lambda x: x[1].PuU, reverse=True)

    def showPublications(self):
        self.updatePublications()
        print(self.name, self.N)
        for publication in self.publications:
            print(publication[0].secondName, publication[1])

    def showOptimize(self, ifShow):
        self.updatePublications()
        self.N -= self.N0 * ifN0
        if self.N == 0:
            return
        N_temp = 0
        for publication in self.publications:
            if N_temp + publication[1].U <= self.N * 2 - 1 and publication[1].year not in ['2017', '2018'] and \
                    publication[0].slots - publication[1].U >= 0:
                self.optimize.append(publication)
                N_temp += publication[1].U
                publication[0].slots -= publication[1].U
        for publication in self.publications:
            if N_temp + publication[1].U <= self.N * 3 and publication[1].year in ['2017', '2018'] and publication[
                0].slots - publication[1].U >= 0:
                self.optimize.append(publication)
                N_temp += publication[1].U
                publication[0].slots -= publication[1].U
        for publication in self.publications:
            if N_temp + publication[1].U <= self.N * 3 and publication[0].slots - publication[1].U >= 0:
                self.optimize.append(publication)
                N_temp += publication[1].U
                publication[0].slots -= publication[1].U
        all_slots = 0
        all_points = 0
        for publication in self.optimize:
            all_slots += publication[1].U
            all_points += publication[1].Pu
            if ifShow:
                print(publication[0].secondName, publication[1])
        print('Sloty:', all_slots, 'Punkty:', all_points, 'N:', self.N, 'N0:', self.N0, 'Punkty/N:',
              all_points / self.N)
        output.append([self.name, self.N, self.N0, all_slots, all_points, all_points / self.N])


for institution in institutions:
    anagram = ''.join([s[0] for s in institution[1].split()]) + '_' + institution[2]
    Uczelnie.append(University(institution[1], institution[2], anagram))

    for author in authors:
        if author[7] == institution[1]:
            primary = False
            if author[10] == 'Tak':
                primary = True
            Uczelnie[-1].addEmployer(Author(author[2], author[5], len(author[11].split(',')), primary))
    """r = requests.get(
        "https://radon.nauka.gov.pl/opendata/polon/employees?resultNumbers=100&employingInstitutionUuid="+institution[0]+"&disciplineName=matematyka&penaltyMarker=false").json()

    for element in r['results']:
        for uczelnia_ele in element['employments']:
            if institution[1] in uczelnia_ele['employingInstitutionName']:
                numberOfDiscipline = 1
                primary = True
                if uczelnia_ele['basicPlaceOfWork'] == 'Nie':
                    primary = False
                if element['employments'][0]['declaredDisciplines']['secondDisciplineName'] != None:
                    numberOfDiscipline = 2
                uczelnia.addEmployer(Author(element['personalData']['firstName'], element['personalData']['lastName'],
                                            numberOfDiscipline, primary))"""

for uczelnia in Uczelnie:
    ile_mdpi=0
    print(uczelnia.name, Uczelnie.index(uczelnia) + 1, 'z', len(Uczelnie))
    print('---')
    uni_id = uczelnia.scopusID
    if len(uczelnia.employer) == 0:
        print('brak dyscypliny')
        continue
    if not os.path.exists('uczelnie/' + uczelnia.dirName + discipline):
        os.mkdir('uczelnie/' + uczelnia.dirName + discipline)

    for author in uczelnia.employer:

        print(author.firstName, author.secondName, uczelnia.employer.index(author) + 1, 'z', len(uczelnia.employer))

        if author.secondName == '-':
            continue

        if not os.path.exists(
                'uczelnie/' + uczelnia.dirName + discipline + '/' + author.firstName + '_' + author.secondName + '.txt'):
            bibtex_file = open(
                'uczelnie/' + uczelnia.dirName + discipline + '/' + author.firstName + '_' + author.secondName + '.txt',
                mode='w', encoding='utf-8-sig')

        if not os.path.exists(
                'uczelnie/' + uczelnia.dirName + discipline + '/' + author.firstName + '_' + author.secondName + '.json') or download:
            author_name = author.secondName.split('-')[0] + ' and ' + author.firstName
            doc_srch = ElsSearch("AUTH(" + author_name + ") AND AF-ID(" + uni_id + ") AND PUBYEAR > 2016", 'scopus')
            doc_srch.execute(client, get_all=True)

            if doc_srch.tot_num_res == 0:
                author_name = author.secondName.split('-')[0] + ' and ' + author.firstName[0]
                doc_srch = ElsSearch("AUTH(" + author_name + ") AND AF-ID(" + uni_id + ") AND PUBYEAR > 2016", 'scopus')
                doc_srch.execute(client, get_all=True)

            with open(
                    'uczelnie/' + uczelnia.dirName + discipline + '/' + author.firstName + '_' + author.secondName + '.json',
                    mode='w', encoding='utf-8-sig') as file:
                json.dump(doc_srch.results, file, ensure_ascii=False, indent=4)
                file.close()
            doc_srch = doc_srch.results
        else:
            with open(
                    'uczelnie/' + uczelnia.dirName + discipline + '/' + author.firstName + '_' + author.secondName + '.json',
                    mode='r',
                    encoding='utf-8-sig') as file:
                doc_srch = json.load(file)
                file.close()

        notEmpty = True
        try:
            if doc_srch[0]['error'] == "Result set was empty":
                notEmpty = False
        except:
            pass

        if notEmpty:
            for doc in doc_srch:
                issn = None
                eIssn = None
                bibtex_file = open(
                    'uczelnie/' + uczelnia.dirName + discipline + '/' + author.firstName + '_' + author.secondName + '.txt',
                    mode='r', encoding='utf-8-sig')

                try:
                    T = 0
                    for line in bibtex_file:
                        line = line.replace('\':', '\":').replace('{\'', '{\"').replace('\'}', '\"}').replace(': \'',
                                                                                                              ': \"').replace(
                            '\',', '\",').replace(', \'', ', \"')
                        bibtex = json.loads(line)
                        if doc['prism:doi'] == bibtex['doi']:
                            T = 1
                            break
                    if T == 0:
                        bibtex_file = open(
                            'uczelnie/' + uczelnia.dirName + discipline + '/' + author.firstName + '_' + author.secondName + '.txt',
                            mode='a', encoding='utf-8-sig')
                        bibtex = d2b.get_bibtex_entry(doc['prism:doi'])
                        bibtex_file.write(str(bibtex) + '\n')
                        bibtex_file.close()

                    '''bibtex_file = open(
                        'uczelnie/' + uczelnia.dirName+discipline + '/' + author.firstName + '_' + author.secondName + '.txt',
                        mode='r', encoding='utf-8-sig')
                    bibtext = bibtex_file.readline().replace('\'','\"')
                    print(json.loads(bibtext)['author'])

                    exit()'''

                    ifInDiscipline = 0
                    Pc = 0
                    prestige = 0
                    if doc['subtypeDescription'] != 'Article':
                        if bibtex == None:
                            break
                        for publisher in publishers:
                            if publisher[0].lower().translate(trans) == bibtex['publisher'].lower().translate(trans):
                                prestige = publisher[1]
                                break
                        if doc['subtypeDescription'] == 'Chapter':
                            czy_mono = True
                            if prestige == 2:
                                Pc = 50
                            elif prestige == 1:
                                Pc = 20
                            else:
                                Pc = 5
                        elif doc['subtypeDescription'] == 'Book':
                            czy_mono = True
                            if prestige == 2:
                                Pc = 200
                            elif prestige == 1:
                                Pc = 80
                            else:
                                Pc = 20
                    else:
                        try:
                            try:
                                issn = doc['prism:issn'][:4] + '-' + doc['prism:issn'][4:]
                            except:
                                eIssn = doc['prism:eIssn'][:4] + '-' + doc['prism:eIssn'][4:]

                            if issn == None:
                                issn = 'None'
                            if eIssn == None:
                                eIssn = 'None'

                            for record in list_publications_19_21:
                                if record[3] == issn or record[6] == issn or record[4] == eIssn or record[7] == eIssn:
                                    Pc = int(record[8])
                                    if record[column_discipline] == 'x':
                                        ifInDiscipline = 1
                                    break

                            if doc['prism:coverDate'][:4] in ['2017', '2018']:
                                for record in list_publications_17_18:
                                    if len(record) > 1:
                                        if record[1] == issn:
                                            Pc = int(record[3])
                                            break
                        except:
                            for record in list_publications_19_21:
                                if doc['prism:publicationName'].lower() == record[2].lower() or doc[
                                    'prism:publicationName'].lower() == record[5].lower():
                                    Pc = int(record[8])
                                    if record[column_discipline] == 'x':
                                        ifInDiscipline = 1
                                    break

                            if doc['prism:coverDate'][:4] in ['2017', '2018']:
                                for record in list_publications_17_18:
                                    if len(record) > 1:
                                        if record[0].lower() == doc['prism:publicationName'].lower():
                                            Pc = int(record[3])
                                            break
                    try:
                        authors = [y for y in [x.split(' and')[0] for x in bibtex['author'].split(' and ')] if
                                   len(y) > 2]
                    except:
                        authors = [author.firstName + ' ' + author.secondName]
                        if author.secondName not in doc['dc:creator']:
                            authors.append(doc['dc:creator'])

                    numberOfAuthors = len(authors)
                    numberOfAuthorsWithAffil = 0
                    for author_s in authors:
                        for second_author in uczelnia.employer:
                            firName = unidecode.unidecode(second_author.firstName).lower()
                            secName = unidecode.unidecode(second_author.secondName).lower()
                            auth = unidecode.unidecode(author_s).lower()
                            if (firName in auth and secName in auth) or (firName[0] in auth and secName in auth):
                                numberOfAuthorsWithAffil += 1
                    numberOfAuthorsWithAffil = max(1, numberOfAuthorsWithAffil)

                    for m in mdpi:
                        if m[1] == doc['prism:issn']:
                            ile_mdpi +=1
                        break

                    for author_a in authors:
                        if ' ' + unidecode.unidecode(author.secondName).lower() in unidecode.unidecode(
                                author_a).lower():
                            publication = Publication(doc['prism:coverDate'][:4], authors, doc['dc:title'],
                                                      doc['subtypeDescription'],
                                                      doc['prism:publicationName'], numberOfAuthors,
                                                      numberOfAuthorsWithAffil, ifInDiscipline, Pc)

                            author.addPublication(publication)
                            # print(publication)
                            break
                except:
                    pass

    print('_____________________')
    uczelnia.showOptimize(False)
    print('MDPI: ',ile_mdpi)
    print('_____________________' * 5)

with open('Wynik' + discipline + 'MDPI.csv', mode='w', encoding='utf-8-sig') as csv_file:
    csv_writer = csv.writer(csv_file, delimiter=';')
    for row in output:
        csv_writer.writerow(row)
    csv_file.close()
