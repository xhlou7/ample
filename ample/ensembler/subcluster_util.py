"""
02.03.2016

@author: hlfsimko
"""

import copy
import logging
import os
import random
import shutil

_logger = logging.getLogger(__name__)

def pick_nmodels(models, clusters, ensemble_max_models):
    MAXTRIES = 50
    tries = 0
    clusters = set(clusters)
    nmodels = min(len(models), ensemble_max_models)
    while True:
        subcluster = random.sample(models, nmodels)
        subcluster = tuple(sorted(subcluster))
        if subcluster not in clusters: break
        tries += 1
        if tries >= MAXTRIES: return None
    return subcluster

def slice_subcluster(cluster_files, previous_clusters, ensemble_max_models, radius, radius_thresholds):
    """Select a unique set of models from a subcluster of models.
    """
    len_cluster = len(cluster_files)
    if not len_cluster: return None
    len_radius_thresholds = len(radius_thresholds)
    if len_cluster <= ensemble_max_models:
        if cluster_files not in previous_clusters: return cluster_files
        else: return None
    
    if len_cluster > ensemble_max_models:
        idx = radius_thresholds.index(radius)
        selected = cluster_files[:ensemble_max_models]
        if idx == 0 or selected not in previous_clusters: return selected
        
        # Here we have more models then we need, but the first slice has already been selected
        # we therefore need to select another slice
        
        # If last radius threshold, just take the slice to the end
        if idx + 1 == len_radius_thresholds:
            start = len_cluster - ensemble_max_models
            selected = cluster_files[start:]
            if selected not in previous_clusters:
                return selected
            else:
                return None
        
        # Work out how many residues are extra
        remainder = len_cluster - ensemble_max_models
        
        # Use the position of the radius in the list of radii to work out where to start this slice
        prop = float(idx) / float(len(radius_thresholds) - 1)  # -1 as the first is always at the start
        
        # Work out how many residues in to the remainder to start
        start = int(round(float(remainder) * prop))
        selected = cluster_files[start :  start + ensemble_max_models]
        if selected and selected not in previous_clusters:
                return selected
        else:
            return None
    
    return None

def subcluster_nmodels(nmodels, radius, clusterer, direction, increment):

    MINRADIUS = 0.0001
    MAXRADIUS = 100
    
    subcluster_models = clusterer.cluster_by_radius(radius)
    len_models = len(subcluster_models) if subcluster_models else 0
    
    _logger.debug("subcluster nmodels: {0} {1} {2} {3} {4}".format(len_models, nmodels, radius, direction, increment))
    if len_models == nmodels or radius < MINRADIUS or radius > MAXRADIUS:
        _logger.debug("nmodels: {0} radius: {1}".format(len_models, radius))
        return subcluster_models, radius
    
    def lower_increment(increment):
        increment = increment / float(10)
        if increment <= 0.00001: raise RuntimeError, "increment out of bounds"
        return increment
    
    # Am sure the logic could be improved here, but it seems to  work
    try:
        if len_models > nmodels:
            # If we have more models than we want and we are increasing the radius, we've overshot, so we need to
            # decrease the radius but by a smaller increment
            # If the radius is the same as the increment, we need to decrease the incrememnt before we subtract it
            # as both of the above require decreasing the increment we have one test and just change the direction
            # for the overshoot
            if direction == 'up' or abs(radius - increment) < 0.0000001:
                if direction == 'up': direction = 'down'
                increment = lower_increment(increment)
            radius -= increment
        elif len_models < nmodels:
            if direction == 'down' :
                direction = 'up'
                increment = lower_increment(increment)
            radius += increment
    except RuntimeError:
        # Can't get a match so just return what we have
        _logger.debug("subcluster nmodels exceeded increment. Returning: nmodels: {0} radius: {1}".format(len(subcluster_models), radius))
        return subcluster_models, radius
        
    return subcluster_nmodels(nmodels, radius, clusterer, direction, increment)

def subcluster_radius(models, radius, truncated_models_data):
    # Extract data from dictionary
    cluster_num = truncated_models_data['cluster_num']
    truncation_level = truncated_models_data['truncation_level']
    truncation_dir = truncated_models_data['truncation_dir']

    # Got files so create the directories
    subcluster_dir = os.path.join(truncation_dir, 'subcluster_{0}'.format(radius))
    os.mkdir(subcluster_dir)
    os.chdir(subcluster_dir)

    basename = 'c{0}_t{1}_r{2}'.format(cluster_num, truncation_level, radius)
    cluster_file = self.superpose_models(models)
    if not cluster_file:
        msg = "Error running theseus on ensemble {0} in directory: {1}\nSkipping subcluster: {0}".format(basename,
                                                                                            subcluster_dir)
        _logger.critical(msg)
        raise RuntimeError, msg
    
    ensemble = os.path.join(subcluster_dir, basename + '.pdb')
    shutil.move(cluster_file, ensemble)

    # The data we've collected is the same for all pdbs in this level so just keep using the first  
    subcluster_data = copy.copy(truncated_models_data)
    subcluster_data['subcluster_num_models'] = len(models)
    subcluster_data['subcluster_radius_threshold'] = radius
    subcluster_data['ensemble_pdb'] = ensemble

    # Get the centroid model name from the list of files given to theseus - we can't parse
    # the pdb file as theseus truncates the filename
    subcluster_data['subcluster_centroid_model'] = os.path.abspath(models[0])
    return ensemble, subcluster_data
