import random
import math
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from scipy.stats import vonmises
import numpy as np
import os,sys
sys.path.append("./src")  

from const import KAPPA, MU, LAMBDA
point_num = 1000

list_pi = [random.vonmisesvariate(MU, KAPPA) for i in range(point_num)]
list_x = [random.expovariate(LAMBDA) for i in range(point_num)]
tmp = []
for i in range(point_num):
    tmp.append([list_x[i]*math.cos(list_pi[i]), list_x[i]*math.sin(list_pi[i])])

df = pd.DataFrame(tmp)
fig = plt.figure(figsize=(10,6))
sns.kdeplot(df[0],df[1],
           cbar = True,    
           shade = True,   
           cmap = 'Reds_r',  
           shade_lowest=True,  
           n_levels = 10,   
           bw = .3
           )
 
sns.rugplot(df[0], color="g", axis='x',alpha = 0.5)
sns.rugplot(df[1], color="k", axis='y',alpha = 0.5)
plt.show()
fig, ax = plt.subplots(1, 1)
x = [i/1000 for i in range(-1000, 1000)]
ax.plot(x, vonmises.pdf(x, KAPPA),
       'r-', lw=5, alpha=0.6, label='vonmises pdf')       
plt.show()        