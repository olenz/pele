import unittest
import numpy as np
from testmindist import TestMinDist
from pygmin.mindist.minpermdist_stochastic import MinPermDistCluster
from pygmin.mindist._minpermdist_policies import MeasureAtomicCluster

class TestMinPermDistStochastic_BLJ(TestMinDist):
    def setUp(self):
        from pygmin.potentials.ljpshiftfast import LJpshift as BLJ
        from pygmin import defaults
        
        self.natoms = 25
        self.ntypeA = int(self.natoms * .8)
        self.pot = BLJ(self.natoms, self.ntypeA)
        self.permlist = [range(self.ntypeA), range(self.ntypeA, self.natoms)]
        
        self.X1 = np.random.uniform(-1,1,[self.natoms*3])*(float(self.natoms))**(1./3)/2
        
        #run a quench so the structure is not crazy
        ret = defaults.quenchRoutine(self.X1, self.pot.getEnergyGradient, **defaults.quenchParams)
        self.X1 = ret[0]
        

    def testBLJ(self):
        import pygmin.defaults
        X1 = np.copy(self.X1)
        X2 = np.random.uniform(-1,1,[self.natoms*3])*(float(self.natoms))**(1./3)/2
        
        #run a quench so the structure is not crazy
        ret = pygmin.defaults.quenchRoutine(X2, self.pot.getEnergyGradient)
        X2 = ret[0]

        self.runtest(X1, X2, MinPermDistCluster(measure=MeasureAtomicCluster(permlist=self.permlist)))


    def testBLJ_isomer(self):
        """
        test with BLJ potential.  We have two classes of permutable atoms  
        
        test case where X2 is an isomer of X1.
        """
        import pygmin.utils.rotations as rot
        X1i = np.copy(self.X1)
        X1 = np.copy(self.X1)        
        X2 = np.copy(X1)
        
        #rotate X2 randomly
        aa = rot.random_aa()
        rot_mx = rot.aa2mx( aa )
        for j in range(self.natoms):
            i = 3*j
            X2[i:i+3] = np.dot( rot_mx, X1[i:i+3] )
        
        #permute X2
        import random, copy
        from pygmin.mindist.permutational_alignment import permuteArray
        for atomlist in self.permlist:
            perm = copy.copy(atomlist)
            random.shuffle( perm )
            X2 = permuteArray( X2, perm)

        X2i = np.copy(X2)
        
        #distreturned, X1, X2 = self.runtest(X1, X2)
        distreturned, X1, X2 = self.runtest(X1, X2, MinPermDistCluster(measure=MeasureAtomicCluster(permlist=self.permlist)))

        
        #it's an isomer, so the distance should be zero
        self.assertTrue( abs(distreturned) < 1e-14, "didn't find isomer: dist = %g" % (distreturned) )

if __name__ == "__main__":
    unittest.main()