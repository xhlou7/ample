REM Windows run script

# NMR ensembling example - 2LC9 is an ensemble model of a minor and transiently formed state of 
# a T4 lysozyme mutant. The target 102l is X-ray data

REM Need to add path to shelxe
set PATH=C:\Users\jmht42\Shelx\shelx64;%PATH%

%CCP4%\bin\ample.bat ^
-mtz input\102l.mtz ^
-fasta input\102L.fasta ^
-name 102l ^
-nmr_model_in input\2LC9.pdb ^
-quick_mode True ^
-show_gui True

