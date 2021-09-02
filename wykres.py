# libraries
import matplotlib

matplotlib.use('Agg')
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# set width of bars
barWidth = 1
barWidth_bigger = 1


# set heights of bars
bars1 = []
bars2 = []
N=[]
uczelnie =[]

dane = []

with open('Wynik_I.csv','r',encoding='utf8') as file:
    for line in file:
        dane.append(line.replace(',','.').split(';'))
    dane =sorted(dane,key=lambda x: float(float(x[4])/(float(x[1])+float(x[2]))),reverse=False)
    for element in dane:
        uczelnie.append(element[0])
        bars1.append(float(element[4])/(float(element[1])+float(element[2])))
        bars2.append(float(element[5]))
        N.append([float(element[1]),float(element[2])])


# Set position of bar on X axis
r1 = [2*x for x in range(len(bars1))]
r2 = [x + barWidth for x in r1]

# Make the plot
for i, v in enumerate(bars2):
    plt.text(v+1, 2*i-0.125, str(round(v,2)), color='black', size=8)
for i, v in enumerate(bars1):
    plt.text(3, 2*i-0.125, str(round(v,2)), color='black', size=8)

plt.barh(r1, bars1, color='#79D3E6',height=barWidth, label='Nowe zasady')
plt.barh(r1, bars2,height=barWidth_bigger, label='Nowe zasady \n(bez N0)', fill=False, edgecolor='#4A76E6')

# Add xticks on the middle of the group bars
for i in range(len(uczelnie)):
    uczelnie[-i-1] = str(i+1)+'. '+ str(uczelnie[-i-1])+'  N='+str(round(sum(N[i]),2))+'  N0='+str(round(float(N[i][1]),2))

plt.yticks(r1, uczelnie,color='black')
plt.ylim([r1[0]-1,r2[-1]])


# Create legend & Show graphic
plt.legend()
figure = plt.gcf()

figure.set_size_inches(14, 20)
figure.tight_layout()
plt.savefig('wykres.jpg',dpi=600)