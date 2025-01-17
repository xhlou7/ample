"""
Created on 28 May 2013

@author: jmht
"""

import logging
import os
import sys

# Our imports
from ample.util import ample_util
from iotbx.cif import reader as cif_reader

# TODO: Combine this with MTZ_util - make a reflection_file_util

class CifParser(object):
    """Class for manipulating CIF files."""

    def __init__(self):
        """Initialise from a ciFile"""

        self.hasRfree = False
        self.hasAmplitudes = False

        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)

        return

    def _parseCif(self, cifFile):

        self.hasRfree = False
        self.reflnStatus = False
        self.hasAmplitudes = False

        cifObject = cif_reader(file_path=cifFile).model()

        # For now assume only one dataSet
        assert len(cifObject.keys()) == 1, "More than one data set in sf_cif - not sure what to do!"
        data = cifObject[cifObject.keys()[0]]

        # See if any of the _refln.status columns are 'f' - indicating they've been set aside for RFree
        if "_refln.status" in data:
            self.reflnStatus = True
            self.hasRfree = any(map(lambda x: x == 'f', data["_refln.status"]))

        # Need to check we have structure factor amplitudes. For now just check - we
        # need to add code to use ctrunctate to convert if we only have intensities
        #
        # http://mmcif.pdb.org/dictionaries/mmcif_pdbx.dic/Categories/refln.html
        if "_refln.F_meas" in data or "_refln.F_meas_au" in data:
            self.hasAmplitudes = True

        return

    def _sfcif2mtz(self, cifPath, mtzPath):
        """Convert a CIF containing structure factors to an MTZ file."""

        cmd = ["cif2mtz", "hklin", cifPath, "hklout", mtzPath]
        logfile = os.path.join(os.getcwd(), "cif2mtz.log")
        # Need empty stdin to trigger eof to get program to run
        retcode = ample_util.run_command(cmd, stdin="", logfile=logfile)
        if retcode != 0:
            raise RuntimeError("Error running sfcif2mtz. Check the logfile: {0}".format(logfile))

    def sfcif2mtz(self, cifPath):
        """Convert a CIF containing structure factors to an MTZ file."""

        # Create a name for the mtz
        name = os.path.splitext(os.path.basename(cifPath))[0]
        mtzPath = os.path.join(os.getcwd(), name + ".mtz")

        self.logger.info("sfcif2mtz: sf-cif file will be converted to mtz: {0}".format(cifPath))

        # First parse the cif file - checks if amplitudes present and whether any reflections
        # have been set aside for RFree
        self._parseCif(cifPath)
        if not self.hasAmplitudes:
            raise RuntimeError("sfcif2mtz: no amplitudes in sf-cif - need to run ctruncate!")

        # Convert to mtz - this might add a spurious FREE column
        self._sfcif2mtz(cifPath, mtzPath)

        self.logger.info("sfcif2mtz: created mtz file: {0}".format(mtzPath))
        return mtzPath


if __name__ == '__main__':

    assert len(sys.argv) == 2
    cifpath = sys.argv[1]
    cp = CifParser()
    mtzPath = cp.sfcif2mtz(cifpath)
