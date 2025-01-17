"""
Created on 24 Oct 2014

@author: jmht
"""

import copy
import glob
import logging
import os
import pandas as pd
import shutil
import sys

from ample.util import ample_util, csymmatch, mtz_util, pdb_edit, pdb_model, reforigin, residue_map, rio, shelxe, \
    tm_util
from pyjob import Script

logger = logging.getLogger(__name__)

_oldroot = None
_newroot = None
SHELXE_STEM = 'shelxe'

_CSV_KEYLIST = [
    'ample_version',
    # Native info
    'native_pdb_code',
    'native_pdb_title',
    'native_pdb_resolution',
    'native_pdb_solvent_content',
    'native_pdb_space_group',
    'native_pdb_num_atoms',
    'native_pdb_num_residues',
    'native_pdb_num_chains',
    # The modelled sequence
    'fasta_length',
    # Get the ensemble data and add to the MRBUMP data
    'ensemble_name',
    'ensemble_percent_model',
    # cluster info
    'cluster_method',
    'num_clusters',
    'cluster_num',
    'cluster_centroid',
    'cluster_num_models',
    # truncation info
    'truncation_level',
    'percent_truncation',
    'truncation_method',
    'truncation_pruning',
    'truncation_variance',
    'num_residues',
    'pruned_residues',
    # subclustering info
    'subcluster_num_models',
    'subcluster_radius_threshold',
    'subcluster_centroid_model',
    'subcluster_centroid_model_RMSD',
    'subcluster_centroid_model_TM',
    # ensemble info
    # 'name',
    'side_chain_treatment',
    'ensemble_num_atoms',
    # MR result info
    # 'name',
    'MR_program',
    'Solution_Type',
    'PHASER_LLG',
    'PHASER_TFZ',
    'PHASER_RFZ',
    'PHASER_time',
    'PHASER_killed',
    'PHASER_version',
    'PHASER_errors',
    'MOLREP_score',
    'MOLREP_time',
    'MOLREP_version',
    'MR_MPE',
    'MR_wMPE',
    'REFMAC_Rfact',
    'REFMAC_Rfree',
    #     'REFMAC_MPE',
    #     'REFMAC_wMPE',
    'REFMAC_version',
    'BUCC_final_Rfact',
    'BUCC_final_Rfree',
    'BUCC_version',
    'ARP_final_Rfact',
    'ARP_final_Rfree',
    'ARP_version',
    'SHELXE_CC',
    'SHELXE_ACL',
    'SHELXE_MCL',
    'SHELXE_NC',
    'SHELXE_wPE',
    'SHELXE_wMPE',
    'SHELXE_os',
    'SHELXE_time',
    'SHELXE_version',
    'SXRBUCC_version',
    'SXRBUCC_final_Rfact',
    'SXRBUCC_final_Rfree',
    'SXRBUCC_MPE',
    'SXRBUCC_wMPE',
    'SXRARP_version',
    'SXRARP_final_Rfact',
    'SXRARP_final_Rfree',
    'SXRARP_MPE',
    'SXRARP_wMPE',
    'num_placed_chains',
    'num_placed_atoms',
    'reforigin_RMSD',
    'AA_num_contacts',
    'RIO_num_contacts',
    'RIO_in_register',
    'RIO_oo_register',
    'RIO_backwards',
    'RIO',
    'RIO_no_cat',
    'RIO_norm',
]


