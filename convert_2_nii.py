###---test out nipype

import os                                    # system functions
import nipype.interfaces.dcm2nii as dcm2nii  # file conversion
import nipype.interfaces.fsl as fsl          # fsl
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.interfaces.io as nio			 # for data grabbing and sinking
import nipype.interfaces.utility as util	 # for defining input node


##=====define the pipeline engine
preProc = pe.Workflow(name='conv2nii')


##=====define the nodes

##node 0: input node to distribute inputs to everybody
inputnode = pe.Node(interface=util.IdentityInterface(fields=['run_list']),
		    name = 'c2nInputnode')


##node 0: convert volumes to nii
nii_vols = pe.MapNode(interface = dcm2nii.Dcm2nii(),
					 name = 'nii_vols',
					 iterfield = ['source_names'])
					 
##=====connect the nodes
##======connections
preProc.connect(inputnode, 'run_list', nii_vols, 'source_names')

