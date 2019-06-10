#!/usr/bin/python3

from numpy import *
import numpy as np
import os
import sys
import os.path
from athena import ATHENA_DIR

_na_lib_dir = os.path.join( ATHENA_DIR, 'tools', 'na_library')

"""
PDBGen Version 1.5
------------------

Contents
--------
  I. cndo_to_dnainfo
  II. Reference DNA classes (B-DNA)
  III. writePDBresidue
  IV. Matrix transformation functions
    1. getTransMat
    2. applyTransMat
    3. translate
    4. eultoaxisangle
    5. axisangletoeul
  V. Large number encoding functions
    1. base36encode
    2. hybrid36encode
  VI. Main pdbgen function
--------
  
"""

# I. cndo_to_dnainfo
# This function converts a .cndo data structure to a useable input
# for the main pdbgen function
def cndo_to_dnainfo(filename, inputdir):

    f = open(inputdir + filename + '.cndo', 'r')

    # Initialize variables to list
    dnaTop = []
    dNode = []
    triad = []
    id_nt = []

    # Read in the data structure
    for line in f:

        if 'dnaTop' in line:

            line = next(f)
            while line.strip() != '':
                linestr = line.strip()
                dnaTop.append(linestr.split(','))
                line = next(f)

        elif 'dNode' in line:

            line = next(f)
            while line.strip() != '':
                linestr = line.strip()
                dNode.append(linestr.split(','))
                line = next(f)

        elif 'triad' in line:

            line = next(f)
            while line.strip() != '':
                linestr = line.strip()
                triad.append(linestr.split(','))
                line = next(f)

        elif 'id_nt' in line:

            line = next(f)
            while line.strip() != '':
                linestr = line.strip()
                id_nt.append(linestr.split(','))
                # End of file requires this try-except break
                try:
                    line = next(f)
                except:
                    break

        else:
            pass

    return dnaTop, dNode, triad, id_nt

# II. Reference DNA Structures
# Class for reference B-DNA structure 

class BDNA(object):

    def __init__(self):

        """
        This class will parse the reference B-DNA files and return a 
        data structure which can be used during rotation of coordinate
        frames.

        Parameters
        ----------
        none

        Returns
        -------
        bdna:
            Structure that describes the PDB geometry of a reference 
            B-DNA assembly using the 3DNA convention.
            Substructures:
            AAA.scaf = adenine scaffold information
            AAA.stap = adenine staple information
            CCC.scaf = cytosine scaffold information
            CCC.stap = cytosine staple information
            GGG.scaf = guanine scaffold information
            GGG.stap = guanine staple information
            TTT.scaf = thymine scaffold information
            TTT.stap = thymine staple information

        Will load the reference files AAA.pdb, CCC.pdb, GGG.pdb, and TTT.pdb
        sequentially to acquire the necessary structural information.
        """

        # Run the basepairs
        self.AAA()
        self.CCC()
        self.GGG()
        self.TTT()

    def AAA(self):

        AAAtemp = np.loadtxt( os.path.join(_na_lib_dir, 'bdna_ath.pdb'), dtype=object)

        AAAlen = len(AAAtemp)

        # Calculate atoms in scaffold and staple strands
        scafatoms = 0
        stapatoms = 0

        for i in range(AAAlen):
            if AAAtemp[i,3] == 'ADE':
                scafatoms += 1
            elif AAAtemp[i,3] == 'THY':
                stapatoms += 1

        # Now transfer important PDB structural information to the refdna.bdna
        # object.

        # Initialize scaffold and staple structures
        self.Ascaf = np.zeros((scafatoms, 6), dtype=object)
        self.Tstap = np.zeros((stapatoms, 6), dtype=object)

        # Now transfer PDB structure line by line
        ss = 0
        aa = 0
        for i in range(AAAlen):

            # {atomtype, strand, residue, xcoord, ycoord, zcoord, atom}
            if AAAtemp[i,3] == 'ADE':
                self.Ascaf[ss,0] = AAAtemp[i,2]
                self.Ascaf[ss,1] = AAAtemp[i,4] 
                self.Ascaf[ss,2] = AAAtemp[i,5] 
                self.Ascaf[ss,3] = float(AAAtemp[i,6])
                self.Ascaf[ss,4] = float(AAAtemp[i,7])
                self.Ascaf[ss,5] = float(AAAtemp[i,8])
                ss += 1
            elif AAAtemp[i,3] == 'THY':
                self.Tstap[aa,0] = AAAtemp[i,2]
                self.Tstap[aa,1] = AAAtemp[i,4]
                self.Tstap[aa,2] = AAAtemp[i,5]
                self.Tstap[aa,3] = float(AAAtemp[i,6])
                self.Tstap[aa,4] = float(AAAtemp[i,7])
                self.Tstap[aa,5] = float(AAAtemp[i,8])
                aa += 1

        return self.Ascaf, self.Tstap
    
    def CCC(self):

        CCCtemp = np.loadtxt(os.path.join(_na_lib_dir, 'bdna_cgh.pdb'), dtype=object)

        CCClen = len(CCCtemp)

        # Calculate atoms in scaffold and staple strands
        scafatoms = 0
        stapatoms = 0

        for i in range(CCClen):
            if CCCtemp[i,3] == 'CYT':
                scafatoms += 1
            elif CCCtemp[i,3] == 'GUA':
                stapatoms += 1

        # Initialize scaffold and staple structures
        self.Cscaf = np.zeros((scafatoms, 6), dtype=object)
        self.Gstap = np.zeros((stapatoms, 6), dtype=object)

        # Now transfer PDB structure line by line
        ss = 0
        aa = 0

        # Now transfer important PDB structural information to the refdna.bdna
        # object.

        # Now transfer PDB structure line by line
        for i in range(CCClen):

            # {atomtype, strand, residue, xcoord, ycoord, zcoord, atom}
            if CCCtemp[i,3] == 'CYT':
                self.Cscaf[ss,0] = CCCtemp[i,2]
                self.Cscaf[ss,1] = CCCtemp[i,4]
                self.Cscaf[ss,2] = CCCtemp[i,5]
                self.Cscaf[ss,3] = float(CCCtemp[i,6])
                self.Cscaf[ss,4] = float(CCCtemp[i,7])
                self.Cscaf[ss,5] = float(CCCtemp[i,8])
                ss += 1
            elif CCCtemp[i,3] == 'GUA':
                self.Gstap[aa,0] = CCCtemp[i,2]
                self.Gstap[aa,1] = CCCtemp[i,4]
                self.Gstap[aa,2] = CCCtemp[i,5]
                self.Gstap[aa,3] = float(CCCtemp[i,6])
                self.Gstap[aa,4] = float(CCCtemp[i,7])
                self.Gstap[aa,5] = float(CCCtemp[i,8])
                aa += 1

        return self.Cscaf, self.Gstap

    def GGG(self):

        GGGtemp = np.loadtxt(os.path.join(_na_lib_dir, 'bdna_gch.pdb'), dtype=object)

        GGGlen = len(GGGtemp)

        # Calculate atoms in scaffold and staple strands
        scafatoms = 0
        stapatoms = 0

        for i in range(GGGlen):
            if GGGtemp[i,3] == 'GUA':
                scafatoms += 1
            elif GGGtemp[i,3] == 'CYT':
                stapatoms += 1

        # Initialize scaffold and staple structures
        self.Gscaf = np.zeros((scafatoms, 6), dtype=object)
        self.Cstap = np.zeros((stapatoms, 6), dtype=object)

        # Now transfer PDB structure line by line
        ss = 0
        aa = 0

        for i in range(GGGlen):

            # {atomtype, strand, residue, xcoord, ycoord, zcoord, atom}
            if GGGtemp[i,3] == 'GUA':
                self.Gscaf[ss,0] = GGGtemp[i,2]
                self.Gscaf[ss,1] = GGGtemp[i,4]
                self.Gscaf[ss,2] = GGGtemp[i,5]
                self.Gscaf[ss,3] = float(GGGtemp[i,6])
                self.Gscaf[ss,4] = float(GGGtemp[i,7])
                self.Gscaf[ss,5] = float(GGGtemp[i,8])
                ss += 1
            elif GGGtemp[i,3] == 'CYT':
                self.Cstap[aa,0] = GGGtemp[i,2]
                self.Cstap[aa,1] = GGGtemp[i,4]
                self.Cstap[aa,2] = GGGtemp[i,5]
                self.Cstap[aa,3] = float(GGGtemp[i,6])
                self.Cstap[aa,4] = float(GGGtemp[i,7])
                self.Cstap[aa,5] = float(GGGtemp[i,8])
                aa += 1

        return self.Gscaf, self.Cstap

    def TTT(self):

        TTTtemp = np.loadtxt(os.path.join(_na_lib_dir, 'bdna_tah.pdb'), dtype=object)

        TTTlen = len(TTTtemp)

        # Calculate atoms in scaffold and staple strands
        scafatoms = 0
        stapatoms = 0

        for i in range(TTTlen):
            if TTTtemp[i,3] == 'THY':
                scafatoms += 1
            elif TTTtemp[i,3] == 'ADE':
                stapatoms += 1

        # Initialize scaffold and staple structures
        self.Tscaf = np.zeros((scafatoms, 6), dtype=object)
        self.Astap = np.zeros((stapatoms, 6), dtype=object)

        # Now transfer PDB structure line by line
        ss = 0
        aa = 0

        # Now transfer PDB structure line by line
        for i in range(TTTlen):

            # {atomtype, strand, residue, xcoord, ycoord, zcoord, atom}
            if TTTtemp[i,3] == 'THY':
                self.Tscaf[ss,0] = TTTtemp[i,2]
                self.Tscaf[ss,1] = TTTtemp[i,4]
                self.Tscaf[ss,2] = TTTtemp[i,5]
                self.Tscaf[ss,3] = float(TTTtemp[i,6])
                self.Tscaf[ss,4] = float(TTTtemp[i,7])
                self.Tscaf[ss,5] = float(TTTtemp[i,8])
                ss += 1
            elif TTTtemp[i,3] == 'ADE':
                self.Astap[aa,0] = TTTtemp[i,2]
                self.Astap[aa,1] = TTTtemp[i,4]
                self.Astap[aa,2] = TTTtemp[i,5]
                self.Astap[aa,3] = float(TTTtemp[i,6])
                self.Astap[aa,4] = float(TTTtemp[i,7])
                self.Astap[aa,5] = float(TTTtemp[i,8])
                aa += 1

        return self.Tscaf, self.Astap


