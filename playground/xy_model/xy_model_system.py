import numpy as np

from pele.potentials import XYModel
from pele.potentials.xyspin import angle_to_2dvector
from pele.systems import BaseSystem
from pele.landscape import smoothPath


def spin_distance_1d(x1, x2):
    dx = x1 - x2
    # apply periodic boundary conditions
    L = 2. * np.pi
    dx -=  L * np.round(dx / L)
    return np.linalg.norm(dx)

def spin_mindist_1d(x1, x2):
    # apply periodic boundary conditions
    L = 2. * np.pi
    offset = L * np.round((x1 - x2) / L)
    x2 = x2 + offset
    print "max dist", np.max(np.abs(x1-x2))
    assert np.max(np.abs(x1-x2)) <= L/2.
    return np.linalg.norm(x1-x2), x1, x2
     

class XYModlelSystem(BaseSystem):
    def __init__(self, dim=[4, 4], phi_disorder=1.):
        BaseSystem.__init__(self)
        self.dim = dim
        self.phi_disorder = phi_disorder
        self.pot = self.get_potential()
        self.nspins = np.prod(dim)
        
        self.setup_params(self.params)

    def setup_params(self, params):
        params.takestep.stepsize = np.pi / 2.
        params.takestep.verbose = True
#        params.double_ended_connect.local_connect_params.NEBparams.interpolator = interpolate_spins
        params.double_ended_connect.local_connect_params.NEBparams.image_density = 3
        params.double_ended_connect.local_connect_params.NEBparams.reinterpolate = 50
#        params.double_ended_connect.local_connect_params.NEBparams.distance = spin3d_distance
        params.structural_quench_params.tol = 1e-6


    def get_potential(self):
        try:
            return self.pot
        except AttributeError:
            return XYModel(dim=self.dim, phi=self.phi_disorder)
    
    def get_orthogonalize_to_zero_eigenvectors(self):
        return None
    
    def get_metric_tensor(self, coords):
        return None
    
    def get_nzero_modes(self):
        return 1

    def get_pgorder(self, coords):
        return 1
    
    def get_mindist(self):
        return spin_mindist_1d

    def smooth_path(self, path, **kwargs):
        mindist = self.get_mindist()
        return smoothPath(path, mindist, **kwargs)

    def get_random_configuration(self):
        return np.random.uniform(0,2.*np.pi, self.nspins)

    def node2xyz(self, node):
        return np.array([float(x) for x in [node[0], node[1], 0]])
    

    def draw(self, coords, index):
        from pele.systems._opengl_tools import draw_cone
#        if self.one_frozen:
#            coords = self.coords_converter.get_full_coords(coords)
        d = .4
        r = .04
        nspins = coords.size
        com = sum(self.node2xyz(node) for node in self.pot.G.nodes())
        com /= nspins
        for node in self.pot.G.nodes():
            xyz = self.node2xyz(node)
            i = self.pot.indices[node]
            spin2 = angle_to_2dvector(coords[i])
            spin3 = np.zeros(3)
            spin3[:2] = spin2
            x1 = xyz - 0.5 * spin3 * d - com
            x2 = xyz + 0.5 * spin3 * d - com
            draw_cone(x1, x2, rbase=r)
    
def run_gui():
    from pele.gui import run_gui
    system = XYModlelSystem(dim=[10,10], phi_disorder=1.5)
    run_gui(system)

def test_potential():
    system = XYModlelSystem(dim=[10,10], phi_disorder=1.5)
    pot = system.get_potential()
    pot.test_potential(system.get_random_configuration())


if __name__ == "__main__":
#    test_potential()
    run_gui()
        
    
    
