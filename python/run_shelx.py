#!/usr/bin/python2.6

#

import signal, time
import subprocess
import os
import sys, re
#from signal import alarm, signal, SIGALRM, SIGKILL
from subprocess import PIPE, Popen

import get_TFZ_resolution
import run_refmac
#import local_map_correlation
########
def try_theseus(cmd):#  theseus can fail so try Run a command with a timeout after which it will be forcibly killed.

 has_worked = False
 while has_worked == False:

   p = subprocess.Popen(cmd, shell = True)
   time.sleep(1)
   print p.poll()
   if p.poll() is None: #still running      
      p.kill()
      print 'timed out'
   else:
     print p.communicate()
     has_worked = True

#######
def mtz2hkl(mtz):
    mtz2hkl = os.environ.get("mtz2hkl")

    cur_dir = os.getcwd()
    mtz2hkl_run = open(cur_dir + '/mtz2hkl', "w")
    mtz2hkl_run.write('#!/bin/sh\n')
    mtz2hkl_run.write(mtz2hkl+' -2 orig')
    mtz2hkl_run.close()
    os.system('chmod uoga=wrx '+ cur_dir + '/mtz2hkl')
    os.system(cur_dir + '/mtz2hkl')

    if not os.path.exists(cur_dir + '/orig.hkl'):
      print 'NO HKL'
      sys.exit()
#########
def run_pro(ASU):
    shelxpro = os.environ.get("shelxpro")
    cur_dir = os.getcwd()
    mtz2hkl_run = open(cur_dir + '/pro', "w")
    mtz2hkl_run.write('#!/bin/sh\n')
    mtz2hkl_run.write(shelxpro+' orig <<eof'+
    '\nI\n'+
    '\norig.ins\norig.pdb\n\n\n'+ASU+'\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\nQ\n\n\nQ\n\n\n'+
    'eof\n')
    mtz2hkl_run.close()
    os.system('chmod uoga=wrx '+ cur_dir + '/pro')
   
    os.system(cur_dir + '/pro')

    if not os.path.exists(cur_dir + '/orig.ins'):
      print 'NO INS'
      sys.exit()

########
def shelxl():
    shelxl = os.environ.get("shelxl")
    cur_dir = os.getcwd()
    mtz2hkl_run = open(cur_dir + '/shelxl', "w")
    mtz2hkl_run.write('#!/bin/sh\n')
    mtz2hkl_run.write(shelxl+'  orig')
    mtz2hkl_run.close()
    os.system('chmod uoga=wrx '+ cur_dir + '/shelxl')
    os.system(cur_dir + '/shelxl')

    if not os.path.exists(cur_dir + '/orig.res'):
      print 'NO RES'
      sys.exit()
#####################
def shelxe(solvent, resolution):
    shelxe = os.environ.get("shelxe")

    free_lunch = ' '
    if float(resolution)<2.0:
      free_lunch = ' -e1.0'
    solvent = re.split('\.', solvent)

    solvent = solvent[0]
    cur_dir = os.getcwd()
    mtz2hkl_run = open(cur_dir + '/shelxe', "w")
    mtz2hkl_run.write('#!/bin/sh\n')
    mtz2hkl_run.write(shelxe +' orig -a10 -q -s0.'+str(solvent)+' -h -z -b '+ free_lunch)
    mtz2hkl_run.close()
    os.system('chmod uoga=wrx '+ cur_dir + '/shelxe')
    os.system(cur_dir + '/shelxe >RESULT')

    if not os.path.exists(cur_dir + '/orig.phs'):
      print 'NO PHS'


    Best_result = 0
    result = open(cur_dir + '/RESULT')
    fail_pattern = ('\*\* Unable to trace map - giving up \*\*')
    pattern = re.compile('CC for partial structure against native data =\s*(\d*\.\d*)\s*%')
    for line in result: 
       if re.search(pattern, line):
        split= re.split(pattern, line)
        print split
        if float(split[1]) > Best_result:
          Best_result = float(split[1])
       if re.search(fail_pattern, line):
        Best_result = line.rstrip('\n')


    HKLOUT, XYZOUT, SCORE = run_refmac.refmac('orig.pdb', 'orig.mtz')
    os.system('mv  orig.phs shel.phs') 
    #os.system('rm orig.*')
    return str(Best_result), SCORE, HKLOUT, XYZOUT
    


