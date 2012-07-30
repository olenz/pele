import numpy as np
from numpy import cos, sin
from copy import copy
from pygmin.potentials.xyspin import XYModel




def angle2vec(a):
    return np.array( [cos(a), sin(a)] )

def printspins(fout, pot, angles):
    nspins = len(angles)
    for node in pot.G.nodes():
        i = pot.indices[node]
        s = angle2vec(angles[i])
        fout.write("%g %g " % (node[0], node[1]) )
        fout.write("%g %g\n" % (s[0], s[1]) )
        


pi = np.pi
L = 6
nspins = L**2

#phases = np.zeros(nspins)
pot = XYModel( dim = [L,L], phi = np.pi) #, phases=phases)


angles = np.random.uniform(-pi, pi, nspins)
print angles

e = pot.getEnergy(angles)
print "energy ", e



#try a quench
from pygmin.optimize.quench import mylbfgs
ret = mylbfgs(angles, pot.getEnergyGradient)

print "quenched e = ", ret[1]
print ret[0]


#set up and run basin hopping

from pygmin.basinhopping import BasinHopping
from pygmin.takestep.displace import RandomDisplacement
from pygmin.takestep.adaptive import AdaptiveStepsize
from pygmin.storage import savenlowest

#should probably use a different take step routine  which takes into account
#the cyclical periodicity of angles
takestep = RandomDisplacement(stepsize = np.pi/4)
takestepa = AdaptiveStepsize(takestep, frequency = 20)
storage = savenlowest.SaveN(20)


bh = BasinHopping( angles, pot, takestepa, temperature = 1.01, storage = storage)
bh.run(200)

print "minima found"
with open("out.spin", "w") as fout:
    for min in storage.data:
        print "energy", min.E
        fout.write("#%g\n" % (min.E))
        printspins(fout, pot, min.coords)
        fout.write('\n\n')
        """
        view this in gnuplot with the command
        set size ratio -1
        plot 'out.spin' index 0 u 1:2 w p pt 5, '' index 0 u 1:2:($3*0.5):($4*0.5) w vectors
        """

try:
    lowest = storage.data[0].coords
    import matplotlib.pyplot as plt
    x = [node[0] for node in pot.G.nodes()]
    y = [node[1] for node in pot.G.nodes()]
    ilist = [pot.indices[node] for node in pot.G.nodes()]
    v0 = cos(lowest)
    v1 = sin(lowest)
    plt.quiver(x, y, v0, v1)
    a = plt.gca()
    a.set_xlim([-1, max(x)+1])
    a.set_ylim([-1, max(y)+1])
    plt.show()
except:
    print "problem ploting with matplotlib"