# III. Functions for writing a PDB file atom-by-atom
# Requires current chain, resnum, restype

def writePDBresidue(filename, chain, chainnum, resnum, atomnum, mmatomnum,
                    segatomnum, restype, refatoms, basecrds, numchains, fid,
                    outputdir, fpdb, fmm, fseg):

    # Check that file lengths are consistent
    if len(refatoms) != len(basecrds[:,0]):
        fid.write('...Error: Base coord data is inconsistent. Aborting...\n')
    else:
        pass
    
    # This function will append coordinates to a PDB file residue by residue
    # 1. Single-model PDB with alphanumeric chains

    # Do not build this model if numchains > 63
    if numchains <= 63:

        #f = open(outputdir + filename + '.pdb', 'a')

        fid.write('...Chain ' + str(chain) + ', Residue ' + str(resnum) + \
                  ' printing coordinates...\n')

        element = ' '
        # Please see official PDB file format documentation for more 
        # information www.wwpdb.org/documentation/file-format
        #
        for i in range(len(refatoms)):
            # Data type: Record Name: Cols 1 - 6
            fpdb.write('{0:<6s}'.format('ATOM'))
            # Data type: Atom serial number: Cols 7 - 11
            if atomnum < 100000:
                fpdb.write('{0:>5d}'.format(int(atomnum)))
            else:
                hybatomnum = hybrid36encode(atomnum,5)
                fpdb.write('{0:>5s}'.format(str(hybatomnum)))
                #f.write('*****')
            fpdb.write(' ') # <-- One blank space
            # Data type: Atom name: Cols 13 - 16
            # This one is complicated and depends on size of string
            if len(str(refatoms[i])) == 1:
                fpdb.write(' ' + '{0:>1s}'.format(str(refatoms[i])) + '  ')
                element = str(refatoms[i])
            elif len(str(refatoms[i])) == 2:
                fpdb.write(' ' + '{0:>2s}'.format(str(refatoms[i])) + ' ')
                element = str(refatoms[i])[0]
            elif len(str(refatoms[i])) == 3:
                fpdb.write(' ' + '{0:>3s}'.format(str(refatoms[i])))
                element = str(refatoms[i])[0]
            elif len(str(refatoms[i])) == 4:
                fpdb.write('{0:>4s}'.format(str(refatoms[i])))
                element = str(refatoms[i])[1]
            # Data type: Alternate location indicator: Col 17 
            # <-- This is typically empty
            fpdb.write(' ')
            # Data type: Residue name: Cols 18 - 20
            fpdb.write('{0:>3s}'.format(str(restype)))
            # Data type: Chain identifier: Col 22 <-- Insert extra column 21
            fpdb.write('{0:>2s}'.format(str(chain)))
            # Data type: Residue sequence number: Cols 23 - 26
            if resnum < 10000:
                fpdb.write('{0:>4d}'.format(int(resnum)))
            else:
                hybresnum = hybrid36encode(resnum,4)
                fpdb.write('{0:>4s}'.format(str(hybresnum)))
                #f.write('****')
            fpdb.write('    ') # <-- Four blank spaces
            # Data type: X coordinates: Cols 31 - 38 (8.3)
            fpdb.write('{0:>8.3f}'.format(float(basecrds[i,0])))
            # Data type: Y coordinates: Cols 39 - 46 (8.3)
            fpdb.write('{0:>8.3f}'.format(float(basecrds[i,1])))
            # Data type: Z coordinates: Cols 47 - 54 (8.3)
            fpdb.write('{0:>8.3f}'.format(float(basecrds[i,2])))
            # Data type: Occupancy: Cols 55 - 60 (6.2)
            fpdb.write('{0:>6.2f}'.format(float(1.0)))
            # Data type: Temperature factor: Cols 61 - 66 (6.2)
            fpdb.write('{0:>6.2f}'.format(float(0.0)))
            fpdb.write('          ') # <-- Ten blank spaces
            # Data type: Element symbol: Cols 77 - 78
            fpdb.write('{0:>2s}'.format(str(element)))
            # Data type: Charge: Cols 79 - 80 <-- Currently leaving this blank
            fpdb.write('  \n') # <-- Move to next line

            # Iterate atom number
            atomnum += 1
    else:
        pass

    # 2. Multi-model PDB with chains = 'A'
    #f = open(outputdir + filename + '-multimodel.pdb', 'a')

    fid.write('...Model ' + str(chainnum + 1) + ', Residue ' + str(resnum) + \
              ' printing coordinates...\n')

    element = ' '
    # Please see official PDB file format documentation for more information
    # www.wwpdb.org/documentation/file-format
    #
    for i in range(len(refatoms)):
        # Data type: Record Name: Cols 1 - 6
        fmm.write('{0:<6s}'.format('ATOM'))
        # Data type: Atom serial number: Cols 7 - 11
        if mmatomnum < 100000:
            fmm.write('{0:>5d}'.format(int(mmatomnum)))
        else:
            mmhybatomnum = hybrid36encode(mmatomnum,5)
            fmm.write('{0:>5s}'.format(str(mmhybatomnum)))
            #f.write('*****')
        fmm.write(' ') # <-- One blank space
        # Data type: Atom name: Cols 13 - 16
        # This one is complicated and depends on size of string
        if len(str(refatoms[i])) == 1:
            fmm.write(' ' + '{0:>1s}'.format(str(refatoms[i])) + '  ')
            element = str(refatoms[i])
        elif len(str(refatoms[i])) == 2:
            fmm.write(' ' + '{0:>2s}'.format(str(refatoms[i])) + ' ')
            element = str(refatoms[i])[0]
        elif len(str(refatoms[i])) == 3:
            fmm.write(' ' + '{0:>3s}'.format(str(refatoms[i])))
            element = str(refatoms[i])[0]
        elif len(str(refatoms[i])) == 4:
            fmm.write('{0:>4s}'.format(str(refatoms[i])))
            element = str(refatoms[i])[1]
        # Data type: Alternate location indicator: Col 17 
        # <-- This is typically empty
        fmm.write(' ')
        # Data type: Residue name: Cols 18 - 20
        fmm.write('{0:>3s}'.format(str(restype)))
        # Data type: Chain identifier: Col 22 <-- Insert extra column 21
        # For multi-model PDB, this is always 'A'
        fmm.write('{0:>2s}'.format(str('A')))
        # Data type: Residue sequence number: Cols 23 - 26
        if resnum < 10000:
            fmm.write('{0:>4d}'.format(int(resnum)))
        else:
            hybresnum = hybrid36encode(resnum,4)
            fmm.write('{0:>4s}'.format(str(hybresnum)))
            #f.write('****')
        fmm.write('    ') # <-- Four blank spaces
        # Data type: X coordinates: Cols 31 - 38 (8.3)
        fmm.write('{0:>8.3f}'.format(float(basecrds[i,0])))
        # Data type: Y coordinates: Cols 39 - 46 (8.3)
        fmm.write('{0:>8.3f}'.format(float(basecrds[i,1])))
        # Data type: Z coordinates: Cols 47 - 54 (8.3)
        fmm.write('{0:>8.3f}'.format(float(basecrds[i,2])))
        # Data type: Occupancy: Cols 55 - 60 (6.2)
        fmm.write('{0:>6.2f}'.format(float(1.0)))
        # Data type: Temperature factor: Cols 61 - 66 (6.2)
        fmm.write('{0:>6.2f}'.format(float(0.0)))
        fmm.write('          ') # <-- Ten blank spaces
        # Data type: Element symbol: Cols 77 - 78
        fmm.write('{0:>2s}'.format(str(element)))
        # Data type: Charge: Cols 79 - 80 <-- Currently leaving this blank
        fmm.write('  \n') # <-- Move to next line

        # Iterate atom number
        mmatomnum += 1

    #fmm.close()

    # 3. Single-model PDB with chains = 'A' and iterative segid
    #f = open(outputdir + filename + '-chseg.pdb', 'a')

    fid.write('...Segment ' + str(chainnum + 1) + ', Residue ' + \
              str(resnum) + ' printing coordinates...\n')

    element = ' '
    # Please see official PDB file format documentation for more information
    # www.wwpdb.org/documentation/file-format
    #
    for i in range(len(refatoms)):
        # Data type: Record Name: Cols 1 - 6
        fseg.write('{0:<6s}'.format('ATOM'))
        # Data type: Atom serial number: Cols 7 - 11
        if segatomnum < 100000:
            fseg.write('{0:>5d}'.format(int(segatomnum)))
        else:
            hybatomnum = hybrid36encode(segatomnum,5)
            fseg.write('{0:>5s}'.format(str(hybatomnum)))
            #f.write('*****')
        fseg.write(' ') # <-- One blank space
        # Data type: Atom name: Cols 13 - 16
        # This one is complicated and depends on size of string
        if len(str(refatoms[i])) == 1:
            fseg.write(' ' + '{0:>1s}'.format(str(refatoms[i])) + '  ')
            element = str(refatoms[i])
        elif len(str(refatoms[i])) == 2:
            fseg.write(' ' + '{0:>2s}'.format(str(refatoms[i])) + ' ')
            element = str(refatoms[i])[0]
        elif len(str(refatoms[i])) == 3:
            fseg.write(' ' + '{0:>3s}'.format(str(refatoms[i])))
            element = str(refatoms[i])[0]
        elif len(str(refatoms[i])) == 4:
            fseg.write('{0:>4s}'.format(str(refatoms[i])))
            element = str(refatoms[i])[1]
        # Data type: Alternate location indicator: Col 17 
        # <-- This is typically empty
        fseg.write(' ')
        # Data type: Residue name: Cols 18 - 20
        fseg.write('{0:>3s}'.format(str(restype)))
        # Data type: Chain identifier: Col 22 <-- Insert extra column 21
        # Use chain 'A' here
        fseg.write('{0:>2s}'.format(str('A')))
        # Data type: Residue sequence number: Cols 23 - 26
        if resnum < 10000:
            fseg.write('{0:>4d}'.format(int(resnum)))
        else:
            hybresnum = hybrid36encode(atomnum,4)
            fseg.write('{0:>4s}'.format(str(hybresnum)))
            #f.write('****')
        fseg.write('    ') # <-- Four blank spaces
        # Data type: X coordinates: Cols 31 - 38 (8.3)
        fseg.write('{0:>8.3f}'.format(float(basecrds[i,0])))
        # Data type: Y coordinates: Cols 39 - 46 (8.3)
        fseg.write('{0:>8.3f}'.format(float(basecrds[i,1])))
        # Data type: Z coordinates: Cols 47 - 54 (8.3)
        fseg.write('{0:>8.3f}'.format(float(basecrds[i,2])))
        # Data type: Occupancy: Cols 55 - 60 (6.2)
        fseg.write('{0:>6.2f}'.format(float(1.0)))
        # Data type: Temperature factor: Cols 61 - 66 (6.2)
        fseg.write('{0:>6.2f}'.format(float(0.0)))
        fseg.write('      ') # <-- Six blank spaces
        # Write SEGID here <-- This is a NAMD hack that allows for a "large"
        # number of segments or chains (I've allowed for up to 9999 which is
        # unreasonably large)
        fseg.write('{0:>4d}'.format(chainnum+1))
        # Data type: Element symbol: Cols 77 - 78
        fseg.write('{0:>2s}'.format(str(element)))
        # Data type: Charge: Cols 79 - 80 <-- Currently leaving this blank
        fseg.write('  \n') # <-- Move to next line

        # Iterate atom number
        segatomnum += 1

    #f.close()

    return atomnum, mmatomnum, segatomnum
  