def analyse(amoptd, newroot=None):
    if newroot:
        assert os.path.isdir(newroot)
        global _oldroot, _newroot
        _newroot = newroot
        _oldroot = amoptd['work_dir']

    if not os.path.isdir(fixpath(amoptd['benchmark_dir'])):
        os.mkdir(fixpath(amoptd['benchmark_dir']))
    os.chdir(fixpath(amoptd['benchmark_dir']))

    # AnalysePdb may have already been called from the main script
    if amoptd['native_pdb'] and 'native_pdb_std' not in amoptd:
        analysePdb(amoptd)

    if amoptd['native_pdb_std']:
        # Generate an SHELXE HKL and ENT file so that we can calculate phase errors
        mtz_util.to_hkl(amoptd['mtz'], hkl_file=os.path.join(amoptd['benchmark_dir'], SHELXE_STEM + ".hkl"))
        shutil.copyfile(amoptd['native_pdb_std'], os.path.join(amoptd['benchmark_dir'], SHELXE_STEM + ".ent"))

    if amoptd['native_pdb'] and not (amoptd['homologs'] or amoptd['ideal_helices'] or amoptd['helical_ensembles']
                                     or amoptd['import_ensembles'] or amoptd['single_model_mode']):
        analyseModels(amoptd)

    # Get the ensembling data
    if 'ensembles_data' not in amoptd or not len(amoptd['ensembles_data']):
        logger.critical("Benchmark cannot find any ensemble data!")
        return

    # Get dict of ensemble name -> ensemble result
    ensemble_results = {e['name']: e for e in amoptd['ensembles_data']}

    # Get mrbump_results for cluster
    if 'mrbump_results' not in amoptd or not len(amoptd['mrbump_results']):
        logger.critical("Benchmark cannot find any mrbump results!")
        return

    data = []
    mrinfo = shelxe.MRinfo(amoptd['shelxe_exe'], amoptd['native_pdb_info'].pdb, amoptd['mtz'])
    for result in amoptd['mrbump_results']:

        # use mrbump dict as basis for result object
        d = copy.copy(result)

        # Add in the data from the ensemble
        d.update(ensemble_results[d['ensemble_name']])
        assert d['ensemble_name'] == d['name'], d

        # Hack for old results
        if 'truncation_num_residues' in d:
            d['num_residues'] = d['truncation_num_residues']
            del d['truncation_num_residues']

        # Hack for ideal helices where num_residues are missing
        if amoptd['ideal_helices'] and ('num_residues' not in d or d['num_residues'] is None):
            d['num_residues'] = int(d['ensemble_name'].lstrip('polyala_'))

        # Get the ensemble data and add to the MRBUMP data
        d['ensemble_percent_model'] = int((float(d['num_residues']) / float(amoptd['fasta_length'])) * 100)

        if amoptd['native_pdb']:
            # Add in stuff we've cleaned from the pdb
            native_keys = [
                'native_pdb_code',
                'native_pdb_title',
                'native_pdb_resolution',
                'native_pdb_solvent_content',
                'native_pdb_space_group',
                'native_pdb_num_chains',
                'native_pdb_num_atoms',
                'native_pdb_num_residues',
            ]
            d.update({key: amoptd[key] for key in native_keys})
            # Analyse the solution
            analyseSolution(amoptd, d, mrinfo)
        data.append(d)

    # Put everything in a pandas DataFrame
    dframe = pd.DataFrame(data)

    # General stuff
    dframe['ample_version'] = amoptd['ample_version']
    dframe['fasta_length'] = amoptd['fasta_length']

    # Analyse subcluster centroid models
    if 'subcluster_centroid_model' in dframe.columns and amoptd['native_pdb']:
        centroid_index = dframe.index
        centroid_models = [fixpath(f) for f in dframe.subcluster_centroid_model]
        native_pdb_std = fixpath(amoptd['native_pdb_std'])
        fasta = fixpath(amoptd['fasta'])

        # Calculation of TMscores for subcluster centroid models
        if amoptd['have_tmscore']:
            tm = tm_util.TMscore(amoptd['tmscore_exe'], wdir=fixpath(amoptd['benchmark_dir']), **amoptd)
            tm_results = tm.compare_structures(centroid_models, [native_pdb_std], [fasta])
            centroid_tmscores = [r['tmscore'] for r in tm_results]
            centroid_rmsds = [r['rmsd'] for r in tm_results]
        else:
            raise RuntimeError("No program to calculate tmscores!")

        dframe['subcluster_centroid_model_TM'] = pd.Series(centroid_tmscores, index=centroid_index)
        dframe['subcluster_centroid_model_RMSD'] = pd.Series(centroid_rmsds, index=centroid_index)

    # Save the data
    file_name = os.path.join(fixpath(amoptd['benchmark_dir']), 'results.csv')
    dframe.to_csv(file_name, columns=_CSV_KEYLIST, index=False, na_rep="N/A")
    amoptd['benchmark_results'] = dframe.to_dict('records')

    return


