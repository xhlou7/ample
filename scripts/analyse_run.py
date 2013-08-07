#!/usr/bin/env python
'''
Created on 19 Jul 2013

@author: jmht

Data we will be collecting:

Target:
length in AA
resolution in A
secondary structure (% and per AA)
?radius of gyration

Rosetta Models:
Score
maxsub cf target

Cluster:

Ensemble:
number of models (and their scores)
truncation level
number residues
side_chain_treatment

Solution
number (and identity? of residues)

shelxe rebuild:
* CC
* av. fragment length
* RMSD to native
* Maxsub to native
* TM to native

remac refined result
* reforigin score to native
* rmsd to native
* maxsub to native
* TM to native

TO THINK ABOUT
* multiple models/chains in native
* multiple chains in solution (e.g. 3PCV)

'''

import os
import re
import shutil
import sys
import unittest

sys.path.append("/Users/jmht/Documents/AMPLE/ample-dev1/python")
import ample_util
import mrbump_results
import pdbEd


class ReforiginRmsd(object):
    """Class to use reforigin to determine how well the model was placed.
    
    For multiple models in the native pdb, this will cycle through each model and take the best rmsd.
    If the numbers of chains in the native/refined models are the same, the single rmsd is calculated.
    If there are differing numbers of chains between the native/refined models, a comparison is made 
    between each chain in the native and refined model, and the lowest rmsd is used
        
    """
    
    def __init__( self, nativePdb, refinedPdb ):
        
        
        self.rmsd = None
        self.bestChains = None
        
        self.run( nativePdb, refinedPdb )
    
    def run( self, nativePdb, refinedPdb ):
        """For now just save lowest rmsd - can look at collecting more info later
        
        Currently we assume we are only given one model and that it has already been standardised.
        """

        # Run a pass to find the # chains
        refinedInfo = pdbEd.get_info( refinedPdb )
        nativeInfo = pdbEd.get_info( nativePdb )
        native_chains = nativeInfo.models[ 0 ].chains
        refined_chains = refinedInfo.models[ 0 ].chains # only ever one model in the refined pdb
            
        rmsds = {} # dict of rmsd -> ( chainIDnative, chainIDrefined )
        
        # Match each chain in native against refined and pick the best
        for nativeChainID in native_chains:
            
            #print "native_chain: {0}".format( nativeChainID )
                    
            if len( native_chains ) == 1:
                # Don't need to do owt as we are just using the native as is
                nativeChainPdb = nativePdb
            else:
                
                # Extract the chain from the pdb
                n = os.path.splitext( os.path.basename( nativePdb ) )[0]
                nativeChainPdb = os.path.join( workdir, n+"_chain{0}.pdb".format( nativeChainID ) ) 
                pdbEd.extract_chain( nativePdb, nativeChainPdb, chainID=nativeChainID )
                
                assert os.path.isfile( nativeChainPdb  ), nativeChainPdb
            
            for refinedChainID in refined_chains:
                
                #print "refined_chain: {0}".format( refinedChainID )
                
                assert os.path.isfile( nativeChainPdb  ), nativeChainPdb
                
                # Extract the chain from the pdb
                n = os.path.splitext( os.path.basename( refinedPdb ) )[0]
                refinedChainPdb = os.path.join( workdir, n+"_chain{0}.pdb".format( refinedChainID ) ) 
                pdbEd.extract_chain( refinedPdb, refinedChainPdb, chainID=refinedChainID, newChainID=nativeChainID )
                
                #print "calculating for {0} vs. {1}.".format( refinedChainPdb, nativeChainPdb  )
                
                rmsd = self.calc_reforigin_rmsd( refinedChainPdb, nativeChainPdb, nativeChainID=nativeChainID )
                #print "got rmsd chain ",rmsd
                
                rmsds[ rmsd ] = ( nativeChainID, refinedChainID )
                
        # End loop over chains
        # Now pick the best...
        rmsd = sorted( rmsds.keys() )[ 0 ]
        print "Got rmsds over chains: {0}".format( rmsds )
        
        self.rmsd = rmsd
        self.bestChains = rmsds[ rmsd ]
        print "best chain rmsd is {0} for nativeChain {1} vs refinedChain {2}".format( self.rmsd, self.bestChains[0], self.bestChains[1] )
            
        return


    def calc_reforigin_rmsd( self, refinedPdb, nativePdb, nativeChainID=None ):
        """Use reforigin to calculate rmsd between native and refined"""
        
        workdir=os.getcwd()
        
        # Now create a PDB with the matching atoms from native that are in refined
        n = os.path.splitext( os.path.basename( nativePdb ) )[0]
        nativePdbMatch = os.path.join( workdir, n+"_matched.pdb" )
        pdbEd.keep_matching( refpdb=refinedPdb, targetpdb=nativePdb, outpdb=nativePdbMatch )
        
        # Now get the rmsd
        n = os.path.splitext( os.path.basename( refinedPdb ) )[0]
        reforiginOut = os.path.join( workdir, n+"_chain{0}_reforigin.pdb".format( nativeChainID ) )
        return pdbEd.reforigin_rmsd( refpdb=nativePdbMatch, targetpdb=refinedPdb, outpdb=reforiginOut )

