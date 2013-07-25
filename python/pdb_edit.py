'''
Created on 15 Apr 2013

@author: jmht
'''

import re
import types
import unittest

class PDBEdit(object):
    """Class for editing PDBs
    
    """
    
    def select_residues(self, inpath=None, outpath=None, residues=None ):
        """Create a new pdb by selecting only the numbered residues from the list.
        
        Args:
        infile: path to input pdb
        outfile: path to output pdb
        residues: list of integers of the residues to keep
        
        Return:
        path to new pdb or None
        """
    
        assert inpath, outpath
        assert type(residues) == list
    
        pdb_in = open(inpath, "r")
        pdb_out = open(outpath , "w")
        
        # Loop through PDB files and create new ones that only contain the residues specified in the list
        for pdbline in pdb_in:
            pdb_pattern = re.compile('^ATOM\s*(\d*)\s*(\w*)\s*(\w*)\s*(\w)\s*(\d*)\s')
            pdb_result = pdb_pattern.match(pdbline)
            if pdb_result:
                pdb_result2 = re.split(pdb_pattern, pdbline )
                for i in residues : #convert to ints to comparex
        
                    if int(pdb_result2[5]) == int(i):
        
                        pdb_out.write(pdbline)
        
        pdb_out.close()
        
        return
    
    def reliable_sidechains(self, inpath=None, outpath=None ):
        """Only output non-backbone atoms for residues in the res_names list.
        """
        
        # Remove sidechains that are in res_names where the atom name is not in atom_names
        res_names = [ 'MET', 'ASP', 'PRO', 'GLN', 'LYS', 'ARG', 'GLU', 'SER']
        atom_names = [ 'N', 'CA', 'C', 'O', 'CB' ]

        #   print 'Found ',each_file
        pdb_in = open( inpath, "r" )
        pdb_out = open( outpath, "w" )
        
        for pdbline in pdb_in:
            pdb_pattern = re.compile('^ATOM\s*(\d*)\s*(\w*)\s*(\w*)\s*(\w)\s*(\d*)\s')
            pdb_result = pdb_pattern.match(pdbline)
            
            # Check ATOM line and for residues in res_name, skip any that are not in atom names
            if pdb_result:
                pdb_result2 = re.split(pdb_pattern, pdbline)
                if pdb_result2[3] in res_names and not pdb_result2[2] in atom_names:
                    continue
            
            # Write out everything else
            pdb_out.write(pdbline)
        
        #End for
        pdb_out.close()
        pdb_in.close()
        
    def backbone(self, inpath=None, outpath=None ):
        """Only output backbone atoms.
        """        
        
        atom_names = [ 'N', 'CA', 'C', 'O', 'CB' ]

        #   print 'Found ',each_file
        pdb_in = open( inpath, "r" )
        pdb_out = open( outpath, "w" )    

        for pdbline in pdb_in:
            pdb_pattern = re.compile('^ATOM\s*(\d*)\s*(\w*)\s*(\w*)\s*(\w)\s*(\d*)\s')
            pdb_result = pdb_pattern.match(pdbline)
    
            if pdb_result:
                pdb_result2 = re.split(pdb_pattern, pdbline)
                if pdb_result2[3] != '':
                    if pdb_result2[2] not in atom_names:
                        continue
            
            # Write out everything else
            pdb_out.write(pdbline)
        
        #End for
        pdb_out.close()
        pdb_in.close



