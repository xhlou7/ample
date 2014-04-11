#!/usr/bin/env python

#script to truncate the non secondary structure ends of a pdb

import re
import os, glob
import sys
import shutil

# our imports
import ample_util


#######  EDIT
def fix(pdb):

    cur = open(os.getcwd()+'/cur', 'w')
    cur.write('pdbset xyzin '+os.getcwd()+'/tmp' +' xyzout '+pdb+' <<EOF'+
               'OCCUPANCY 1 \n'+
               'EXCLUDE WATER \n'+
               'CHAIN A')
    cur.close()
#######
def check(pdb):
    i=1
    for line in open(pdb):
        if re.search('^ATOM', line):
            if   line[13:16] =='CA ':
                i+=1
    return i
#######
def try_NMR(pdb):
    list = [0]
    i = 2
    ISNMR = False
    out = open(os.getcwd()+'/test.pdb', 'w')
    out.write('MODEL    1\n')
    for line in  open(pdb):


        if re.search('^ATOM', line):
            out.write(line)


            if int(line[7:11]) < list[-1]:
                ISNMR = True
                out.write('ENDMDL\nMODEL    '+str(i)+'\n')
                i+=1
            list.append( int(line[7:11]) )
    out.close()
    print ISNMR
    return ISNMR, os.getcwd()+'/test.pdb'


#######
def split(model, path ):


    SPLIT = False
    for line in open(model):
        if  re.search('^MODEL', line):
            SPLIT = True
            modno = splitNMR(model, path)
            return modno

    if SPLIT == False:
        n = os.path.split(model)
        # check if run on nmr
        ISNMR, temp  = try_NMR(model)
        if ISNMR == False:
            print 'Only remodelingin one model'
            shutil.copyfile(model, path+'/'+n[-1])
            return 1
        if ISNMR == True:
            model = temp
            modno = splitNMR(model, path)
            return modno
def splitNMR(model, path):

    name = '.pdb'
    modelin= open(model)
    modno = 0
    condition= 0
    for line in modelin:
        # print line
        model_pattern = re.compile('^MODEL')
        model_result = model_pattern.match(line)
        if model_result:
            condition = 1
        #  print 'IN'
        pdb_pattern = re.compile('ENDMDL')
        pdb_result = pdb_pattern.match(line)
        if pdb_result:
            condition = 0
            modno = modno+1

        if condition == 1 and not model_result :
            # print 'IN'
            new_model = open(path+'/'+str(modno)+'_'+name, "a")
            #print line[21:22]
            if line[21:22] == 'A':
                #print line[21:22]
                new_model.write(line)
                new_model.flush()
            new_model.close()

    lengths = []
    for model in os.listdir(path):
        fix(path+'/'+model)
        l =  check(path+'/'+model)
        lengths.append(l)


    if len(lengths) >1:
        mina  = min(lengths, key = int)
        maxa  = max(lengths, key = int)
        if mina != maxa:
            print 'min length = ', mina, ' max length = ', maxa
            print 'All of the models need to be the same length, edit them and try again'
            sys.exit()
    return modno

def split_pdb(pdbin, directory=None):
    """Split a pdb file into its separate models"""

    if directory is None:
        directory = os.path.dirname(pdbin)
    
    # Largely stolen from pdb_split_models.py in phenix
    #http://cci.lbl.gov/cctbx_sources/iotbx/command_line/pdb_split_models.py
    import iotbx.file_reader
    
    pdbf = iotbx.file_reader.any_file(pdbin, force_type="pdb")
    pdbf.check_file_type("pdb")
    hierarchy = pdbf.file_object.construct_hierarchy()
    
    # Nothing to do
    n_models = hierarchy.models_size()
    if n_models == 1:
        print "split_pdb {0} only contained 1 model!".format( pdbin )
        return 1
    
    crystal_symmetry=pdbf.file_object.crystal_symmetry()
    
    for k, model in enumerate(hierarchy.models()) :
        k += 1
        new_hierarchy = iotbx.pdb.hierarchy.root()
        new_hierarchy.append_model(model.detached_copy())
        if (model.id == "") :
            model_id = str(k)
        else:
            model_id = model.id.strip()
            
        output_file = ample_util.filename_append(pdbin, model_id, directory)
        with open(output_file, "w") as f:
            if (crystal_symmetry is not None) :
                print >> f, iotbx.pdb.format_cryst1_and_scale_records(
                                                                      crystal_symmetry=crystal_symmetry,
                                                                      write_scale_records=True)
            print >> f, "REMARK Model %d of %d" % (k, n_models)
            if (pdbin is not None) :
                print >> f, "REMARK Original file:"
                print >> f, "REMARK   %s" % pdbin
            f.write(new_hierarchy.as_pdb_string())
    
    return n_models


if __name__ == "__main__":
    m = "/media/data/shared/coiled-coils/ensemble/ensemble.run1/1BYZ/ROSETTA_MR_0/ensembles_1/All_atom_trunc_0.005734_rad_1.pdb"
    
    print split_pdb(m,directory=os.getcwd())
    
    #model = '/data2/jac45/ex/2JQN.pdb'
    #path = '/data2/jac45/ex/m'
    #split(model, path )