# IV. Matrix transformation functions 

# 1. Function to generate transformation matrix 
#    between two data sets
def getTransMat(mob, tar):

    mob_com = mob.mean(0)
    tar_com = tar.mean(0)
    mob = mob - mob_com
    tar = tar - tar_com
    matrix = np.dot(mob.T, tar)

    U, s, Vh = linalg.svd(matrix)
    Id = np.array([[1, 0, 0],
                   [0, 1, 0],
                   [0, 0, np.sign(linalg.det(matrix))]])
    rotation = np.dot(Vh.T, np.dot(Id, U.T))

    transmat = np.eye(4)
    transmat[:3,:3] = rotation
    transmat[:3, 3] = tar_com - mob_com

    return transmat

# 2. Function to transform coordinates
def applyTransMat(transmat, coords):

    return np.dot(coords, transmat[:3,:3].T) + transmat[:3, 3]

# 3. Function to translate coordinates
def translate(mob,trans):

    npts = mob.shape[0]
    
    for i in range(npts):

        mob[i,:] = mob[i,:] + trans

    return mob

# 4. Function to convert Euler rotation to Axis-Angle
def eultoaxisangle(mat):

    [[m00, m10, m20],\
     [m01, m11, m21],\
     [m02, m12, m22]] = mat

    angle = math.degrees(math.acos((m00 + m11 + m22 - 1)/2))

    xtemp = (m21 - m12) / math.sqrt(pow(m21 - m12,2) + pow(m02 - m20,2) + \
                                    pow(m10 - m01,2))
    ytemp = (m02 - m20) / math.sqrt(pow(m21 - m12,2) + pow(m02 - m20,2) + \
                                    pow(m10 - m01,2))
    ztemp = (m10 - m01) / math.sqrt(pow(m21 - m12,2) + pow(m02 - m20,2) + \
                                    pow(m10 - m01,2))

    axis = np.array([xtemp, ytemp, ztemp])

    return angle, axis