###################
def mathews(CELL, SPACE, MOLWT, ASU):

   
   path = os.getcwd()
   mat = open(path+'/mat', "w")
   mat.write ('#!/bin/sh\n'+
   'matthews_coef <<eof\n'+
   'MOLW ' + MOLWT + '\n'+
   'CELL ' + CELL +'\n'+
   'SYMMETRY ' + SPACE+'\n'+
   'AUTO \n'+
   'END\n'+
   'eof')
   mat.close()
   os.system('chmod uoga=wrx mat')
   os.system('./mat >mat.log')
   

   pattern = re.compile('^\s*(\d)\s*(\d*.\d*)\s*(\d*.\d*)\s*(\d*.\d*)')
   mat_out = open(path + '/mat.log')
   for line in mat_out:
     #print line
     result = re.search(pattern, line)
     if result:
      print line
      split = re.split(pattern, line)
      print split

      if split[1] == ASU:
         SOLVENT = split[3]


   return SOLVENT
###################################
def seqwt(fasta):
   path = os.getcwd()
  # print 'here'
   wt = open(path+'/wt', "w")
   wt.write ('#!/bin/sh\n'+
   'seqwt SEQUENCE ' + fasta+'\n')
   wt.close()

   os.system('chmod uoga=wrx wt')
   os.system('./wt >wt.log')
   wt_out = open(path +'/wt.log')
   pattern = re.compile(' Total     Molecular Weight\s*(\d*)\s*\(Da\)')

   for line in wt_out:
      result = re.match(pattern, line)
      if result:      
         # print line 
          split = re.split(pattern, line)
         # print split[1]
          MOLWT = split[1]
   return  MOLWT 
#######################
def get_cell_dimentions(mtz):
   SPACE = ''
   CELL=''
   path = os.getcwd()
  # print 'here'
   cell = open(path+'/cell', "w")
   cell.write ('#!/bin/sh\n'+
   'mtzdmp ' + mtz+'\n')
   cell.close()

   os.system('chmod uoga=wrx cell')
   os.system('./cell >cell.log')
 
   got_cell = False
   cell_result = open(path + '/cell.log')
   cell_pattern = re.compile(' * Cell Dimensions')
   space_pattern = re.compile('Space group =\s*(\'.*\')')

   all_lines = cell_result.readlines()
   counter = 0
   for line in all_lines:
     result = re.search(cell_pattern, line)
     if result:
       got_cell = True
      # print line
     if  got_cell == True:
       counter +=1
     if  got_cell == True and counter == 3:
       # print line
        CELL = line
        break

   for line in all_lines:
           result = re.search(space_pattern, line)
           if result:
            # print line
             split = re.split(space_pattern, line)
            # print split[1]
             SPACE = split[1]

   if SPACE =='P-1':
      SPACE = 'P 1'

   if CELL == '' or SPACE =='':
    sys.exit()
   return CELL, SPACE
#####################


#####################
def RUN(mtz, pdb, ASU, fasta, run_dir):

  os.chdir(run_dir)
  os.system('cp '+mtz +' orig.mtz')
  os.system('cp '+pdb +' orig.pdb')
  mtz2hkl(mtz)
  run_pro(ASU)
  shelxl()
  resolution,FreeR  = get_TFZ_resolution.get_resolution(pdb)
  CELL, SPACE = get_cell_dimentions(mtz)
  MOLWT = seqwt(fasta)
  solvent = mathews(CELL, SPACE, MOLWT, ASU)
  shelscore, refmacfreeR, HKLOUT, XYZOUT = shelxe(solvent, resolution)

  return shelscore, refmacfreeR, HKLOUT, XYZOUT, SPACE
#####




