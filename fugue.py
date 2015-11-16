
# ---takes a bunch of nii files

import os                                    # system functions
import nipype.interfaces.fsl as fsl          # fsl
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.interfaces.io as nio			 # for data grabbing and sinking
import nipype.interfaces.utility as util	 # for defining input node
import nipype.interfaces.fsl.utils as fslutils


# =====define the pipeline engine
preProc = pe.Workflow(name='fugue_sub_pipe')


# =====define the nodes
# node 0: input node to distribute inputs to everybody
inputnode = pe.Node(interface=util.IdentityInterface(
    fields=['in_files', 'phase', 'mags', 'delta_TE', 'mag_frac']),
    name='fugueInputnode')


strip_mag = pe.MapNode(interface=fsl.BET(mask=True, robust=True, frac=inputnode.inputs.mag_frac),
                       iterfield=['in_file'],
                       name='strip_mag')

prepare_field_map = pe.MapNode(interface=fsl.PrepareFieldmap(delta_TE=1.02),
                               name='prepare_field_map',
                               iterfield=['in_phase', 'in_magnitude'])

fugue = pe.MapNode(
    interface=fsl.FUGUE(dwell_time=.00032,
                        unwarp_direction='y',
                        save_shift=True),
    iterfield=['in_file', 'fmap_in_file'],
    name='fugue')

preProc.connect(inputnode, 'mags', strip_mag, 'in_file')
preProc.connect(strip_mag, 'out_file', prepare_field_map, 'in_magnitude')
preProc.connect(inputnode,'phase',prepare_field_map,'in_phase')
preProc.connect(inputnode,'in_files',fugue,'in_file')
preProc.connect(prepare_field_map,'out_fieldmap',fugue,'fmap_in_file')