class ShelxeLogParser(object):
    """
    Class to mine information from a shelxe log
    """
    
    def __init__(self,logfile):
        
        self.logfile = logfile
        self.CC = None
        self.avgChainLength = None
        
        self.parse()
        
        return
        
    def parse(self):
        """Parse a shelxe log file to get the CC and average Chain length
        """
        
        cycleData = [] # List (CC,avgChainLength) tuples - ordered by cycle
        fh = open( self.logfile, 'r')
        
        line = fh.readline()
        while line:
            
            # find should be quicker then re match
            if line.find("residues left after pruning, divided into chains as follows:") != -1:
                (cc, avgChainLength) = self._parseCycle(fh)
                cycleData.append( (cc, avgChainLength) )
            
            
            if  line.find( "Best trace (cycle" ) != -1:
                # Expecting:
                #  "Best trace (cycle   1 with CC 37.26%) was saved as shelxe-input.pdb"
                cycle = int( re.search("\s\d+\s", line).group(0) )
                cc = float( re.search("\s\d+\.\d+", line).group(0) )
                
                # Check it matches
                if cycleData[ cycle-1 ][0] != cc:
                    raise RuntimeError,"Error getting final CC!"
                
                self.CC =  cycleData[ cycle-1 ][0]
                self.avgChainLength = cycleData[ cycle-1 ][1]

            line = fh.readline()
        #End while
        
        fh.close()
        
        return
        
    def _parseCycle(self, fh):
        """
        Working on assumption each cycle contains something like the below:
<log>
           223 residues left after pruning, divided into chains as follows:
 A:   6   B:   7   C:   6   D:   6   E:   8   F:   7   G:  12   H:  12   I:   5
 J:  10   K:   6   L:   6   M:   6   N:   7   O:   6   P:   7   Q:   8   R:   6
 S:   5   T:   6   U:  10   V:   9   W:  12   X:  11   Y:   8   Z:   6   Z:   6
 Z:   6   Z:   7   Z:   6

 CC for partial structure against native data =  30.92 %
 </log>
 """
        
        lengths = []
        while True:
            
            line = fh.readline().strip()
            line = line.rstrip(os.linesep)
            if not line:
                # End of reading lengths
                break
            
            # Loop through integers & add to list
            for m in re.finditer("\s\d+", line):
                lengths.append( int(m.group(0)) )
                
        # Now calculate average chain length
        if not len( lengths ):
            raise RuntimeError, "Failed to read any fragment lengths"
        
        # Average chain lengths
        avgChainLength = sum(lengths) / int( len(lengths) )        
        
        # Here should have read the  lengths so now just get the CC
        count=0
        while True:
            line = fh.readline().strip()
            if line.startswith("CC for partial structure against native data"):
                break
            else:
                count += 1
                if count > 5:
                    raise RuntimeError,"Error parsing CC score"
            
        cc = float( re.search("\d+\.\d+", line).group(0) )
        
        return ( cc, avgChainLength )

