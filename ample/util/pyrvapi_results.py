#!/usr/bin/env ccp4-python
"""Module to interact with pyrvapi

Notes
-----

:obj:`remove_widget()` may result in an unexpected unless you put :obj:`flush()` immediately before **and** immediately after calling them, e.g.:

.. code-block:: python
   
   >>> pyrvapi_flush()
   >>> for i in range():
   ...     rvapi_remove_widget(..i..)
   >>> rvapi_flush()

This is because chronology of rvapi calls between flushes is not necessarily the same as chronology of making/changing widgets in the page. E.g. in sequence of calls:

.. code-block:: python

   >>> rvapi_flush()
   >>> rvapi_action1()
   >>> rvapi_action2()
   >>> rvapi_action3()
   >>> rvapi_flush()
   >>> rvapi_action4()
   >>> rvapi_action5()
   >>> rvapi_action6()
   >>> rvapi_flush()

it is guaranteed that results of actions 4-6 will appear after results from 1-3, but there is no guarantee that results from 1-3 and 4-6 groups will appear in exactly that order. E.g., the page may perform actions like  3-1-2-5-4-6, but never like 6-4-1-2-3-5.

"""

__author__ = "Jens Thomas"
__date__ = "03 Mar 2015"
__version__ = "1.0"

import logging
import os
import subprocess
import urlparse
import uuid

from ample import ensembler
from ample.util import ample_util
from ample.util import mrbump_util

try: import pyrvapi
except: pyrvapi = None

# Hack to use Andre's pyrvapi API
import pyrvapi_ext as API

logger = logging.getLogger(__name__)

