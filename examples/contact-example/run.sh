#!/bin/bash

# Path to the rosetta directory
rosetta_dir=/opt/rosetta-3.5

$CCP4/bin/ample \
-fasta input/toxd_.fasta \
-mtz input/1dtx.mtz \
-frags_3mers input/aat000_03_05.200_v1_3 \
-frags_9mers input/aat000_09_05.200_v1_3 \
-psipred_ss2 input/toxd_.psipred_ss2 \
-contact_file input/toxd_.mat \
-contact_format ccmpred \
-rosetta_dir $rosetta_dir \
-nmodels 5 \
-percent 50 \
-use_shelxe True \
-nproc 5 

# Add below for running with contact predictions
#-bbcontacts_file input/toxd_.filteredoutput.txt \
#-native_pdb input/1DTX.pdb \
#-native_cutoff 9 \
#-energy_function FADE_default \
