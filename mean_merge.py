
###---takes a bunch of nii files 

import os                                    # system functions
import nipype.interfaces.fsl as fsl          # fsl
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.interfaces.io as nio			 # for data grabbing and sinking
import nipype.interfaces.utility as util	 # for defining input node


##=====define the pipeline engine
preProc = pe.Workflow(name='meanmerge')


##=====define the nodes
##node 0: input node to distribute inputs to everybody
inputnode = pe.Node(interface=util.IdentityInterface(fields=['run_list']),
		     name = 'mmInputnode')


##node 1: get uncorrected mean
mean = pe.MapNode(interface = fsl.maths.MeanImage(),
	                              name = 'mean',
				      iterfield = 'in_file')
				 

##node 2: make a merged copy of the uncorrected volumes
merge = pe.Node(interface = fsl.Merge(dimension='t'),
					          name = 'merge')
					          
##======connections
preProc.connect(inputnode, 'run_list', mean, 'in_file')
preProc.connect(mean, 'out_file', merge, 'in_files');