class AmpleOutput(object):
    """Display the output of an AMPLE job
    
    """
    
    _ensemble_tooltips = {
               "Name" : "Ensemble name - used to name the pdb file and the directory where mrbump carries out molecular replacement.",
               "Cluster" : "The SPICKER cluster that this ensemble was derived from.",
               "Truncation Level" : "Percentage of the model remaining after the varying residues were pruned away",
               "Variance Threshold (A^2)" : "THESEUS variance score for the most variable residue that remains in this ensemble",
               "No. Residues" : "Number of residues for each model in the ensemble",
               "Radius Threshold (A)" : "Radius threshold (1,2 or 3 A) used for subclustering the models in a truncation level",
               "No. Decoys" : "Number of models within this ensemble",
               "Number of Atoms" : "Number of atoms for each model in the ensemble",
               "Sidechain Treatment" : "allatom - all sidechains were retained, reliable - MET, ASP, PRO, GLN, LYS, ARG, GLU, SER were retained, polyAla - all sidechains were stripped back to polyalanine",
               }
    
    _mrbump_tooltips = {
               "ensemble_name" : "The identifier of the AMPLE ensemble search model",
               "MR_program" : "Molecular replacement program",
               "Solution_Type" : "MRBUMP categorisation of the solution",
               "PHASER_LLG" : "PHASER Log-likelihood gain for the Molecular Replacement solution",
               "PHASER_TFZ" : "PHASER Translation Function Z-score for the Molecular Replacement solution",
               "REFMAC_Rfact" : "Rfact score for REFMAC refinement of the Molecular Replacement solution",
               "REFMAC_Rfree" : "Rfree score for REFMAC refinement of the Molecular Replacement solution",
               "BUCC_final_Rfact" : "Rfact score for BUCCANEER rebuild of the Molecular Replacement solution",
               "BUCC_final_Rfree" : "Rfree score for BUCCANEER rebuild of the Molecular Replacement solution",
               "ARP_final_Rfact" : "Rfact score for ARPWARP rebuild of the Molecular Replacement solution",
               "ARP_final_Rfree" : "Rfree score for ARPWARP rebuild of the Molecular Replacement solution",
               "SHELXE_CC" : "SHELXE Correlation Coefficient score after C-alpha trace",
               "SHELXE_ACL" : "Average Chain Length of the fragments of the SHELXE C-alpha trace",
               "SXRBUCC_final_Rfact" : "Rfact score for BUCCANEER rebuild of the SHELXE C-alpha trace",
               "SXRBUCC_final_Rfree" : "Rfree score for BUCCANEER rebuild of the SHELXE C-alpha trace",
               "SXRARP_final_Rfact" : "Rfact score for ARPWARP rebuild of the SHELXE C-alpha trace",
               "SXRAP_final_Rfree" : "Rfree score for ARPWARP rebuild of the SHELXE C-alpha trace",
               }
    
    def __init__(self, amopt, report_dir=None, xml=None, own_gui=False):
        self.header = False
        self.log_tab_id = None
        self.old_mrbump_results = None
        self.results_tab_id = None
        self.results_tab_sections = []
        self.summary_tab_id = None
        self.summary_tab_ensemble_sec_id = None
        self.summary_tab_results_sec_id = None
        self.summary_tab_survey_sec_id = None
        self.webserver_uri = None
        self.wbeserver_start = None
        
        self.setup(amopt, report_dir=report_dir, xml=xml, own_gui=own_gui)
        return

    def setup(self, amopt, report_dir=None, document=None, xml=None, own_gui=False):
        if not pyrvapi or ('no_gui' in amopt and amopt['no_gui']): return
        
        # Infrastructure to run
        if not report_dir: report_dir = os.path.join(amopt['work_dir'], "jsrview")
        if not os.path.isdir(report_dir): os.mkdir(report_dir)
        
        docid = "AMPLE_results"
        title = "AMPLE Results"
        if True:
            share_jsrview = os.path.join(os.environ["CCP4"], "share", "jsrview")
            pyrvapi.rvapi_init_document (docid, report_dir, title, 1, 7, share_jsrview, None, None, None, None)
        else:
            # Quick hack to init with Andre's stuff
            if document:
                API.document.fromfile(document)
            else:
                kwargs = dict(
                  wintitle = title,
                  reportdir = report_dir,
                  xml = xml,
                  abspaths = False,
                # bug in jsrview:
                # layout = 4 if i1 else 7,
                )
                API.document.newdoc(**kwargs)

        if 'webserver_uri' in amopt and amopt['webserver_uri']:
            # don't start browser and setup variables for the path on the webserver
            self._webserver_start = len(amopt['run_dir']) + 1
            self.webserver_uri = amopt['webserver_uri']
            
        if own_gui:
            # We start our own browser
            jsrview = os.path.join(os.environ["CCP4"], "libexec", "jsrview")
            subprocess.Popen([jsrview, os.path.join(report_dir, "index.html")])
        return
    
    def create_log_tab(self, ample_dict):
        if self.log_tab_id: return
        logfile = ample_dict['ample_log']
        if not os.path.isfile(logfile): return False
        
        self.log_tab_id = "log_tab"
        logurl = self.fix_path(logfile)
        pyrvapi.rvapi_add_tab(self.log_tab_id, "Log file", True)  # Last arg is "open" - i.e. show or hide
        
        # Add watched (updatable) content to the log tab.
        pyrvapi.rvapi_append_content(logurl, True, self.log_tab_id)
        # pyrvapi.rvapi_flush()
        return self.log_tab_id
    
    def create_results_tab(self, ample_dict):
        if not self.summary_tab_id: return
        if not self._got_mrbump_results(ample_dict): return
        
        mrb_results = ample_dict['mrbump_results']
        if mrb_results == self.old_mrbump_results: return
        self.old_mrbump_results = mrb_results
        
        if not self.results_tab_id:
            self.results_tab_id = "results_tab"
            # Insert results tab before summary tab
            pyrvapi.rvapi_insert_tab(self.results_tab_id, "Results", self.summary_tab_id, False)  # Last arg is "open" - i.e. show or hide
        
        # Delete old sections:
        pyrvapi.rvapi_flush()
        for section_id in self.results_tab_sections:
            pyrvapi.rvapi_remove_widget(section_id)
        pyrvapi.rvapi_flush()
        self.results_tab_sections = []
        
        ensemble_results = None
        if self._got_ensemble_data(ample_dict):
            ensemble_results = ample_dict['ensembles_data']
            
        mrbsum = mrbump_util.ResultsSummary(results=mrb_results[0:min(len(mrb_results),mrbump_util.TOP_KEEP)])
        mrbsum.sortResults(prioritise="SHELXE_CC")
        self.results_section(self.results_tab_id,
                             mrbsum.results,
                             ensemble_results,
                             "Top {0} SHELXE Results".format(mrbump_util.TOP_KEEP))
        mrbsum.sortResults(prioritise="PHASER_TFZ")
        self.results_section(self.results_tab_id,
                             mrbsum.results,
                             ensemble_results,
                             "Top {0} PHASER Results".format(mrbump_util.TOP_KEEP))
        
        return self.results_tab_id
    
    def _create_summary_tab(self):
        if not self.summary_tab_id:
            self.summary_tab_id = "summary_tab"
            # Insert summary tab before log tab
            pyrvapi.rvapi_insert_tab(self.summary_tab_id, "Summary", self.log_tab_id, False)  # Last arg is "open" - i.e. show or hide
        return

    def create_summary_tab(self, ample_dict):
        #
        # Summary Tab
        #
        if not self.log_tab_id: return
        if not (ample_dict['single_model_mode'] or ample_dict['homologs'] or not self._got_ensemble_data(ample_dict)):
            ensembles_data = ample_dict['ensembles_data']
            
            self._create_summary_tab()
                
            # Hack to cope with ideal helices and importing ensembles
            def do_ensemble_sec(ample_dict):
                return not (ample_dict['ideal_helices'] or ample_dict['import_ensembles'] or ample_dict['homologs'])
                
            if not self.summary_tab_ensemble_sec_id and do_ensemble_sec(ample_dict): 
                self.summary_tab_ensemble_sec_id = "ensembles"
                pyrvapi.rvapi_add_section(self.summary_tab_ensemble_sec_id, "Ensembles", self.summary_tab_id, 0, 0, 1, 1, True)
                
                # Get the ensembling data
                d = ensembler.collate_cluster_data(ensembles_data)
                clusters = d['clusters']
                
                rstr = ""
                rstr += "Ensemble Results<br/>"
                rstr += "----------------<br/><br/>"
                rstr += "Cluster method: {0}<br/>".format(d['cluster_method'])
                rstr += "Cluster score type: {0}<br/>".format(d['cluster_score_type'])
                rstr += "Truncation method: {0}<br/>".format(d['truncation_method'])
                rstr += "Percent truncation: {0}<br/>".format(d['percent_truncation'])
                rstr += "Side-chain treatments: {0}<br/>".format(d['side_chain_treatments'])
                rstr += "Number of clusters: {0}<br/><br/>".format(len(clusters.keys()))
                rstr += "Generated {0} ensembles<br/><br/>".format(len(ensembles_data))
                pyrvapi.rvapi_add_text(rstr, self.summary_tab_ensemble_sec_id, 0, 0, 1, 1)
                
                ensemble_table = "ensemble_table"
                pyrvapi.rvapi_add_table1(self.summary_tab_ensemble_sec_id + "/" + ensemble_table, "Ensembling Results", 1, 0, 1, 1, True)
                # for cluster_num in sorted(clusters.keys()):
                #     rstr += "\n"
                #     rstr += "Cluster {0}\n".format(cluster_num)
                #     rstr += "Number of models: {0}\n".format(clusters[cluster_num]['cluster_num_models'])
                #     rstr += "Cluster centroid: {0}\n".format(clusters[cluster_num]['cluster_centroid'])
                #     rstr += "\n"
                #     tdata = cluster_table_data(clusters, cluster_num)
                #     rstr += tableFormat.pprint_table(tdata)        
                # 
                cluster_num = 1
                tdata = ensembler.cluster_table_data(clusters, cluster_num, d['side_chain_treatments'])
                self.fill_table(ensemble_table, tdata, tooltips=self._ensemble_tooltips)
        
        #
        # MRBUMP Results
        #
        if not self._got_mrbump_results(ample_dict): return self.summary_tab_id
        self._create_summary_tab()
        
        if not self.summary_tab_results_sec_id:
            # Only create the table once
            self.summary_tab_results_sec_id = "mrbump"
            pyrvapi.rvapi_add_section(self.summary_tab_results_sec_id, "MRBUMP", self.summary_tab_id, 0, 0, 1, 1, True)
            self.summary_tab_results_sec_table_id = "mrbump_table"
            pyrvapi.rvapi_add_table1(self.summary_tab_results_sec_id + "/" + self.summary_tab_results_sec_table_id, "MRBUMP Results", 1, 0, 1, 1, True)
        
        mrb_results = ample_dict['mrbump_results']
        if not mrb_results == self.old_mrbump_results:
            # We set old_mrbump_results when we create the results_tab
            self.fill_table(self.summary_tab_results_sec_table_id,
                             mrbump_util.ResultsSummary().results_table(mrb_results),
                             tooltips=self._mrbump_tooltips)
            
        #
        # Survey section
        #
        if not self.summary_tab_survey_sec_id:
            # Only create the table once
            self.summary_tab_survey_sec_id = "survey"
            pyrvapi.rvapi_add_section(self.summary_tab_survey_sec_id, "Feedback", self.summary_tab_id, 0, 0, 1, 1, True)
            rstr = "<h2>How did we do?</h2><h3>Please follow this link and leave some feedback:</h3><a href='{0}' style='color: blue'>{0}</a>".format(ample_util.survey_url)
            pyrvapi.rvapi_add_text(rstr, self.summary_tab_survey_sec_id, 0, 0, 1, 1)
            
        return self.summary_tab_id

    def display_results(self, ample_dict, run_dir=None):
        if not pyrvapi or ('no_gui' in ample_dict and ample_dict['no_gui']): return
        if not self.header:
            pyrvapi.rvapi_add_header("AMPLE Results")
            self.header = True
        self.create_log_tab(ample_dict)
        self.create_summary_tab(ample_dict)
        self.create_results_tab(ample_dict)
        pyrvapi.rvapi_flush()
        return True

    def ensemble_pdb(self, mrbump_result, ensembles_data):
        try:
            ensemble_dict = None
            for e in ensembles_data:
                if e['name'] == mrbump_result['ensemble_name']:
                    ensemble_dict = e
                    break
            if os.path.isfile(ensemble_dict['ensemble_pdb']):
                return ensemble_dict['ensemble_pdb']
            else:
                return False
        except:
            return False
    
    def fix_path(self, path):
        """Ammend path so it's suitable for the webserver"""
        if self.webserver_uri:
            return urlparse.urljoin(self.webserver_uri, path[self._webserver_start:])
        else: return path
        
    def fill_table(self, table_id, tdata, tooltips={}):
        # Make column headers
        for i in range(len(tdata[0])):  # Skip name as it's the row header
            h = tdata[0][i]
            tt = tooltips[h] if h in tooltips else ""
            pyrvapi.rvapi_put_horz_theader(table_id, h.encode('utf-8'), tt, i)  # Add table data
        
        for i in range(1, len(tdata)):
            for j in range(len(tdata[i])):
                pyrvapi.rvapi_put_table_string(table_id, str(tdata[i][j]), i - 1, j)
        
        # Now colour the ensemble name cells
        for i in range(len(tdata) - 1):
            pyrvapi.rvapi_shape_table_cell(table_id,  # tableId
                i,  # row
                0,  # column
                "",  # tooltip
                "",  # cell_css
                "table-blue-vh",  # cell_style
                1,  # rowSpan
                1)  # colSpan
        return
    
    def _got_mrbump_results(self, ample_dict):
        return 'mrbump_results' in ample_dict and len(ample_dict['mrbump_results'])

    def _got_ensemble_data(self, ample_dict):
        return 'ensembles_data' in ample_dict and len(ample_dict['ensembles_data'])

    def results_section(self, results_tab_id, mrb_results, ensemble_results, section_title):
        #
        # Results Tab
        #
        if not mrb_results: return
    
        # Create unique identifier for this section by using the id
        # All ids will have this appended to avoid clashes
        uid = str(uuid.uuid4())
        
        section_id = section_title.replace(" ","_") + uid
        self.results_tab_sections.append(section_id) # Add to list so we can remove if we update
        
        pyrvapi.rvapi_add_panel(section_id, results_tab_id, 0, 0, 1, 1)
        pyrvapi.rvapi_add_text("<h3>{0}</h3>".format(section_title), section_id, 0, 0, 1, 1)
    
        results_tree = "results_tree" + section_id
        pyrvapi.rvapi_add_tree_widget(results_tree, section_title, section_id, 0, 0, 1, 1)
        
        for r in mrb_results:
            name = r['ensemble_name']
            # container_id="sec_{0}".format(name)
            # pyrvapi.rvapi_add_section(container_id,"Results for: {0}".format(name),results_tree,0,0,1,1,True)
            container_id = "sec_{0}".format(name) + uid
            pyrvapi.rvapi_add_panel(container_id, results_tree, 0, 0, 1, 1)
            
            header = "<h3>Results for ensemble: {0}</h3>".format(name)
            pyrvapi.rvapi_add_text(header, container_id, 0, 0, 1, 1)
            
            sec_table = "sec_table_{0}".format(name) + uid
            title = "Results table: {0}".format(name)
            title = "Summary"
            pyrvapi.rvapi_add_section(sec_table, title, container_id, 0, 0, 1, 1, True)
            table_id = "table_{0}".format(name) + uid
            pyrvapi.rvapi_add_table(table_id, "", sec_table, 1, 0, 1, 1, False)
            tdata = mrbump_util.ResultsSummary().results_table([r])
            self.fill_table(table_id, tdata, tooltips=self._mrbump_tooltips)
            
            # Ensemble
            if ensemble_results:
                epdb = self.ensemble_pdb(r, ensemble_results)
                if epdb:
                    sec_ensemble = "sec_ensemble_{0}".format(name) + uid
                    pyrvapi.rvapi_add_section(sec_ensemble, "Ensemble Search Model", container_id, 0, 0, 1, 1, False)
                    data_ensemble = "data_ensemble_{0}".format(name) + uid
                    pyrvapi.rvapi_add_data(data_ensemble,
                                            "Ensemble PDB",
                                            self.fix_path(epdb),
                                            "XYZOUT",
                                            sec_ensemble,
                                            2, 0, 1, 1, True)
            # PHASER
            if os.path.isfile(str(r['PHASER_logfile'])) or (os.path.isfile(str(r['PHASER_pdbout'])) and os.path.isfile(str(r['PHASER_mtzout']))):
                sec_phaser = "sec_phaser_{0}".format(name) + uid
                pyrvapi.rvapi_add_section(sec_phaser, "PHASER Outputs", container_id, 0, 0, 1, 1, False)
                if os.path.isfile(str(r['PHASER_pdbout'])) and os.path.isfile(str(r['PHASER_mtzout'])):
                    data_phaser = "data_phaser_out_{0}".format(name) + uid
                    pyrvapi.rvapi_add_data(data_phaser,
                                            "PHASER PDB",
                                            os.path.splitext(self.fix_path(r['PHASER_pdbout']))[0],
                                            "xyz:map",
                                            sec_phaser,
                                            2, 0, 1, 1, True)
                    pyrvapi.rvapi_append_to_data(data_phaser, self.fix_path(r['PHASER_mtzout']), "xyz:map")
                if os.path.isfile(str(r['PHASER_logfile'])):
                    pyrvapi.rvapi_add_data("data_phaser_logfile_{0}".format(name),
                                            "PHASER Logfile",
                                            self.fix_path(r['PHASER_logfile']),
                                            "text",
                                            sec_phaser,
                                            2, 0, 1, 1, True)
                    
            # REFMAC
            if os.path.isfile(str(r['REFMAC_logfile'])) or (os.path.isfile(str(r['REFMAC_pdbout'])) and os.path.isfile(str(r['REFMAC_mtzout']))):
                sec_refmac = "sec_refmac_{0}".format(name) + uid
                pyrvapi.rvapi_add_section(sec_refmac, "REFMAC Outputs", container_id, 0, 0, 1, 1, False)
                if os.path.isfile(str(r['REFMAC_pdbout'])) and os.path.isfile(str(r['REFMAC_mtzout'])):
                    data_refmac = "data_refmac_out_{0}".format(name) + uid
                    pyrvapi.rvapi_add_data(data_refmac,
                                            "REFMAC PDB",
                                            os.path.splitext(self.fix_path(r['REFMAC_pdbout']))[0],
                                            "xyz:map",
                                            sec_refmac,
                                            2, 0, 1, 1, True)
                    pyrvapi.rvapi_append_to_data(data_refmac, self.fix_path(r['REFMAC_mtzout']), "xyz:map")
                if os.path.isfile(str(r['REFMAC_logfile'])):
                    pyrvapi.rvapi_add_data("data_refmac_logfile_{0}".format(name),
                                            "REFMAC Logfile",
                                            self.fix_path(r['REFMAC_logfile']),
                                            "text",
                                            sec_refmac,
                                            2, 0, 1, 1, True)
    
            # Buccaner
            if os.path.isfile(str(r['BUCC_logfile'])) or (os.path.isfile(str(r['BUCC_pdbout'])) and os.path.isfile(str(r['BUCC_mtzout']))):
                sec_bucc = "sec_bucc_{0}".format(name) + uid
                pyrvapi.rvapi_add_section(sec_bucc, "BUCCANEER Outputs", container_id, 0, 0, 1, 1, False)
                if os.path.isfile(str(r['BUCC_pdbout'])) and os.path.isfile(str(r['BUCC_mtzout'])):
                    data_bucc = "data_bucc_out_{0}".format(name) + uid
                    pyrvapi.rvapi_add_data(data_bucc,
                                            "BUCC PDB",
                                            os.path.splitext(self.fix_path(r['BUCC_pdbout']))[0],
                                            "xyz:map",
                                            sec_bucc,
                                            2, 0, 1, 1, True)
                    pyrvapi.rvapi_append_to_data(data_bucc, self.fix_path(r['BUCC_mtzout']), "xyz:map")
                if os.path.isfile(str(r['BUCC_logfile'])):
                    pyrvapi.rvapi_add_data("data_bucc_logfile_{0}".format(name),
                                            "BUCC Logfile",
                                            self.fix_path(r['BUCC_logfile']),
                                            "text",
                                            sec_bucc,
                                            2, 0, 1, 1, True)
                    
            # Arpwarp
            if os.path.isfile(str(r['ARP_logfile'])) or (os.path.isfile(str(r['ARP_pdbout'])) and os.path.isfile(str(r['ARP_mtzout']))):
                sec_arp = "sec_arp_{0}".format(name) + uid
                pyrvapi.rvapi_add_section(sec_arp, "ARPWARP Outputs", container_id, 0, 0, 1, 1, False)
                if os.path.isfile(str(r['ARP_pdbout'])) and os.path.isfile(str(r['ARP_mtzout'])):
                    data_arp = "data_arp_out_{0}".format(name) + uid
                    pyrvapi.rvapi_add_data(data_arp,
                                            "ARP PDB",
                                            os.path.splitext(self.fix_path(r['ARP_pdbout']))[0],
                                            "xyz:map",
                                            sec_arp,
                                            2, 0, 1, 1, True)
                    pyrvapi.rvapi_append_to_data(data_arp, self.fix_path(r['ARP_mtzout']), "xyz:map")
                if os.path.isfile(str(r['ARP_logfile'])):
                    pyrvapi.rvapi_add_data("data_arp_logfile_{0}".format(name),
                                            "ARP Logfile",
                                            self.fix_path(r['ARP_logfile']),
                                            "text",
                                            sec_arp,
                                            2, 0, 1, 1, True)
    
          
            # SHELXE
            if os.path.isfile(str(r['SHELXE_logfile'])) or (os.path.isfile(str(r['SHELXE_pdbout'])) and os.path.isfile(str(r['SHELXE_mtzout']))):
                sec_shelxe = "sec_shelxe_{0}".format(name) + uid
                pyrvapi.rvapi_add_section(sec_shelxe, "SHELXE Outputs", container_id, 0, 0, 1, 1, False)
                if os.path.isfile(str(r['SHELXE_pdbout'])) and os.path.isfile(str(r['SHELXE_mtzout'])):
                    data_shelxe = "data_shelxe_out_{0}".format(name) + uid
                    pyrvapi.rvapi_add_data(data_shelxe,
                                            "SHELXE PDB",
                                            os.path.splitext(self.fix_path(r['SHELXE_pdbout']))[0],
                                            "xyz:map",
                                            sec_shelxe,
                                            2, 0, 1, 1, True)
                    pyrvapi.rvapi_append_to_data(data_shelxe, self.fix_path(r['SHELXE_mtzout']), "xyz:map")
                if os.path.isfile(str(r['SHELXE_logfile'])):
                    pyrvapi.rvapi_add_data("data_shelxe_logfile_{0}".format(name),
                                            "SHELXE Logfile",
                                            self.fix_path(r['SHELXE_logfile']),
                                            "text",
                                            sec_shelxe,
                                            2, 0, 1, 1, True)
            
            # Buccaner Rebuild
            if os.path.isfile(str(r['SXRBUCC_logfile'])) or (os.path.isfile(str(r['SXRBUCC_pdbout'])) and os.path.isfile(str(r['SXRBUCC_mtzout']))):
                sec_sxrbucc = "sec_sxrbucc_{0}".format(name) + uid
                pyrvapi.rvapi_add_section(sec_sxrbucc, "BUCCANEER SHELXE Trace Rebuild Outputs", container_id, 0, 0, 1, 1, False)
                if os.path.isfile(str(r['SXRBUCC_pdbout'])) and os.path.isfile(str(r['SXRBUCC_mtzout'])):
                    data_sxrbucc = "data_sxrbucc_out_{0}".format(name) + uid
                    pyrvapi.rvapi_add_data(data_sxrbucc,
                                            "SXRBUCC PDB",
                                            os.path.splitext(self.fix_path(r['SXRBUCC_pdbout']))[0],
                                            "xyz:map",
                                            sec_sxrbucc,
                                            2, 0, 1, 1, True)
                    pyrvapi.rvapi_append_to_data(data_sxrbucc, self.fix_path(r['SXRBUCC_mtzout']), "xyz:map")
                if os.path.isfile(str(r['SXRBUCC_logfile'])):
                    pyrvapi.rvapi_add_data("data_sxrbucc_logfile_{0}".format(name),
                                            "SXRBUCC Logfile",
                                            self.fix_path(r['SXRBUCC_logfile']),
                                            "text",
                                            sec_sxrbucc,
                                            2, 0, 1, 1, True)
                    
            # Arpwarp Rebuild
            if os.path.isfile(str(r['SXRARP_logfile'])) or (os.path.isfile(str(r['SXRARP_pdbout'])) and os.path.isfile(str(r['SXRARP_mtzout']))):
                sec_sxrarp = "sec_sxrarp_{0}".format(name) + uid
                pyrvapi.rvapi_add_section(sec_sxrarp, "ARPWARP SHELXE Trace Redbuild Outputs", container_id, 0, 0, 1, 1, False)
                if os.path.isfile(str(r['SXRARP_pdbout'])) and os.path.isfile(str(r['SXRARP_mtzout'])):
                    data_sxrarp = "data_sxrarp_out_{0}".format(name) + uid
                    pyrvapi.rvapi_add_data(data_sxrarp,
                                            "SXRARP PDB",
                                            os.path.splitext(self.fix_path(r['SXRARP_pdbout']))[0],
                                            "xyz:map",
                                            sec_sxrarp,
                                            2, 0, 1, 1, True)
                    pyrvapi.rvapi_append_to_data(data_sxrarp, self.fix_path(r['SXRARP_mtzout']), "xyz:map")
                if os.path.isfile(str(r['SXRARP_logfile'])):
                    pyrvapi.rvapi_add_data("data_sxrarp_logfile_{0}".format(name),
                                            "SXRARP Logfile",
                                            self.fix_path(r['SXRARP_logfile']),
                                            "text",
                                            sec_sxrarp,
                                            2, 0, 1, 1, True)
            
            pyrvapi.rvapi_set_tree_node(results_tree, container_id, "{0}".format(name), "auto", "")
        return
            
