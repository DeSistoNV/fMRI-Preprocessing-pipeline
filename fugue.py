
# ---takes a bunch of nii files

import os                                    # system functions
import nipype.interfaces.fsl as fsl          # fsl
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.interfaces.io as nio			 # for data grabbing and sinking
import nipype.interfaces.utility as util	 # for defining input node
import nipype.interfaces.fsl.utils as fslutils
import sys

# =====define the pipeline engine
preProc = pe.Workflow(name='fugue_sub_pipe')


# =====define the nodes
# node 0: input node to distribute inputs to everybody
fugueInputnode = pe.Node(interface=util.IdentityInterface(
    fields=['in_files', 'phase', 'mags', 'delta_TE', 'mag_frac','dwell_time','unwarp_direction']),
    name='fugueInputnode')


strip_mag = pe.MapNode(interface=fsl.BET(mask=True, robust=True),
                       iterfield=['in_file'],
                       name='strip_mag')

prepare_field_map = pe.MapNode(interface=fsl.PrepareFieldmap(),
                               name='prepare_field_map',
                               iterfield=['in_phase', 'in_magnitude'])

fugue = pe.MapNode(
    interface=fsl.FUGUE(
                      save_shift=True),
    iterfield=['in_file', 'fmap_in_file'],
    name='fugue')

preProc.connect(fugueInputnode, 'mags', strip_mag, 'in_file')
preProc.connect(fugueInputnode,'delta_TE',prepare_field_map,'delta_TE')
preProc.connect(fugueInputnode,'mag_frac',strip_mag,'frac')
preProc.connect(fugueInputnode,'dwell_time',fugue,'dwell_time')
preProc.connect(fugueInputnode,'unwarp_direction',fugue,'unwarp_direction')
preProc.connect(strip_mag, 'out_file', prepare_field_map, 'in_magnitude')
preProc.connect(fugueInputnode,'phase',prepare_field_map,'in_phase')
preProc.connect(fugueInputnode,'in_files',fugue,'in_file')
preProc.connect(prepare_field_map,'out_fieldmap',fugue,'fmap_in_file')