def analyseModels(amoptd):
    # Get hold of a full model so we can do the mapping of residues
    refModelPdb = glob.glob(os.path.join(amoptd['models_dir'], "*.pdb"))[0]

    nativePdbInfo = amoptd['native_pdb_info']
    refModelPdbInfo = pdb_edit.get_info(refModelPdb)
    amoptd['ref_model_pdb_info'] = refModelPdbInfo
    try:
        resSeqMap = residue_map.residueSequenceMap()
        resSeqMap.fromInfo(
            refInfo=refModelPdbInfo,
            refChainID=refModelPdbInfo.models[0].chains[0],  # Only 1 chain in model
            targetInfo=nativePdbInfo,
            targetChainID=nativePdbInfo.models[0].chains[0],
        )
        amoptd['res_seq_map'] = resSeqMap
    except Exception as e:
        logger.exception("Error calculating resSeqMap: %s" % e)
        amoptd['res_seq_map'] = None  # Won't be able to calculate RIO scores

    if amoptd['have_tmscore']:
        try:
            tm = tm_util.TMscore(amoptd['tmscore_exe'], wdir=fixpath(amoptd['benchmark_dir']))
            # Calculation of TMscores for all models
            logger.info("Analysing Rosetta models with TMscore")
            model_list = sorted(glob.glob(os.path.join(amoptd['models_dir'], "*pdb")))
            structure_list = [amoptd['native_pdb_std']]
            amoptd['tmComp'] = tm.compare_structures(model_list, structure_list, fastas=[amoptd['fasta']])
        except Exception as e:
            logger.exception("Unable to run TMscores: %s", e)
    else:
        raise RuntimeError("No program to calculate TMSCORES")


def analysePdb(amoptd):
    """Collect data on the native pdb structure"""

    nativePdb = fixpath(amoptd['native_pdb'])
    nativePdbInfo = pdb_edit.get_info(nativePdb)

    # number atoms/residues
    natoms, nresidues = pdb_edit.num_atoms_and_residues(nativePdb)

    # Get information on the origins for this spaceGroup
    try:
        originInfo = pdb_model.OriginInfo(spaceGroupLabel=nativePdbInfo.crystalInfo.spaceGroup)
    except Exception:
        originInfo = None

    # Do this here as a bug in pdbcur can knacker the CRYST1 data
    amoptd['native_pdb_code'] = nativePdbInfo.pdbCode
    amoptd['native_pdb_title'] = nativePdbInfo.title
    amoptd['native_pdb_resolution'] = nativePdbInfo.resolution
    amoptd['native_pdb_solvent_content'] = nativePdbInfo.solventContent
    amoptd['native_pdb_matthews_coefficient'] = nativePdbInfo.matthewsCoefficient
    if not originInfo:
        space_group = "P1"
    else:
        space_group = originInfo.spaceGroup()
    amoptd['native_pdb_space_group'] = space_group
    amoptd['native_pdb_num_atoms'] = natoms
    amoptd['native_pdb_num_residues'] = nresidues

    # First check if the native has > 1 model and extract the first if so
    if len(nativePdbInfo.models) > 1:
        logger.info("nativePdb has > 1 model - using first")
        nativePdb1 = ample_util.filename_append(
            filename=nativePdb, astr="model1", directory=fixpath(amoptd['work_dir'])
        )
        pdb_edit.extract_model(nativePdb, nativePdb1, modelID=nativePdbInfo.models[0].serial)
        nativePdb = nativePdb1

    # Standardise the PDB to rename any non-standard AA, remove solvent etc
    nativePdbStd = ample_util.filename_append(filename=nativePdb, astr="std", directory=fixpath(amoptd['work_dir']))
    pdb_edit.standardise(nativePdb, nativePdbStd, del_hetatm=True)
    nativePdb = nativePdbStd

    # Get the new Info about the native
    nativePdbInfo = pdb_edit.get_info(nativePdb)

    # For comparsion of shelxe model we need a single chain from the native so we get this here
    if len(nativePdbInfo.models[0].chains) > 1:
        nativeChain1 = ample_util.filename_append(
            filename=nativePdbInfo.pdb, astr="chain1", directory=fixpath(amoptd['work_dir'])
        )
        pdb_edit.merge_chains(nativePdbInfo.pdb, nativeChain1)
    else:
        nativeChain1 = nativePdbInfo.pdb

    # Additional data
    amoptd['native_pdb_num_chains'] = len(nativePdbInfo.models[0].chains)
    amoptd['native_pdb_info'] = nativePdbInfo
    amoptd['native_pdb_std'] = nativePdbStd
    amoptd['native_pdb_1chain'] = nativeChain1
    amoptd['native_pdb_origin_info'] = originInfo

    return