if __name__ == "__main__":
    import copy, sys, time
    pklfile = sys.argv[1]
    ample_dict = ample_util.read_amoptd(pklfile)
    
    ample_dict['no_gui'] = False
    ample_dict['ample_log'] = os.path.abspath(__file__)

    report_dir = os.path.abspath(os.path.join(os.curdir,"pyrvapi_tmp"))
    AR = AmpleOutput(ample_dict, report_dir=report_dir, own_gui=True, xml=None)
    #AR.display_results(ample_dict)
     
    view1_dict = copy.copy(ample_dict)
    del view1_dict['ensembles_data']
    del view1_dict['mrbump_results']
     
    SLEEP = 5
     
    report_dir = os.path.abspath(os.path.join(os.curdir,"pyrvapi_tmp"))
    AR = AmpleOutput(view1_dict, report_dir=report_dir, own_gui=True, xml='jens.xml')
    AR.display_results(view1_dict)
    time.sleep(SLEEP)
     
    #for i in range(10):
    view1_dict['ensembles_data'] = ample_dict['ensembles_data']
    AR.display_results(view1_dict)
    time.sleep(SLEEP)
     
    mrbump_results = []
    for r in ample_dict['mrbump_results'][0:3]:
        r['SHELXE_CC'] = None
        r['SHELXE_ACL'] = None
        mrbump_results.append(r)
    view1_dict['mrbump_results'] = mrbump_results
    AR.display_results(view1_dict)
    time.sleep(SLEEP)
     
    view1_dict['mrbump_results'] = ample_dict['mrbump_results'][0:5]
    AR.display_results(view1_dict)  
    time.sleep(SLEEP)
     
    view1_dict['mrbump_results'] = ample_dict['mrbump_results']
    AR.display_results(view1_dict)  