class PdbAtom(object):
    """
    COLUMNS        DATA  TYPE    FIELD        DEFINITION
-------------------------------------------------------------------------------------
 1 -  6        Record name   "ATOM  "
 7 - 11        Integer       serial       Atom  serial number.
13 - 16        Atom          name         Atom name.
17             Character     altLoc       Alternate location indicator.
18 - 20        Residue name  resName      Residue name.
22             Character     chainID      Chain identifier.
23 - 26        Integer       resSeq       Residue sequence number.
27             AChar         iCode        Code for insertion of residues.
31 - 38        Real(8.3)     x            Orthogonal coordinates for X in Angstroms.
39 - 46        Real(8.3)     y            Orthogonal coordinates for Y in Angstroms.
47 - 54        Real(8.3)     z            Orthogonal coordinates for Z in Angstroms.
55 - 60        Real(6.2)     occupancy    Occupancy.
61 - 66        Real(6.2)     tempFactor   Temperature  factor.
77 - 78        LString(2)    element      Element symbol, right-justified.
79 - 80        LString(2)    charge       Charge  on the atom.
"""
    def __init__(self, line):
        """Set up attributes"""
        
        self.fromLine( line )
        
    
    def _reset(self):
        
        self.serial = None
        self.name = None
        self.altLoc = None
        self.resName = None
        self.chainID = None
        self.resSeq = None
        self.iCode = None
        self.x = None
        self.y = None
        self.z = None
        self.occupancy = None
        self.tempFactor = None
        self.element = None
        self.charge = None
        
    def fromLine(self,line):
        """Initialise from the line from a PDB"""
        
        assert len(line) >= 54,"Line length was: {0}\n{1}".format(len(line),line)
        
        self._reset()
        
        self.serial = int(line[6:11])
        self.name = line[12:16]
        # Use for all so None means an empty field
        if line[16].strip():
            self.altLoc = line[16]
        self.resName = line[17:20]
        if line[21].strip():
            self.chainID = line[21]
        if line[22:26].strip():
            self.resSeq = int(line[22:26])
        if line[26].strip():
            self.iCode = line[26]
        self.x = float(line[30:38])
        self.y = float(line[38:46])
        self.z = float(line[46:54])
        if len(line) >= 60 and line[54:60].strip():
            self.occupancy = float(line[54:60])
        if len(line) >= 66 and line[60:66].strip():
            self.tempFactor = float(line[60:66])
        if len(line) >= 78 and line[76:78].strip():
            self.element = line[76:78]
        if len(line) >= 80 and line[78:80].strip():
            self.charge = line[78:80]
    
    def toLine(self):
        """Create a line suitable for printing to a PDB file"""
        
        s = "ATOM  " # 1-6
        s += "{0:5d}".format( self.serial ) # 7-11
        s += " " # 12 blank
        s += "{0:>4}".format( self.name ) # 13-16
        if not self.altLoc: #17
            s += " "
        else:
            s += "{0:1}".format( self.altLoc )
        s += "{0:3}".format( self.resName ) # 18-20
        s += " " # 21 blank
        if not self.chainID: #22
            s += " "
        else:
            s += "{0:1}".format( self.chainID )
        s += "{0:4}".format( self.resSeq ) #23-26
        if not self.iCode: #27
            s += " "
        else:
            s += "{0:1}".format( self.iCode )
        s += "   " # 28-30 blank
        s += "{0: 8.3F}".format( self.x ) #31-38
        s += "{0: 8.3F}".format( self.y ) #39-46
        s += "{0: 8.3F}".format( self.z ) #47-54
        if not self.occupancy: # 55-60
            s += "      "
        else:
            s += "{0: 6.2F}".format( self.occupancy )
        if not self.tempFactor: # 61-66
            s += "      "
        else:
            s += "{0: 6.2F}".format( self.tempFactor )
        s += "          " # 67-76 blank
        if not self.element: #77-78
            s += "  "
        else:
            s += "{0:>2}".format( self.element )
        if not self.charge: #79-80
            s += "  "
        else:
            s += "{0:2d}".format( self.charge )
            
        return s
        
    def __str__(self):
        """List the data attributes of this object"""
        me = {}
        for slot in dir(self):
            attr = getattr(self, slot)
            if not slot.startswith("__") and not ( isinstance(attr, types.MethodType) or
              isinstance(attr, types.FunctionType) ):
                me[slot] = attr
            
        return "{0} : {1}".format(self.__repr__(),str(me))


class Test(unittest.TestCase):

    def testReadAtom(self):
        """See if we can read an atom line"""

        line = "ATOM     41  NH1AARG A  -3      12.218  84.840  88.007  0.50 40.76           N  "
        a = PdbAtom()
        a.fromLine(line)
        self.assertEqual(a.serial,41)
        self.assertEqual(a.name,' NH1')
        self.assertEqual(a.altLoc,'A')
        self.assertEqual(a.resName,'ARG')
        self.assertEqual(a.chainID,'A')
        self.assertEqual(a.resSeq,-3)
        self.assertEqual(a.iCode,None)
        self.assertEqual(a.x,12.218)
        self.assertEqual(a.y,84.840)
        self.assertEqual(a.z,88.007)
        self.assertEqual(a.occupancy,0.5)
        self.assertEqual(a.tempFactor,40.76)
        self.assertEqual(a.element,' N')
    
    def testWriteAtom(self):
        """Round-trip an atom line"""
        
        line = "ATOM     41  NH1AARG A  -3      12.218  84.840  88.007  0.50 40.76           N  "
        a = PdbAtom()
        a.fromLine(line)   
        self.assertEqual( a.toLine(), line )
           
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
