import csv
import requests
import json

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
    def __init__(self, name):
        self.name = name
        self.employer = []
        self.N = 0
        self.N0 = 0
        self.publications = []
        self.optimize = []

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
                    self.publications.append([author,row])
            else:
                self.N0 += author.N
        self.publications = sorted(self.publications,key=lambda x: x[1].PuU, reverse=True)

    def showPublications(self):
        self.updatePublications()
        print(self.name, self.N)
        for publication in self.publications:
            print(publication[0].secondName,publication[1])

    def showOptimize(self,ifShow):
        self.N -= self.N0
        N_temp = 0
        for publication in self.publications:
            if N_temp + publication[1].U <= self.N*2-1 and publication[1].year not in ['2017','2018'] and publication[0].slots - publication[1].U >= 0:
                self.optimize.append(publication)
                N_temp += publication[1].U
                publication[0].slots -= publication[1].U
        for publication in self.publications:
            if N_temp + publication[1].U <= self.N*3 and publication[1].year in ['2017', '2018'] and publication[0].slots - publication[1].U >= 0:
                self.optimize.append(publication)
                N_temp += publication[1].U
                publication[0].slots -= publication[1].U
        for publication in self.publications :
            if N_temp + publication[1].U <= self.N*3 and publication[0].slots - publication[1].U >= 0:
                self.optimize.append(publication)
                N_temp += publication[1].U
                publication[0].slots -= publication[1].U
        all_slots = 0
        all_points = 0
        for publication in self.optimize:
            all_slots += publication[1].U
            all_points += publication[1].Pu
            if ifShow:
                print(publication[0].secondName,publication[1])
        print('Sloty:',all_slots,'Punkty:',all_points,'N:',self.N,'N0:',self.N0)

institutions = []
with open('Instytucje_Sumelka.csv', mode='r', encoding='utf-8-sig') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=';')
    for row in csv_reader:
        institutions.append(row)
    csv_file.close()

for institution in institutions:

    r = requests.get(
        "https://radon.nauka.gov.pl/opendata/polon/employees?resultNumbers=100&employingInstitutionUuid="+institution[0]+"&disciplineName=matematyka&penaltyMarker=false").json()

    uczelnia = University(institution[1])

    print(uczelnia.name)
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
                                            numberOfDiscipline, primary))
    uczelnia.showEmployer()