# 5. Function to convert Axis-Angle to Euler rotation
def axisangletoeul(angle, axis):

    c = math.cos(math.radians(angle))
    s = math.sin(math.radians(angle))
    t = 1.0 - c
    x, y, z = axis

    mat = [[t*x*x + c, t*x*y - z*s, t*x*z + y*s],\
           [t*x*y + z*s, t*y*y + c, t*y*z - x*s],\
           [t*x*z - y*s, t*y*z + x*s, t*z*z + c]]

    return mat

# V. Functions for encoding large numbers

# 1. Function to encode a decimal using base36 notation
def base36encode(number):

    # 36-character alphabet for base-36 notation
    alphab36 = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', \
                'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', \
                'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
    base36 = ''

    while number:
        number, i  = divmod(number, 36)
        base36 = alphab36[i] + base36

    return base36

# 2. Function to encode a decimal using hybrid36 notation
def hybrid36encode(number,digits):

    # 52-character alphabet for first digit of hybrid36 notation
    alphahyb36 = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', \
                  'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', \
                  'Y', 'Z', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', \
                  'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', \
                  'w', 'x', 'y', 'z']

    div, rem = divmod(number, 36 ** (digits - 1))
    b36rem = base36encode(rem)
    hybrem = alphahyb36[div]
    # Need to check length of b36rem string
    hyb36str = str(hybrem) + str(b36rem)

    return hyb36str

# VI. Main PDBGen Function Definition

