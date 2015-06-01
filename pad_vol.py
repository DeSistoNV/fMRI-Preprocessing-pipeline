###---takes a bunch of nii files 

import os                                    # system functions
import nipype.interfaces.fsl as fsl          # fsl
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.interfaces.io as nio	     # for data grabbing and sinking
import nipype.interfaces.utility as util     # for defining input node


##=====define the pipeline engine
preProc = pe.Workflow(name='padVol')


##=====define the nodes
##node 0: input node to distribute inputs to everybody
pvInputNode = pe.Node(interface=util.IdentityInterface(fields=['run_list', 'padNum', 'nVols']), 
		     name = 'pvInputNode')


##node 1: get uncorrected mean
pvMean = pe.MapNode(interface = fsl.maths.MeanImage(),
	                              name = 'pvMean',
				      iterfield = 'in_file')

##node 2: pad with the mean volume
pad = pe.MapNode(interface = fsl.Merge(dimension='t'),
		name = 'pad',
		iterfield = ['in_files'])


padList = pe.MapNode(interface = util.Function(input_names = ['vol', 'mean', 'padNum'], output_names = ['out']),
		  name = 'padList',
		  iterfield = ['vol', 'mean'])
	  
	


##node 3: extract down to just the right size
extract = pe.MapNode(interface = fsl.utils.ExtractROI(t_min=0),
		      name = 'extract',
		      iterfield = ['in_file', 't_size'])



##======connections
preProc.connect([
			(pvInputNode, pvMean,    [('run_list', 'in_file')]),
			(pvInputNode, padList,   [('run_list', 'vol')]),
			#(pvInputNode, padList,   [('function_str', 'function_str')]),
			(pvMean, padList,        [('out_file', 'mean')]),
			(pvInputNode, padList,   [('padNum', 'padNum')]),
			(padList, pad,           [('out', 'in_files')]),
			(pad, extract,           [('merged_file', 'in_file')]),
			(pvInputNode, extract,   [('nVols', 't_size')])
		])






				 

					          