class CompareModels(object):
    """Class to compare two models - currently with maxcluster"""
    
    def __init__(self, refModel, targetModel, workdir=None ):
        
        self.workdir = workdir
        
        self.refModel = refModel
        self.targetModel = targetModel
        
        self.grmsd = None
        self.masxub = None
        self.pairs = None
        self.rmsd = None
        self.tm = None
        
        
        # If the rebuilt models is in multiple chains, we need to create a single chain
        info = pdbEd.get_info( self.targetModel )
        if len( info.models[0].chains ) > 1:
            print "Coallescing targetModel into a single chain"
            n = os.path.splitext( os.path.basename( self.targetModel ) )[0]
            targetModel1chain = os.path.join( workdir, n+"_1chain.pdb" )
            pdbEd.to_single_chain( self.targetModel, targetModel1chain )
            self.targetModel = targetModel1chain
            
        # If the reference model is in multiple chains, we need to create a single chain
        info = pdbEd.get_info( self.refModel )
        if len( info.models[0].chains ) > 1:
            print "Coallescing refModel into a single chain"
            n = os.path.splitext( os.path.basename( self.refModel ) )[0]
            refModel1chain = os.path.join( workdir, n+"_1chain.pdb" )
            pdbEd.to_single_chain( self.refModel, refModel1chain )
            self.refModel = refModel1chain
        
        self.run()
    
        return
    
    
    def run(self):
        
        
        n = os.path.splitext( os.path.basename( self.targetModel ) )[0]
        logfile = os.path.join( self.workdir, n+"_maxcluster.log" )
        cmd="/opt/maxcluster/maxcluster -in -e {0} -p {1}".format( self.targetModel, self.refModel ).split()
        retcode = ample_util.run_command(cmd=cmd, logfile=logfile, directory=os.getcwd(), dolog=False)
        
        if retcode != 0:
            raise RuntimeError,"Error running maxcluster!"
        
        self.parse_maxcluster_log( logfile )
        
        alignrsm = os.path.join( self.workdir, "align.rsm")
        
        n = os.path.splitext( os.path.basename( self.targetModel ) )[0]
        rootname = os.path.join( self.workdir, n )
        self.split_alignrsm( alignrsm=alignrsm, rootname=rootname )
        
        return
    
    
    def parse_maxcluster_log( self, logfile ):
        """Extract info - assumes it completers in 1 iteration"""
        
        
        def _get_float( istr ):
            # Needed as we sometimes get spurious characters after the last digit
            nums = [ str(i) for i in range(10 ) ]
            if istr[-1] not in nums:
                istr = istr[:-1]
            return float(istr)
        
        for line in open( logfile , 'r' ):
            if line.startswith("Iter"):
                # colon after int
                iternum = int( line.split()[1][:-1] )
                if iternum > 1:
                    raise RuntimeError,"More than one iteration - no idea what that means..."
                
                if line.find( " Pairs=") != -1:
                    # e.g.: Iter 1: Pairs= 144, RMSD= 0.259, MAXSUB=0.997. Len= 144. gRMSD= 0.262, TM=0.997
                    # Need to remove spaces after = sign as the output is flakey - do it twice for safety
                    tmp = line.replace("= ","=")
                    tmp = tmp.replace("= ","=")
                    for f in tmp.split():
#                         if f.startswith("Pairs"):
#                             self.pairs = int( f.split("=")[1] )
                        if f.startswith("RMSD"):
                            self.rmsd = _get_float( f.split("=")[1] )
                        if f.startswith("MAXSUB"):
                            self.maxsub = _get_float( f.split("=")[1] )
                        if f.startswith("gRMSD"):
                            self.grmsd = _get_float( f.split("=")[1] )
                        if f.startswith("TM"):
                            self.tm = _get_float( f.split("=")[1] )
                            
                    # Bail out as we should be done
                    break
            
        return
    
    
    def split_alignrsm(self, alignrsm=None, rootname=None):
         
        # Order is experiment then prediction
 
        
        efile = rootname+"_experiment.pdb"
        pfile = rootname+"_prediction.pdb"
                 
        f = open( alignrsm, 'r' )
        line = f.readline()
         
        reading = False
        gotExp = False
        lines = []
        for line in open( alignrsm, 'r' ):
            
            # End of one of the files
            if line.startswith("TER"):
                lines.append( line )
                if not gotExp:
                    gotExp=True
                    f = open( efile, 'w' )
                else:
                    f = open( pfile, 'w' )
                    
                f.writelines( lines )
                f.close()
                lines = []
                reading=False
            
            if line.startswith("REMARK"):
                if not reading:
                    reading = True
                    
            if reading:
                lines.append( line )
        
        return
    
# End CompareModels

