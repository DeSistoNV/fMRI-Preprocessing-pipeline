###---takes a bunch of nii files 

import os                                    # system functions
import nipype.interfaces.fsl as fsl          # fsl
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.interfaces.io as nio	     # for data grabbing and sinking
import nipype.interfaces.utility as util     # for defining input node


##=====define the pipeline engine
preProc = pe.Workflow(name='killref')


##=====define the nodes
##node 0: input node to distribute inputs to everybody
inputnode = pe.Node(interface=util.IdentityInterface(fields=['run_list', 't_min', 't_size', 'x_min', 'x_size', 'y_min', 'y_size', 'z_min', 'z_size']),
		     name = 'krInputnode')

##conditional nodes/connections
dropref = pe.MapNode(interface = fsl.utils.ExtractROI(),
		      name = 'dropref',
		      iterfield = ['in_file', 't_min', 'x_min', 'x_size', 'y_min', 'y_size', 'z_min', 'z_size'])

  
##======un conditional connections
preProc.connect([(inputnode, dropref, [('run_list', 'in_file'),
				       ('t_min', 't_min'),
				       ('t_size', 't_size'),
				       ('x_size', 'x_size'),
				       ('x_min', 'x_min'),
				       ('y_min', 'y_min'),
				       ('y_size', 'y_size'),
				       ('z_min', 'z_min'),
				       ('z_size', 'z_size')])
		])

