# Confirmed that the AFNI moco routine is "volreg", which there is a wrapper for in nipype.
from nipype.interfaces import afni as afni

import nipype.pipeline.engine as pe

from nipype.interfaces import fsl as fsl

from mean_merge import preProc as mm
import pandas as pd

import nipype.interfaces.io as nio      # for data sink node


import os


from nipype.interfaces.freesurfer import BBRegister

from anatomical_dbObj import fsl_preproc_inode

main_inputnode = fsl_preproc_inode() ## in MriDbObjs ; nipype superclass
      
pipeline_data_params = dict() # Select only...
pipeline_data_params['subject'] = 'TN'
pipeline_data_params['experiment'] = 'imagery.rf'

pipeline_data_params['run_list'] = []                      
pipeline_data_params['sess_list'] = []
pipeline_data_params['vox_res'] = []
pipeline_data_params['crop_this'] = ['med', 'med', 'min']  ##note that this will almost never be needed, and isn't need in this example
pipeline_data_params['db'] = db = '/home/nick/res1_s1r1.csv'



## putting above selections into input node
main_inputnode.panda_fields(
             subj=pipeline_data_params['subject'],
                 expID=pipeline_data_params['experiment'], 
                  runList = pipeline_data_params['run_list'],
                 sessList = pipeline_data_params['sess_list'],
                 cropRule = pipeline_data_params['crop_this'],
             db = pipeline_data_params['db'],
             vox_res = pipeline_data_params['vox_res']

      )   

import os                                    		# system functions
import nipype.interfaces.fsl as fsl          		# fsl
import nipype.pipeline.engine as pe          		# pypeline engine
import nipype.interfaces.io as nio			# for data sink node
from convert_2_nii import preProc as c2n		# conversion from dicom to nii
from mean_merge import preProc as mm		 	# to create volume movies before and after moco
from kill_ref import preProc as kr			# to remove the siemens reference scan for runs that need it
from pad_vol import preProc as pv			# to truncate or pad runs that went too long / short during the experiment
import nipype.interfaces.utility as util              # for defining input node
import nipype.interfaces.fsl.utils as fslutils





##================================================create workflows

##clone the mean/merge workflow
cor_mm = mm.clone('corrected_meanmerge')
uncor_mm = mm.clone('uncorrected_meanmerge')

##define the pre-processing workflow
preProc = pe.Workflow(name='fsl_preproc')

##================================================define workflow nodes
##input node to distribute inputs 

mag = '/musc.repo/Data/nickdesisto/3T.v.7T/Converted/Olman_s1r1/1_015_gre_field_mapping_2iso_20140912/Olman_s1r1_20140912_001_015_gre_field_mapping_2iso.nii'
phase = '/musc.repo/Data/nickdesisto/3T.v.7T/Converted/Olman_s1r1/1_016_gre_field_mapping_2iso_20140912/Olman_s1r1_20140912_001_016_gre_field_mapping_2iso.nii'

bet_frac = .2      # Intensity Threshold
bet_gradient = .0   # vertical gradient
## FUGUE
dwell = .00032      # EPI dwell time (bandwidth^-1)
unwarp_dir = 'z'    # unwarping direction

inputnode = pe.Node(interface = main_inputnode, name = 'inputnode')

print inputnode.inputs

bet_map = pe.Node(interface=fsl.BET(mask = True, robust = True,frac=bet_frac,vertical_gradient=bet_gradient,
    in_file = mag),
    name='bet_map')

bet = pe.MapNode(interface = fsl.BET(functional=True, frac = bet_frac, mask=True),
		name = 'bet',
		iterfield = 'in_file')

prep_map = pe.Node(interface=fsl.PrepareFieldmap(delta_TE = 1.02, in_phase = phase),
    name='prep_map')
			    
fugue = pe.MapNode(interface=fsl.FUGUE(dwell_time=dwell,unwarp_direction = unwarp_dir),
    iterfield= 'in_file',
    name     = 'fugue')

datasink = pe.Node(interface = nio.DataSink(parameterization = True),
    name = 'datasink')

volreg = pe.MapNode(interface=afni.Volreg(verbose = True,outputtype = 'NIFTI_GZ'),
    name='moco',
    iterfield = ['in_file'])

bbreg = pe.MapNode(interface = BBRegister(subject_id='s1000', init='fsl', contrast_type='t1',out_fsl_file = True),
    name = 'bbreg',
    iterfield = ['source_file'])

appX = pe.MapNode(interface = fsl.ApplyXfm(apply_xfm=True,interp='spline'),
    name = 'appX',
    iterfield = ['in_file','in_matrix_file'])

preProc.base_dir = '/mnt/ana_pipe_out'  # this dir

def grab(l):
    return l[0]


preProc.connect([ 
          (bet_map   , prep_map, [('mask_file'        , 'in_magnitude'         )]),
          (prep_map  , fugue,    [('out_fieldmap'     , 'fmap_in_file'         )]),  ## send the field map to fugue
          (inputnode , bet,      [('run_list'         , 'in_file'              )]),    ## send the epis to bet
          (bet       , fugue,    [('out_file'         , 'in_file'              )]),
          (fugue     , volreg,   [('unwarped_file'    , 'in_file'              )]),  
          (bet       , uncor_mm, [('out_file'         , 'mmInputnode.run_list' )]),            
          (volreg    , bbreg,    [('out_file'         , 'source_file'          )]),
          (bbreg     , appX,     [('out_fsl_file'     , 'in_matrix_file'       )]),
          (volreg    , appX,     [('out_file'         , 'in_file'              )]),
          (bet       , appX,     [(('out_file',grab ) , 'reference'            )]),
          (appX      , cor_mm,   [('out_file'         , 'mmInputnode.run_list' )]),
          (uncor_mm  , datasink, [('merge.merged_file', 'uncorrected_movie'    )]),     ##send everything to data sink
          (cor_mm    , datasink, [('merge.merged_file', 'corrected_movie'      )]),
          (appX      , datasink, [('out_file'         , 'final_aligned'        )])
      ])

nProcs = 8

preProc.write_graph(simple_form = True)
if nProcs > 1:
              preProc.run(plugin='MultiProc', plugin_args={'n_procs' : nProcs})
else:
             preProc.run()