def process_result( mrbumpResult=None, nativePdb=None, workdir=None ):
    
    os.chdir( workdir )
    
    # First check if the native has > 1 model and extract the first if so
    info = pdbEd.get_info( nativePdb )
    if len( info.models ) > 1:
        print "nativePdb has > 1 model - using first"
        n = os.path.splitext( os.path.basename( nativePdb ) )[0]
        nativePdb1 = os.path.join( workdir, n+"_model1.pdb" )
        pdbEd.extract_model( nativePdb, nativePdb1, modelID=info.models[0].serial )
        nativePdb = nativePdb1
        
    # Standardise the PDB to rename any non-standard AA, remove solvent etc
    n = os.path.splitext( os.path.basename( nativePdb ) )[0]
    nativePdbStd = os.path.join( workdir, n+"_std.pdb" )
    pdbEd.standardise( nativePdb, nativePdbStd )
    nativePdb = nativePdbStd
    
    # Get the reforigin RMSD of the phaser placed model as refined with refmac
    refinedPdb = os.path.join( mrbumpResult.resultDir, "refine", "refmac_{0}_loc0_ALL_{1}_UNMOD.pdb".format( mrbumpResult.program, mrbumpResult.ensembleName ) )
    
    # debug - copy into work directory
    shutil.copy(refinedPdb, os.path.join( workdir, os.path.basename( refinedPdb ) ) )
    
    rmsder = ReforiginRmsd( nativePdb, refinedPdb )
    print "REFORIGIN RMSD: {0}\n\n".format( rmsder.rmsd )
    
    # Now read the shelxe log to see how we did
    logfile = os.path.join( mrbumpResult.resultDir, "build/shelxe/shelxe_run.log" )
    shelxeP = ShelxeLogParser( logfile )
    print "got CC ",shelxeP.CC
    print "got chain length ",shelxeP.avgChainLength
    
    # Finally use maxcluster to compare the shelxe model with the native
    shelxeModel = os.path.join( mrbumpResult.resultDir, "build/shelxe", "shelxe_{0}_loc0_ALL_{1}_UNMOD.pdb".format( mrbumpResult.program, mrbumpResult.ensembleName ) )
    
    m = CompareModels( nativePdb, shelxeModel, workdir=workdir  )
    print "Maxsub - maxsub={0} rmsd={1} grmsd={2} tm={3}".format( m.maxsub,  m.rmsd, m.grmsd, m.tm  )
    
    return


result = mrbump_results.MrBumpResult()

if False:
    workdir = "/home/jmht/Documents/test/3PCV"
    result.resultDir = "/media/data/shared/TM/3PCV/ROSETTA_MR_0/MRBUMP/cluster_1/search_poly_ala_trunc_2.822761_rad_1_phaser_mrbump/data/loc0_ALL_poly_ala_trunc_2.822761_rad_1/unmod/mr/phaser"
    nativePdb = "/media/data/shared/TM/3PCV/3PCV.pdb"
    result.program = "phaser"
    result.ensembleName = "poly_ala_trunc_2.822761_rad_1"

if False:
    workdir = "/home/jmht/Documents/test/1GU8"
    result.resultDir = "/media/data/shared/TM/1GU8/ROSETTA_MR_0/MRBUMP/cluster_1/search_SCWRL_reliable_sidechains_trunc_19.511671_rad_3_phaser_mrbump/data/loc0_ALL_SCWRL_reliable_sidechains_trunc_19.511671_rad_3/unmod/mr/phaser"
    nativePdb = "/media/data/shared/TM/1GU8/1GU8.pdb"
    result.program = "phaser"
    result.ensembleName = "SCWRL_reliable_sidechains_trunc_19.511671_rad_3"

if True:
    workdir = "/home/jmht/Documents/test/3U2F"
    result.resultDir = "/media/data/shared/TM/3U2F/ROSETTA_MR_0/MRBUMP/cluster_1/search_poly_ala_trunc_0.21093_rad_2_molrep_mrbump/data/loc0_ALL_poly_ala_trunc_0.21093_rad_2/unmod/mr/molrep"
    nativePdb = "/media/data/shared/TM/3U2F/3U2F.pdb"
    result.program = "molrep"
    result.ensembleName = "poly_ala_trunc_0.21093_rad_2"


print "Checking ",nativePdb
process_result( mrbumpResult = result, nativePdb=nativePdb, workdir=workdir)


class Test(unittest.TestCase):


    def testShelxeLogParser(self):
        logfile = "/media/data/shared/TM/2BHW/ROSETTA_MR_0/MRBUMP/cluster_1/search_poly_ala_trunc_9.355791_rad_3_molrep_mrbump/" + \
        "data/loc0_ALL_poly_ala_trunc_9.355791_rad_3/unmod/mr/molrep/build/shelxe/shelxe_run.log"
        
        p = ShelxeLogParser( logfile )
        self.assertEqual(37.26, p.CC)
        self.assertEqual(7, p.avgChainLength)
        

#if __name__ == "__main__":
#    #import sys;sys.argv = ['', 'Test.testName']
#    unittest.main()