def analyseSolution(amoptd, d, mrinfo):
    logger.info("Benchmark: analysing result: {0}".format(d['ensemble_name']))

    mrPdb = None
    if d['MR_program'] == "PHASER":
        mrPdb = d['PHASER_pdbout']
        mrMTZ = d['PHASER_mtzout']
    elif d['MR_program'] == "MOLREP":
        mrPdb = d['MOLREP_pdbout']
    elif d['MR_program'] == "unknown":
        return

    if mrPdb is None or not os.path.isfile(mrPdb):
        # logger.critical("Cannot find mrPdb {0} for solution {1}".format(mrPdb,d))
        return

    # debug - copy into work directory as reforigin struggles with long pathnames
    shutil.copy(mrPdb, os.path.join(fixpath(amoptd['benchmark_dir']), os.path.basename(mrPdb)))

    mrPdbInfo = pdb_edit.get_info(mrPdb)

    d['num_placed_chains'] = mrPdbInfo.numChains()
    d['num_placed_atoms'] = mrPdbInfo.numAtoms()
    d['num_placed_CA'] = mrPdbInfo.numCalpha()

    if amoptd['native_pdb']:
        if not d['SHELXE_os']:
            logger.critical("mrPdb {0} has no SHELXE_os origin shift. Calculating...".format(mrPdb))
            mrinfo.analyse(mrPdb)
            mrOrigin = mrinfo.originShift
            d['SHELXE_MPE'] = mrinfo.MPE
            d['SHELXE_wMPE'] = mrinfo.wMPE
        else:
            mrOrigin = [c * -1 for c in d['SHELXE_os']]

        # Move pdb onto new origin
        originPdb = ample_util.filename_append(mrPdb, astr='offset', directory=fixpath(amoptd['benchmark_dir']))
        pdb_edit.translate(mrPdb, originPdb, mrOrigin)

        # offset.pdb is the mrModel shifted onto the new origin use csymmatch to wrap onto native
        csymmatch.Csymmatch().wrapModelToNative(
            originPdb,
            amoptd['native_pdb'],
            csymmatchPdb=os.path.join(
                fixpath(amoptd['benchmark_dir']), "phaser_{0}_csymmatch.pdb".format(d['ensemble_name'])
            ),
        )
        # can now delete origin pdb
        os.unlink(originPdb)

        # Calculate phase error for the MR PDB
        try:
            mrinfo.analyse(mrPdb)
            d['MR_MPE'] = mrinfo.MPE
            d['MR_wMPE'] = mrinfo.wMPE
        except Exception as e:
            logger.critical("Error analysing mrPdb: {0}\n{1}".format(mrPdb, e))

        # We cannot calculate the Reforigin RMSDs or RIO scores for runs where we don't have a full initial model
        # to compare to the native to allow us to determine which parts of the ensemble correspond to which parts of
        # the native structure - or if we were unable to calculate a res_seq_map
        if not (
                amoptd['homologs']
                or amoptd['ideal_helices']
                or amoptd['helical_ensembles']
                or amoptd['import_ensembles']
                or amoptd['single_model_mode']
                or amoptd['res_seq_map']
        ):

            # Get reforigin info
            rmsder = reforigin.ReforiginRmsd()
            try:
                rmsder.getRmsd(
                    nativePdbInfo=amoptd['native_pdb_info'],
                    placedPdbInfo=mrPdbInfo,
                    refModelPdbInfo=amoptd['ref_model_pdb_info'],
                    cAlphaOnly=True,
                    workdir=fixpath(amoptd['benchmark_dir']),
                )
                d['reforigin_RMSD'] = rmsder.rmsd
            except Exception as e:
                logger.critical("Error calculating RMSD: {0}".format(e))
                d['reforigin_RMSD'] = 999

            # Score the origin with all-atom and rio
            rioData = rio.Rio().scoreOrigin(
                mrOrigin,
                mrPdbInfo=mrPdbInfo,
                nativePdbInfo=amoptd['native_pdb_info'],
                resSeqMap=amoptd['res_seq_map'],
                workdir=fixpath(amoptd['benchmark_dir']),
            )

            # Set attributes
            d['AA_num_contacts'] = rioData.aaNumContacts
            d['RIO_num_contacts'] = rioData.rioNumContacts
            d['RIO_in_register'] = rioData.rioInRegister
            d['RIO_oo_register'] = rioData.rioOoRegister
            d['RIO_backwards'] = rioData.rioBackwards
            d['RIO'] = rioData.rioInRegister + rioData.rioOoRegister
            d['RIO_no_cat'] = rioData.rioNumContacts - (rioData.rioInRegister + rioData.rioOoRegister)
            d['RIO_norm'] = float(d['RIO']) / float(d['native_pdb_num_residues'])
        else:
            d['AA_num_contacts'] = None
            d['RIO_num_contacts'] = None
            d['RIO_in_register'] = None
            d['RIO_oo_register'] = None
            d['RIO_backwards'] = None
            d['RIO'] = None
            d['RIO_no_cat'] = None
            d['RIO_norm'] = None

        #     # Now get the helix
        #     helixSequence = contacts.Rio().helixFromContacts( contacts=rioData.contacts,
        #                                                            dsspLog=dsspLog )
        #     if helixSequence is not None:
        #         ampleResult.rioHelixSequence = helixSequence
        #         ampleResult.rioLenHelix      = len( helixSequence )
        #         hfile = os.path.join( workdir, "{0}.helix".format( ampleResult.ensembleName ) )
        #         with open( hfile, 'w' ) as f:
        #             f.write( helixSequence+"\n" )

        #
        # This purely for checking and so we have pdbs to view
        #
        # Wrap shelxe trace onto native using Csymmatch
        if not d['SHELXE_pdbout'] is None and os.path.isfile(fixpath(d['SHELXE_pdbout'])):
            csymmatch.Csymmatch().wrapModelToNative(
                fixpath(d['SHELXE_pdbout']),
                amoptd['native_pdb'],
                origin=mrOrigin,
                workdir=fixpath(amoptd['benchmark_dir']),
            )

        if not ('SHELXE_wMPE' in d and d['SHELXE_wMPE']):
            try:
                mrinfo.analyse(d['SHELXE_pdbout'])
                d['SHELXE_MPE'] = mrinfo.MPE
                d['SHELXE_wMPE'] = mrinfo.wMPE
            except Exception as e:
                logger.critical("Error analysing SHELXE_pdbout: {0}\n{1}".format(d['SHELXE_pdbout'], e))

        # Wrap parse_buccaneer model onto native
        if d['SXRBUCC_pdbout'] and os.path.isfile(fixpath(d['SXRBUCC_pdbout'])):
            # Need to rename Pdb as is just called buccSX_output.pdb
            csymmatchPdb = os.path.join(
                fixpath(amoptd['benchmark_dir']), "buccaneer_{0}_csymmatch.pdb".format(d['ensemble_name'])
            )

            csymmatch.Csymmatch().wrapModelToNative(
                fixpath(d['SXRBUCC_pdbout']),
                amoptd['native_pdb'],
                origin=mrOrigin,
                csymmatchPdb=csymmatchPdb,
                workdir=fixpath(amoptd['benchmark_dir']),
            )
            # Calculate phase error
            try:
                mrinfo.analyse(d['SXRBUCC_pdbout'])
                d['SXRBUCC_MPE'] = mrinfo.MPE
                d['SXRBUCC_wMPE'] = mrinfo.wMPE
            except Exception as e:
                logger.critical("Error analysing SXRBUCC_pdbout: {0}\n{1}".format(d['SXRBUCC_pdbout'], e))

        # Wrap parse_buccaneer model onto native
        if d['SXRARP_pdbout'] and os.path.isfile(fixpath(d['SXRARP_pdbout'])):
            # Need to rename Pdb as is just called buccSX_output.pdb
            csymmatchPdb = os.path.join(
                fixpath(amoptd['benchmark_dir']), "arpwarp_{0}_csymmatch.pdb".format(d['ensemble_name'])
            )

            csymmatch.Csymmatch().wrapModelToNative(
                fixpath(d['SXRARP_pdbout']),
                amoptd['native_pdb'],
                origin=mrOrigin,
                csymmatchPdb=csymmatchPdb,
                workdir=fixpath(amoptd['benchmark_dir']),
            )
            # Calculate phase error
            try:
                mrinfo.analyse(d['SXRARP_pdbout'])
                d['SXRARP_MPE'] = mrinfo.MPE
                d['SXRARP_wMPE'] = mrinfo.wMPE
            except Exception as e:
                logger.critical("Error analysing SXRARP_pdbout: {0}\n{1}".format(d['SXRARP_pdbout'], e))
    return


