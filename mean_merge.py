
###---takes a bunch of nii files 

import os                                    # system functions
import nipype.interfaces.fsl as fsl          # fsl
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.interfaces.io as nio			 # for data grabbing and sinking
import nipype.interfaces.utility as util	 # for defining input node
import nipype.interfaces.fsl.maths as fslmaths

##=====define the pipeline engine
preProc = pe.Workflow(name='meanmerge')


##=====define the nodes
##node 0: input node to distribute inputs to everybody
inputnode = pe.Node(interface=util.IdentityInterface(fields=['run_list']),
		     name = 'mmInputnode')



##Take the mean of each run
mean_out = pe.MapNode(interface=fslmaths.MeanImage(),
		    name = 'mean_image',
		    iterfield = ['in_file']
		    )
		       				 

##node 2: make a merged copy of the uncorrected volumes
merge = pe.Node(interface = fsl.Merge(dimension='t'),
					          name = 'merge')
					          
##======connections


preProc.connect([( inputnode, mean_out,  [ ( 'run_list'                   , 'in_file'  )]),
			     ( mean_out,     merge,  [ ( 'out_file' ,'in_files')])
 		    	])
