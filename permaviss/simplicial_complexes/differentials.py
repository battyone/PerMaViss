"""
    differentials.py

    This module computes the differentials of a given filtered complex.
    Put test that composition of differentials is 0
"""
import numpy as np

def complex_differentials(C, p):
    """
    Given a simplicial complex C, it returns a list D with its differentials mod p
    A simplicial complex C is assumed to have first entries the radius associated to the simplices.
    C[0] contains the edges, C[1] contains the 2-simplexes, and so on.
    D[0] contanins the number of points
    D[1] contains the 1st differential,
    D[2] contains the 2nd differential, and so on
    """
    dim = len(C) - 1  # get the dimension of the simplicial complex
    D = []
    for d in range(dim + 1):
        D.append([]) 

    D[0] = C[0] # number of points
    # create 1D boundary
    D[1] = np.zeros((C[0], np.size(C[1],0)))
    for i, c in enumerate(C[1]):
        D[1][int(c[0])][i] = 1
        D[1][int(c[1])][i] = p - 1
        

    # We proceed to compute all the differentials for all dimensions
    for d in range(2, dim + 1):
        """
            Go through all the d-simplexes of C, computing their images
            in (d-1)-simplex basis
        """
        D[d] = np.zeros((np.size(C[d-1],0), np.size(C[d],0)))
        for i, s in enumerate(C[d]):
            im = []  # initialize image of s
            signs = [] # also initialize signs of faces
            for j, c in enumerate(C[d - 1]):
                if len(np.intersect1d(c, s)) == d:
                    face_idx = np.setdiff1d(s, c)[0]
                    im.append(j)
                    signs.append((-1) ** np.searchsorted(s, face_idx))
            
            for j, v in enumerate(im):
                D[d][v][i] = signs[j] % p
                
             
    return D

#########################################################################################
# Test 1

import scipy.spatial.distance as dist

from .vietoris_rips import vietoris_rips

X = np.array(
    [[ 1.91580552,  0.57418571],
     [-0.72993636,  1.86203999],
     [ 1.97700111,  0.30243449],
     [ 1.99699445,  0.10960461],
     [-1.58839255,  1.21532264]])

Dist = dist.squareform(dist.pdist(X))
max_r = 3
max_dim = 4
p = 5
C, _ = vietoris_rips(Dist, max_r, max_dim)
Diff = complex_differentials(C, p)
res = np.matmul(Diff[1], Diff[2]) % p
assert np.array_equal(res, np.zeros((np.size(Diff[1],0), np.size(Diff[2],1))))
res = np.matmul(Diff[2], Diff[3]) % p
assert np.array_equal(res, np.zeros((np.size(Diff[2],0), np.size(Diff[3],1))))