def cluster_script(amoptd, python_path="ccp4-python"):
    """Create the script for benchmarking on a cluster"""
    # write out script
    work_dir = amoptd['work_dir']
    script = Script(directory=work_dir, stem="submit_benchmark")
    pydir = os.path.abspath(os.path.dirname(__file__))
    benchmark_script = os.path.join(pydir, "benchmark_util.py")
    script.append("{0} {1} {2} {3}".format(python_path, "-u", benchmark_script, amoptd['results_path']))
    script.write()

    return script



def fixpath(path):
    # fix for analysing on a different machine
    if _oldroot and _newroot:
        return path.replace(_oldroot, _newroot)
    else:
        return path


# Run unit tests
if __name__ == "__main__":
    # Set up logging - could append to an existing log?
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # This runs the benchmarking starting from a pickled file containing an amopt dictionary.
    # - used when submitting the modelling jobs to a cluster
    if len(sys.argv) != 2 or not os.path.isfile(sys.argv[1]):
        logging.debug("benchmark script requires the path to a pickled amopt dictionary!")
        sys.exit(1)

    # Get the amopt dictionary
    amoptd = ample_util.read_amoptd(sys.argv[1])

    fl = logging.FileHandler(os.path.join(amoptd['work_dir'], "benchmark.log"))
    fl.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fl.setFormatter(formatter)
    logger.addHandler(fl)

    analyse(amoptd)
    ample_util.save_amoptd(amoptd)