def pdbgen(filename,abtype,natype,inputdir,outputdir,log):
    
    """
    This function creates PDB files for a data structure input as a .cndo
    filetype.
    
    Parameters
    ----------
      filename --> name of structure (omit .cndo)
      abtype --> type of DNA helical structure ('A' or 'B')
      natype --> 'DNA' or 'RNA'
      inputdir --> directory with input .cndo file
      outputdir --> directory for .pdb and .log output files
    
    Returns
    -------
      none
      
    """
    
    # Create reference DNA/RNA data structure:
    if abtype == 'B' and natype == 'DNA':
        bdna = BDNA()
    else:
        # Only BDNA available in this version pdbgen
        # Return if not selected
        sys.stdout.write('\nNucleic acid type not currently available. Aborting...\n\n')
        return
    
    # Use the given file-like logging object
    fid = log

    # Initialization block
    fid.write('\n\n')
    fid.write('    ##########################################\n')
    fid.write('    ##                                      ##\n')
    fid.write('    ##              PDBGen v1.5             ##\n')
    fid.write('    ##                                      ##\n')
    fid.write('    ##              written by              ##\n')
    fid.write('    ##          William P. Bricker          ##\n')
    fid.write('    ##                  at                  ##\n')
    fid.write('    ##         Mass. Inst. of Tech.         ##\n')
    fid.write('    ##                                      ##\n')
    fid.write('    ##             last updated             ##\n')
    fid.write('    ##             May 9th, 2019            ##\n')
    fid.write('    ##                                      ##\n')
    fid.write('    ##########################################\n')
    fid.write('\n\n')

    sys.stdout.write('\nPDB GENERATOR V1.5\n')
    sys.stdout.write('Begin PDB Generation...\n\n')
    sys.stdout.write('Check ' + filename + '-pdbgen.log for more detailed output...\n\n')

    # Step 1. Extract data from DNA topology file

    cndofilename = filename

    # Parse .cndo file to get dnaInfo
    dnaTop, dNode, triad, id_nt = cndo_to_dnainfo(cndofilename, str(inputdir))
    
    # Create array for dNode, triad
    dNode = np.asarray(dNode)
    triad = np.asarray(triad)

    # 1.1. dnaInfo.dnaTop contains the sequential topology
    # {dnaTop, id, up, down, across, seq}

    # 1.2. dnaInfo.dnaGeom.dNode contains the centroid of each node (bp)
    # {dNode, e0(1), e0(2), e0(3)}

    # 1.3. dnaInfo.dnaGeom.triad contains coordinate system of each node (bp)
    # {triad, e1(1), e1(2), e1(3), e2(1), e2(2), e2(3), e3(1), e3(2), e3(3)}

    # 1.4. dnaInfo.dnaGeom.id_nt contains the basepairing info
    # {id_nt, id1, id2}

    # The object dnaInfo.dnaTop is ordered by chain, starting with the scaffold
    # strand. From this we can sequentially build our PDB file, after a routing
    # procedure.

    fid.write('INPUT PARAMETERS:\n')
    fid.write('  filename = ' + filename + '\n')
    fid.write('  abtype = ' + abtype + '\n')
    fid.write('  natype = ' + natype + '\n')
    fid.write('  inputdir = ' + inputdir + '\n')
    fid.write('  outputdir = ' + outputdir + '\n\n')

    # If pdb files currently exist, delete them
    if os.path.exists(outputdir + filename + '.pdb'):
        os.remove(outputdir + filename + '.pdb')

    if os.path.exists(outputdir + filename + '-multimodel.pdb'):
        os.remove(outputdir + filename + '-multimodel.pdb')

    if os.path.exists(outputdir + filename + '-chseg.pdb'):
        os.remove(outputdir + filename + '-chseg.pdb')
        
    # Check dNode for physical XYZ size of system
    minx, miny, minz = np.amin(dNode[:,1].astype(float)),\
                       np.amin(dNode[:,2].astype(float)),\
                       np.amin(dNode[:,3].astype(float))
    maxx, maxy, maxz = np.amax(dNode[:,1].astype(float)),\
                       np.amax(dNode[:,2].astype(float)),\
                       np.amax(dNode[:,3].astype(float))
    minxyz = np.amin([minx,miny,minz])
    maxxyz = np.amax([maxx,maxy,maxz])
    sys.stdout.write('Minimum XYZ value is ' + str(minxyz) + 
                     ' and maximum XYZ value is ' + str(maxxyz) + '...\n\n')
    
    # PDB filetype is strict and only allows 4 digits positive or negative
    # Note: unless we shift the center of coordinates {0.0, 0.0, 0.0}, the
    # maximum effective size of the nanoparticle is 
    # {1999.998, 1999.998, 1999.998} Angstroms
    if minxyz <= float(-1000.0):
        sys.stdout.write('Minimum XYZ value is too large for ' + 
                         'PDB generation. Aborting...\n\n')
        return
    elif maxxyz >= float(10000.0):
        sys.stdout.write('Maximum XYZ value is too large for ' + 
                         'PDB generation. Aborting...\n\n')
        return
    else:
        pass

    # Initialize PDB Generation Values
    atomnum = 1
    mmatomnum = 1
    segatomnum = 1
    resnum = 1
    chainnum = 0
    numchains = 0
    chlist = 'A'
    cc = 0

    # Chain list consists of 63 alphanumeric characters used sequentially to 
    # number PDB chains.
    chainlist = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', \
                 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', \
                 'Y', 'Z', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', \
                 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', \
                 'w', 'x', 'y', 'z', '0', '1', '2', '3', '4', '5', '6', '7', \
                 '8', '9']
    
    # First need to re-order the dnaInfo.dnaTop structure as it is not in the 
    # order needed to build a pdb file. Loop through data structure and save to 
    # routeTemp. The dnaInfo.dnaTop structure is ordered so that the scaffold 
    # strand is first. Next, the staple strands are not always contiguous, so 
    # they need to be reordered.

    fid.write('Starting DNA nanostructural routing procedure...\n')

    # Create array for unrouteTemp
    unrouteTemp = np.asarray(dnaTop)
    numbases = len(unrouteTemp[:,0])
    routeTemp = np.zeros((numbases,5),dtype=object)
    visited = np.zeros(numbases,dtype=int)
    routeindex = 0

    sys.stdout.write('There are ' + str(numbases) + 
                     ' total bases in the structure...\n')
    if numbases > 9999:
        sys.stdout.write('WARNING: Chain IDs greater than 9999 bases' +  
                         ' will be output in hybrid base36 notation\n')

    # Estimate number of atoms
    if natype == 'DNA':
        estatoms = int(np.ceil(31.75*numbases))

    sys.stdout.write('There are an estimated ' + str(estatoms) + 
                     ' total atoms in the structure...\n')
    if estatoms > 99999:
        sys.stdout.write('WARNING: Atom IDs greater than 99999 atoms will' +
                         ' be output in hybrid base36 notation\n')

    # Loop through all of the bases
    sys.stdout.write('\n1. DNA nanostructural routing... [                    ]   0%')
    for ii in range(numbases):
        
        # Print progress bar
        nn = int(np.ceil((float(ii+1) / float(numbases)) * 20.0))
        pp = int(np.ceil((float(ii+1) / float(numbases)) * 100.0))
        sys.stdout.write('\r1. DNA nanostructural routing... [' + 
                         '{:<20}'.format('='*nn) + ']' + '{:>4}'.format(pp) + 
                         '%')
        sys.stdout.flush()

        # Base-pairing info for base
        base = unrouteTemp[ii,1:]
        baseid = int(unrouteTemp[ii,1])
        baseup = int(unrouteTemp[ii,2])
        basedown = int(unrouteTemp[ii,3])
        baseacross = int(unrouteTemp[ii,4])
        baseseq = str(unrouteTemp[ii,5])

        # Check if base is a terminal 5' end and not visited yet
        if baseup == -1 and visited[ii] == 0:
            # Append base to route
            routeTemp[routeindex,:] = base
            routeindex += 1
            visited[ii] = 1
            # Set initial length of strand
            strlen = 1
            while basedown != -1:
                nextbaseid = basedown
                # Check if next base is correct one
                # Fails if ii == numbases - 1
                if ii + strlen < numbases - 1:
                    tempnextbaseid = int(unrouteTemp[ii+strlen,1])
                    if nextbaseid == tempnextbaseid:
                        # Base-pairing info for base
                        base = unrouteTemp[ii+strlen,1:]
                        baseid = int(unrouteTemp[ii+strlen,1])
                        baseup = int(unrouteTemp[ii+strlen,2])
                        basedown = int(unrouteTemp[ii+strlen,3])
                        baseacross = int(unrouteTemp[ii+strlen,4])
                        baseseq = str(unrouteTemp[ii+strlen,5])
                    else:
                        # First try unrouteTemp[basedown-1]
                        tempnextbaseid = int(unrouteTemp[basedown-1,1])
                        if nextbaseid == tempnextbaseid:
                            base = unrouteTemp[basedown-1,1:]
                            baseid = int(unrouteTemp[basedown-1,1])
                            baseup = int(unrouteTemp[basedown-1,2])
                            basedown = int(unrouteTemp[basedown-1,3])
                            baseacross = int(unrouteTemp[basedown-1,4])
                            baseseq = str(unrouteTemp[basedown-1,5])
                        else:
                            # If all else fails!
                            # Loop through to find next base in sequence
                            for jj in range(numbases):
                                # Base-pairing info for base
                                base = unrouteTemp[jj,1:]
                                baseid = int(unrouteTemp[jj,1])
                                baseup = int(unrouteTemp[jj,2])
                                basedown = int(unrouteTemp[jj,3])
                                baseacross = int(unrouteTemp[jj,4])
                                baseseq = str(unrouteTemp[jj,5])
                                if baseid == nextbaseid:
                                    break
                                else:
                                    continue
                else:
                    # Loop through to find next base in sequence
                    for jj in range(numbases):
                        # Base-pairing info for base
                        base = unrouteTemp[jj,1:]
                        baseid = int(unrouteTemp[jj,1])
                        baseup = int(unrouteTemp[jj,2])
                        basedown = int(unrouteTemp[jj,3])
                        baseacross = int(unrouteTemp[jj,4])
                        baseseq = str(unrouteTemp[jj,5])
                        if baseid == nextbaseid:
                            break
                        else:
                            continue
                routeTemp[routeindex,:] = base
                routeindex += 1
                strlen += 1
            else:
                # Base is a terminal 3' end
                # Continue the loop
                if basedown == -1:
                    numchains += 1
                    continue
                else:
                    fid.write('...Error in routing info...\n')
                    break      

    sys.stdout.write('\n\nThere are ' + str(numchains) + 
                     ' total chains in the structure...\n')
    if numchains > 63:
        sys.stdout.write('WARNING: Skipping standard PDB file generation' +
                         ' due to large (>63) number of chains.\n')
    
    # Open PDB files for appending
    if numchains <= 63:
        fpdb = open(outputdir + filename + '.pdb', 'a')
    else:
        fpdb = ''
        
    fmm = open(outputdir + filename + '-multimodel.pdb', 'a')
    fseg = open(outputdir + filename + '-segid.pdb', 'a')

    # Tags for ssDNA
    ssfirst = 0 # ID of first nucleotide in ss region
    sslast = 0 # ID of last nucleotide in ss region
    sslength = 0 # Length of ss region
    ssbases = []

    # Go through each base in routed structure
    fid.write('\nExtract coordinates for each base in routed structure...\n')

    sys.stdout.write('\n2. PDB generation... [                    ]   0%')
    for ii in range(numbases):

        # Print progress bar
        nn = int(np.ceil((float(ii+1) / float(numbases)) * 20.0))
        pp = int(np.ceil((float(ii+1) / float(numbases)) * 100.0))
        sys.stdout.write('\r2. PDB generation... [' + 
                         '{:<20}'.format('='*nn) + ']' + '{:>4}'.format(pp) + 
                         '%')
        sys.stdout.flush()

        # Get base-pairing info
        base = routeTemp[ii,:]
        baseid = int(routeTemp[ii,0])
        baseup = int(routeTemp[ii,1])
        basedown = int(routeTemp[ii,2])
        baseacross = int(routeTemp[ii,3])
        baseseq = str(routeTemp[ii,4])
        #print ii, baseid, baseup, basedown, baseacross, baseseq

        # Tag for type of base strand
        type = 0 # scaf = 1, stap = 2, ssdna = 3
        
        # Check if the base is 5'-end
        if baseup == -1:
            # Multi-model PDB starts new model here
            f = open(outputdir + filename + '-multimodel.pdb', 'a')
            f.write('MODEL' + '{0:>9s}'.format(str(chainnum + 1)) + '\n')
            f.close()    

        #print sslength, sslast, baseid

        # Check if in an ssDNA region
        if sslength > 0:
            if sslength == 1:
                ssfirst = 0
                sslast = 0
                sslength = 0
                ssbases = []
                continue
            elif baseid != sslast:
                continue
            elif baseid == sslast:
                ssfirst = 0
                sslast = 0
                sslength = 0
                ssbases = []
                continue
        else:
            pass

        # First Check if base is unpaired
        if baseacross == -1:
            type = 3
            fid.write('...Unpaired base...\n')
            pass
        else:
            # Otherwise, Extract basepairid
            for j, bp in enumerate(id_nt):
                # Scaffold strand
                if baseid == int(bp[1]):
                    bpid = int(j)
                    type = 1
                    fid.write('...Scaffold strand...\n')
                    break
                # Staple strand
                elif baseid == int(bp[2]):
                    bpid = int(j)
                    type = 2
                    fid.write('...Staple strand...\n')
                    break

        #print base, type

        # Only basepaired sequences have coordinates
        if type == 1 or type == 2:
            # Extract Centroid of Base
            xx0, yy0, zz0 = float(dNode[bpid,1]), float(dNode[bpid,2]), \
                            float(dNode[bpid,3])
            #print xx0, yy0, zz0

            # Extract Coordinate System of Base
            xx1, xx2, xx3 = float(triad[bpid,1]), float(triad[bpid,2]), \
                            float(triad[bpid,3]) # X-axis
            yy1, yy2, yy3 = float(triad[bpid,4]), float(triad[bpid,5]), \
                            float(triad[bpid,6]) # Y-axis
            zz1, zz2, zz3 = float(triad[bpid,7]), float(triad[bpid,8]), \
                            float(triad[bpid,9]) # Z-axis

            #print xx1, xx2, xx3
            #print yy1, yy2, yy3
            #print zz1, zz2, zz3

            # Get transformation matrix for origin to base coordinate system

            xyzorigin = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])    

            xyzbase = np.array([[xx0, yy0, zz0],
                                [xx0 + xx1, yy0 + xx2, zz0 + xx3],
                                [xx0 + yy1, yy0 + yy2, zz0 + yy3],
                                [xx0 + zz1, yy0 + zz2, zz0 + zz3]])

            #print xyzorigin, xyzbase

            transformMat = getTransMat(xyzorigin, xyzbase)

        # For unpaired sequences, need to calculate the reference frame
        elif type == 3:

            # Whole ss region will be calculated within this statement
            ssfirst = baseid
            upbase = baseup
            sslast = baseid
            downbase = basedown
            ssbases.append(base)
            sslength = 1
            # Now find last unpaired nucleotide
            #print baseup, basedown
            itemp = ii
            while baseacross == -1:
                itemp += 1
                # Get base-pairing info
                base = routeTemp[itemp,:]
                baseid = int(routeTemp[itemp,0])
                baseup = int(routeTemp[itemp,1])
                basedown = int(routeTemp[itemp,2])
                baseacross = int(routeTemp[itemp,3])
                baseseq = str(routeTemp[itemp,4])
                if baseacross == -1:
                    sslast = baseid
                    ssbases.append(base)
                    downbase = basedown
                    sslength += 1
                    continue
                else:
                    break
            #print baseup, basedown

            # Print ssDNA characteristics
            fid.write('  ssDNA region (first: ' + str(ssfirst) + ', last: ' + 
                      str(sslast) + ', length: ' + str(sslength) + ')\n')     

            # Extract coordinates of upstream base
            for j, bp in enumerate(id_nt):
                # Scaffold strand
                if upbase == int(bp[1]):
                    bpidup = int(j)
                    fid.write('...Upstream base ID is ' + str(bpidup) + '...\n')
                    typeup = 1
                    fid.write('...Upstream base is scaffold strand...\n')
                    break
                # Staple strand
                elif upbase == int(bp[2]):
                    bpidup = int(j)
                    fid.write('...Upstream base ID is ' + str(bpidup) + '...\n')
                    typeup = 2
                    fid.write('...Upstream base is staple strand...\n')
                    break

            # Extract Centroid of Upstream Base
            xx0up, yy0up, zz0up = float(dNode[bpidup,1]), float(dNode[bpidup,2]), \
                                  float(dNode[bpidup,3])

            #print xx0up, yy0up, zz0up

            # Extract Coordinate System of Upstream Base
            xx1up, xx2up, xx3up = float(triad[bpidup,1]), float(triad[bpidup,2]), \
                                  float(triad[bpidup,3]) # X-axis
            yy1up, yy2up, yy3up = float(triad[bpidup,4]), float(triad[bpidup,5]), \
                                  float(triad[bpidup,6]) # Y-axis
            zz1up, zz2up, zz3up = float(triad[bpidup,7]), float(triad[bpidup,8]), \
                                  float(triad[bpidup,9]) # Z-axis

            xyzbase0 = np.array([[xx0up, yy0up, zz0up],
                                 [xx0up + xx1up, yy0up + xx2up, zz0up + xx3up],
                                 [xx0up + yy1up, yy0up + yy2up, zz0up + yy3up],
                                 [xx0up + zz1up, yy0up + zz2up, zz0up + zz3up]])

            # Extract coordinates of downstream base
            for j, bp in enumerate(id_nt):
                # Scaffold strand
                if downbase == int(bp[1]):
                    bpiddo = int(j)
                    fid.write('...Downstream base ID is ' + str(bpiddo) + '...\n')
                    typedo = 1
                    fid.write('...Downstream base is scaffold strand...\n')
                    break
                # Staple strand
                elif downbase == int(bp[2]):
                    bpiddo = int(j)
                    fid.write('...Downstream base ID is ' + str(bpiddo) + '...\n')
                    typedo = 2
                    fid.write('...Downstream base is staple strand...\n')
                    break

            # Extract Centroid of Downstream Base
            xx0do, yy0do, zz0do = float(dNode[bpiddo,1]), float(dNode[bpiddo,2]), \
                                  float(dNode[bpiddo,3])

            # Extract Coordinate System of Downstream Base
            xx1do, xx2do, xx3do = float(triad[bpiddo,1]), float(triad[bpiddo,2]), \
                                  float(triad[bpiddo,3]) # X-axis
            yy1do, yy2do, yy3do = float(triad[bpiddo,4]), float(triad[bpiddo,5]), \
                                  float(triad[bpiddo,6]) # Y-axis
            zz1do, zz2do, zz3do = float(triad[bpiddo,7]), float(triad[bpiddo,8]), \
                                  float(triad[bpiddo,9]) # Z-axis

            xyzbase3 = np.array([[xx0do, yy0do, zz0do],
                                 [xx0do + xx1do, yy0do + xx2do, zz0do + xx3do],
                                 [xx0do + yy1do, yy0do + yy2do, zz0do + yy3do],
                                 [xx0do + zz1do, yy0do + zz2do, zz0do + zz3do]])

            # Compute distance between upstream and downstream bases
            dist12 = sqrt(pow(float(xx0do)-float(xx0up), 2) + \
                          pow(float(yy0do)-float(yy0up), 2) + \
                          pow(float(zz0do)-float(zz0up), 2))

            # Debugging - ssDNA region distance
            #print 'ssDNA Region Dist = ', str(dist12)

            # Check that up- and downstream bases are same type
            if typeup == typedo:
                pass
            elif typeup != typedo:
                fid.write('...Error: up- and down-stream bases in ssDNA region' +
                          '    are differing types...\n')
                break

            # Need two additional points for ss bulge region
            # Check: make this work for additional types of ss regions
            #
            # Diagram shows a typical 'staple' ss bulge region
            #
            #       d1 ------ d2
            #       |         |
            #       |         ^
            #       |         |
            #   <--(d0)       (d3)-->
            #       |
            #       v
            #
            # Point 0 is upstream base centroid
            d0 = np.array([xx0up, yy0up, zz0up])
            # Point 3 is downstream base centroid
            d3 = np.array([xx0do, yy0do, zz0do])

            # Distance to extend d0 - d1 and d3 - d2 axes
            # To test later - Used a 5 Ang distance for points d1 and d2. 
            # Is this dependent on ssDNA length?
            dext = 5 # Angstroms
            #dext = sslength # Angstroms (Try 1 Angstrom per ssDNA base)

            # Point 1 is along Upstream Z-axis
            # Scaffold
            if typeup == 1:
                d1 = np.array([dext*zz1up, dext*zz2up, dext*zz3up])
            # Staple
            elif typeup == 2:
                d1 = np.array([-dext*zz1up, -dext*zz2up, -dext*zz3up])
            else:
                fid.write('...Error: Upstream base does not have a base type...\n')
                break
            # Point 2 is along Downstream Z-axis
            # Scaffold
            if typeup == 1:
                d2 = np.array([(xx0do - dext*zz1do) - xx0up, 
                               (yy0do - dext*zz2do) - yy0up, 
                               (zz0do - dext*zz3do) - zz0up])
            # Staple
            elif typeup == 2:
                d2 = np.array([(xx0do + dext*zz1do) - xx0up, 
                               (yy0do + dext*zz2do) - yy0up, 
                               (zz0do + dext*zz3do) - zz0up])
            else:
                fid.write('...Error: Upstream base does not have a base type...\n')
                break

            # Move upstream and downstream bases to {0,0,0}
            xyzbase30 = np.array([[0, 0, 0],
                                  [xx1do, xx2do, xx3do],
                                  [yy1do, yy2do, yy3do],
                                  [zz1do, zz2do, zz3do]])
            
            xyzbase00 = np.array([[0, 0, 0],
                                  [xx1up, xx2up, xx3up],
                                  [yy1up, yy2up, yy3up],
                                  [zz1up, zz2up, zz3up]])

            # Total rotation matrix between base0 and base3 at origin
            Rtot = getTransMat(xyzbase30, xyzbase00)

            # Extract rotation matrix from transformation matrix
            Rrotate = Rtot[:3,:3]

            # Convert to axis-angle representation
            angle, axis = eultoaxisangle(Rrotate)

            # Loop through ssDNA bases
            for jj in range(sslength):        
            
                # Get ss base information
                base = ssbases[jj]
                baseid = int(base[0])
                baseup = int(base[1])
                basedown = int(base[2])
                baseacross = int(base[3])
                baseseq = str(base[4])

                # Now pull reference base information
                refcrds = []
                refatoms = []
                restype = ''
                if typeup == 1 and abtype == 'B' and natype == 'DNA': # Scaffold strand
                    if baseseq == 'A':
                        refcrds = bdna.Ascaf[:,3:6]
                        refatoms = bdna.Ascaf[:,0]
                        restype = 'ADE'
                    elif baseseq == 'C':
                        refcrds = bdna.Cscaf[:,3:6]
                        refatoms = bdna.Cscaf[:,0]
                        restype = 'CYT'
                    elif baseseq == 'G':
                        refcrds = bdna.Gscaf[:,3:6]
                        refatoms = bdna.Gscaf[:,0]
                        restype = 'GUA'
                    elif baseseq == 'T':
                        refcrds = bdna.Tscaf[:,3:6]
                        refatoms = bdna.Tscaf[:,0]
                        restype = 'THY'
                    else:
                        fid.write('...Error: No base sequence for scaffold strand...\n')
                elif typeup == 2 and abtype == 'B' and natype == 'DNA': # Staple strand
                    if baseseq == 'A':
                        refcrds = bdna.Astap[:,3:6]
                        refatoms = bdna.Astap[:,0]
                        restype = 'ADE'
                    elif baseseq == 'C':
                        refcrds = bdna.Cstap[:,3:6]
                        refatoms = bdna.Cstap[:,0]
                        restype = 'CYT'
                    elif baseseq == 'G':
                        refcrds = bdna.Gstap[:,3:6]
                        refatoms = bdna.Gstap[:,0]
                        restype = 'GUA'
                    elif baseseq == 'T':
                        refcrds = bdna.Tstap[:,3:6]
                        refatoms = bdna.Tstap[:,0]
                        restype = 'THY'
                    else:
                        fid.write('...Error: No base sequence for staple strand...\n')
                else:
                    fid.write('...Error: SS base sequence not labelled as scaffold or staple strand...\n')
                    continue

                # First move to upstream base position
                xyzorigin = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])

                # Transform upstream base to XYZ origin
                transformMat = getTransMat(xyzorigin, xyzbase00)

                upbasecrds = applyTransMat(transformMat, refcrds)
        
                # Reset temporary rotation matrix to total rotation matrix
                Rtemp = Rtot

                iangle = angle * (jj+1) / (sslength+1)

                # Test - Use cubic Bezier function to interpolate curve
                # d0 - upstream base, d3 - downstream base
                #
                # B(t) = (1 - t)^3 * d0 + 
                #        3(1 - t)^2 * t * d1 +
                #        3(1 - t) * t^2 * d2 +
                #        t^3 * d3

                # Fraction along Bezier curve
                t = (float(jj) + 1) / (float(sslength) + 1)
                
                # Use d0 (upstream base) as reference point for Bezier interpolation
                d0 = np.array([0.0, 0.0, 0.0])
                d3 = np.array([xx0do - xx0up, yy0do - yy0up, zz0do - zz0up])

                # Bezier contributions
                B3 = (1 - t)**3 * d0
                B2 = 3 * (1 - t)**2 * t * d1
                B1 = 3 * (1 - t) * t**2 * d2
                B0 = t**3 * d3

                # Total Bezier function for ssDNA region
                Bt = B3 + B2 + B1 + B0
     
                # Set interpolated vector to Bezier sum
                ivec = Bt

                # Switch back to Euler rotation matrix
                Rrotiter = np.array(axisangletoeul(iangle,axis))

                Rtemp[:3,:3] = Rrotiter
                Rtemp[:3,3] = ivec

                # Transform B-form base to Bezier position
                basecrds = applyTransMat(Rtemp, upbasecrds)

                # Move base back to upbase coordinates
                basecrds = translate(basecrds,np.array([xx0up, yy0up, zz0up]))

                # Write out PDB file sequentially
                # Pass {filename, chain, residue number, atom number, residue type,
                # atom types, base coords} to PDB writer
                atomnum, mmatomnum, segatomnum = writePDBresidue(filename, chlist, 
                                                 chainnum, resnum, atomnum, 
                                                 mmatomnum, segatomnum, restype, 
                                                 refatoms, basecrds, numchains, fid,
                                                 outputdir, fpdb, fmm, fseg)

                # Iterate residue indexing
                resnum += 1

        # Now pull reference base information
        refcrds = []
        refatoms = []
        restype = ''
        if type == 1 and abtype == 'B' and natype == 'DNA': # Scaffold strand
            if baseseq == 'A':
                refcrds = bdna.Ascaf[:,3:6]
                refatoms = bdna.Ascaf[:,0]
                restype = 'ADE'
            elif baseseq == 'C':
                refcrds = bdna.Cscaf[:,3:6]
                refatoms = bdna.Cscaf[:,0]
                restype = 'CYT'
            elif baseseq == 'G':
                refcrds = bdna.Gscaf[:,3:6]
                refatoms = bdna.Gscaf[:,0]
                restype = 'GUA'
            elif baseseq == 'T':
                refcrds = bdna.Tscaf[:,3:6]
                refatoms = bdna.Tscaf[:,0]
                restype = 'THY'
            else:
                fid.write('...Error: No base sequence for scaffold strand...\n')
        elif type == 2 and abtype == 'B' and natype == 'DNA': # Staple strand
            if baseseq == 'A':
                refcrds = bdna.Astap[:,3:6]
                refatoms = bdna.Astap[:,0]
                restype = 'ADE'
            elif baseseq == 'C':
                refcrds = bdna.Cstap[:,3:6]
                refatoms = bdna.Cstap[:,0]
                restype = 'CYT'
            elif baseseq == 'G':
                refcrds = bdna.Gstap[:,3:6]
                refatoms = bdna.Gstap[:,0]
                restype = 'GUA'
            elif baseseq == 'T':
                refcrds = bdna.Tstap[:,3:6]
                refatoms = bdna.Tstap[:,0]
                restype = 'THY'
            else:
                fid.write('...Error: No base sequence for staple strand...\n')
        elif type == 3: # Single-stranded region
            # Single-stranded regions already written out above
            continue
        else:
            fid.write('...Error: Base sequence not labelled as scaffold or staple strand...\n')
            continue

        # Now transform reference coordinates to base coordinate system
        basecrds = applyTransMat(transformMat, refcrds)

        # Write out PDB file sequentially
        # Pass {filename, chain, residue number, atom number, residue type, 
        # atom types, base coords} to PDB writer 
        atomnum, mmatomnum, segatomnum = writePDBresidue(filename, chlist, 
                                         chainnum, resnum, atomnum, mmatomnum, 
                                         segatomnum, restype, refatoms, 
                                         basecrds, numchains, fid, outputdir,
                                         fpdb, fmm, fseg)

        # Iterate residue indexing
        resnum += 1
        if basedown == -1:
            
            # Multi-model PDB ends model here
            fmm.write('ENDMDL\n')
            
            # Iterate chainnum and return mmatomnum to 1
            chainnum += 1
            mmatomnum = 1
            resnum = 1

            # Chainlist definition
            # Now deprecated due to not printing standard model if >63
            if chainnum < 62:
                chlist = chainlist[chainnum]
            elif chainnum == int(62 * (cc + 1)):
                chlist = chainlist[chainnum - int(62*(cc+1))]
                cc += 1
            else:
                chlist = chainlist[chainnum - int(62*cc)]
                
    # Finalization of script
    fid.write('\n  PDB Generation Successful!  \n\n')
    sys.stdout.write('\n\nPDB Generation Successful!\n')
    if numchains <= 63:
        sys.stdout.write('Standard PDB file is output as ' + filename + '.pdb\n')
        sys.stdout.write('    This file can be opened in any visualizer...\n')
    sys.stdout.write('Multimodel PDB file is output as ' + filename + '-multimodel.pdb\n')
    sys.stdout.write('    This file can be opened in UCSD Chimera...\n')
    sys.stdout.write('Chain segment PDB file is output as ' + filename + '-chseg.pdb\n')
    sys.stdout.write('    This file can be opened in VMD...\n')
    sys.stdout.write('Happy PDB viewing!\n\n')
    
    # Close any open files
    if numchains <= 63:
        fpdb.close()
    fmm.close()
    fseg.close()
    fid.close()
    
    return
