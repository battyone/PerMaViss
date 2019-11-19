"""
    persistence_algebra.py

    This module implements algebra functions for working with:
    -Barcode basis
    -Persistence vectors

"""
import numpy as np
import matplotlib.pyplot as plt


class barcode_basis(object):
    """
        This class implements barcode bases.
    """
    def __init__(self, bars, prev_basis=None, coordinates=np.array([[]]), store_well_defined=False, 
                 broken_basis=False, broken_differentials=None):
        """
            TO DO: change *coord for optional arguments
            Sorting is done outside, mainly because in some cases we
            need not to sort the result. A case is when we perform the quotient.
            Initialize barcode basis. 
            Order barcodes as well.
            Each coordinate is stored in a column, whereas bars are stored on rows.  
            INPUT:
                - bars: list of pairs specifiying birth and death radius of barcode.
                - prev_basis : reference to a previously defined barcode basis
                - coordinates : cooridnates of this basis in terms of prev_basis
                - store_well_defined : store the indices of well defined bars.
                - broken_basis: whether the barcode basis is broken. i.e. it is not really a barcode basis.
                - broken_differentials: a np.array containing the broken differentials.
        """
        # When the basis is broken, the death_differentials must be given as an np.array
        if broken_basis and type(broken_differentials) != type(np.array([])):
            raise ValueError

        self.broken_basis = broken_basis
        self.barcode = np.copy(bars)
        self.prev_basis = prev_basis
        self.coordinates = coordinates
        self.sorted = False
        # Take out trivial bars and also bad defined bars
        if len(bars)==0:
            self.dim = 0
        else:
            well_defined = self.barcode[:,0] < self.barcode[:,1]
            self.barcode = self.barcode[well_defined] 
            self.dim = np.sum(well_defined)

        # Add coordinates, checking for mistakes on the data.      
        if (prev_basis != None) and (np.size(coordinates,1) > 0):
            # Check that the given coordinates match the dimension of the previous basis
            if np.size(coordinates,0) != self.prev_basis.dim:
                print("Error:given coordinates do not match dimension of prev_basis")
                raise ValueError

            # check that same amount of coordinates as bars were given
            if np.size(bars,0) != np.size(coordinates, 1):
                print("Error:given {} bars but {} coordinates".format(len(bars), np.size(coordinates, 1)))
                raise ValueError
           
            self.coordinates = self.coordinates[:, well_defined]


        if store_well_defined:
            self.well_defined = well_defined
        
       
        # make sure the broken differentials are given as a square matrix of dimension self.dim 
        if broken_basis:
            if np.size(broken_differentials,0) == self.dim and np.size(broken_differentials,1)==self.dim:
                self.broken_differentials = broken_differentials 
            else:
                raise ValueError


    def __str__(self):
        """
        Printing function for barcode bases.  
        """
        print("Barcode basis")
        print(self.barcode)
        if self.prev_basis != None:
            print(self.coordinates)
        
        return ""


    def sort(self, precision=7, send_order=False):
        """
            Sorts a barcode basis according to the standard order.
            That is, from smaller birth radius to biger, and from 
            biger death radius to smaller. 
            A precision up to n zeros is an optional argument. 
        """
        
        aux_bars = np.around(self.barcode, decimals = precision)
        order = np.lexsort((-aux_bars[:,1], aux_bars[:,0]))
        if self.prev_basis != None:
            self.coordinates = self.coordinates[:, order]

        self.barcode = self.barcode[order]
        self.sorted = True
        if self.broken_basis:
            self.broken_differentials=self.broken_differentials[order]
            self.broken_differentials=self.broken_differentials[:,order]

        if send_order:
            return order
  
    ########################################################################### 
    # Functions used by Image_kernel:     

    def changes_list(self):
        """
            Returns an array with the values of changes occouring in the basis.
        """
        l = np.resize(self.barcode, (1, 2 * len(self.barcode)))
        return np.unique(l)
    
    def active(self, rad, start=0, end=-1):
        """
            Returns array with active indices at rad.
            Option to restrict to generators from start to self.dim
        """
        if end == -1:
            end = self.dim
        # end if    
        if start >= self.dim or (end > self.dim) or (end < 0):
            print("start:{}, end:{}, self.dim:{}".format(start, end, self.dim))
            raise ValueError
        # end if
        indices = np.array(range(end - start))
        active_bool = np.logical_and(self.barcode[:,0] <= rad, rad < self.barcode[:,1])
        return indices[active_bool[start:end]]


    def trans_active_coord(self, coord, rad, start=0):
        """
            Given coordinates on the active generators. 
            Obtain coordinates in the whole basis.
            This also can be done with coordinates starting from start to self.dim
        """
        trans_coord = np.zeros(self.dim - start)        
        trans_coord[self.active(rad, start)] = coord
        return trans_coord


    def death(self, rad, start=0):
        """
            Returns an array with the indices dying at rad.
            These indices are relative to the optional argument start.
        """
        if start >= self.dim:
            raise ValueError
        indices = np.array(range(self.dim - start))
        death_bool =  (self.barcode[:,1] == rad)
        return indices[death_bool[start:]]

    ###########################################################################
    # Functions used by spectral_sequence class

    def birth_radius(self, coordinates):
        """
            This finds the birth radius of a list of coordinates.
        """
        if not np.any(coordinates):
            return np.nan #returns nan if coordinates are zero
        
        return np.min(self.barcode[np.nonzero(coordinates)])
        
    def death_radius(self, coordinates):
        """
            Find the death radius of given coordinates. 
        """
        if not np.any(coordinates):
            return np.nan #returns nan if coordinates are zero
        
        return np.max(self.barcode[np.nonzero(coordinates)]) 
    
    def bool_select(self, selection):
        if self.prev_basis == None:
            return barcode_basis(self.barcode[selection])
        
        return barcode_basis(self.barcode[selection], self.prev_basis, self.coordinates[:, selection])

    def active_coordinates(self, rad):
        # Active submatrix of coordinates at rad
        A = np.copy(self.coordinates[:, self.active(rad)])
        return A[self.prev_basis.active(rad)]

    def active_domain(self, rad):
        # Active columns of coordinates at rad
        if self.dim == 0:
            return np.array([])
        else:
            return np.copy(self.coordinates[:, self.active(rad)])

    
    ###########################################################################
    # Function updating broken_differentials

    def update_broken(self, A, rad):
        """
        Updates a matrix A, using the broken differentials of the generators dying at rad.
        INPUT:
            -A: np.array whose columns represent coordinates in the barcode_basis.
            -rad: radius at which we want to update the coordinates using the broken_differentials.
        OUTPUT:
            -A: return updated matrix
        """
        dying_indices = self.death(rad)
        if len(dying_indices) > 0:
            sum_update = np.matmul(self.broken_differentials[:,dying_indices], A[dying_indices])
            A[dying_indices] = np.zeros((len(dying_indices), np.size(A,1)))
            A = A + sum_update
        
        return A


barcode = [[1,2],[1,4],[-0.25,5] ,[0.1,1]]
bas = barcode_basis(barcode)
order = bas.sort(send_order=True)
assert np.array_equal(order[np.argsort(order)],range(4))
assert np.array_equal(np.array([[-0.25,5.],[ 0.1,1.],[1.,4.],[1.,2.]]), bas.barcode)
assert np.array_equal(bas.active(1.1),np.array([0,2,3]))
assert np.array_equal(bas.active(1.1, start=2),np.array([0,1]))
assert np.array_equal(bas.trans_active_coord([0,1,1],1.2), np.array([0,0,1,1]))
assert np.array_equal(bas.death(4), np.array([2]))
assert np.array_equal(bas.death(4,start=2), np.array([0]))
assert bas.birth_radius(np.array([1,1,0,0])) == -0.25
assert bas.death_radius(np.array([1,1,0,1])) == 5
assert np.array_equal(bas.changes_list(), np.array([-0.25, 0.1, 1, 2, 4, 5]))

        
