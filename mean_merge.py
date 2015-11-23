
###---takes a bunch of nii files 

import os                                    # system functions
import nipype.interfaces.fsl as fsl          # fsl
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.interfaces.io as nio			 # for data grabbing and sinking
import nipype.interfaces.utility as util	 # for defining input node
import nipype.interfaces.fsl.utils as fslutils

def first_and_last(l):
	o = []
	for i in l:
		o.append(i.pop())
		o.append(i.pop(0))
	print o	
	return o 
##=====define the pipeline engine
preProc = pe.Workflow(name='meanmerge')


##=====define the nodes
##node 0: input node to distribute inputs to everybody
inputnode = pe.Node(interface=util.IdentityInterface(fields=['run_list']),
		     name = 'mmInputnode')



##split the 4D volumes up into individual 3D files
split_out = pe.MapNode(interface = fslutils.Split(dimension = 't'),
		    name = 'split_out',
		    iterfield = ['in_file']
		    )
		       				 

##node 2: make a merged copy of the uncorrected volumes
merge = pe.Node(interface = fsl.Merge(dimension='t'),
					          name = 'merge')
					          
##======connections


preProc.connect([( inputnode, split_out,  [ ( 'run_list'                   , 'in_file'  )]),
			     ( split_out,     merge,  [ ( ('out_files', first_and_last) ,'in_files')])
 		    	])