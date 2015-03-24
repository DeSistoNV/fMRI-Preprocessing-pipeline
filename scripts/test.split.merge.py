import nipype.pipeline.engine as pe          # pypeline engine

##===========directories / parameter
basedir = '/Data/tmp/test.split.merge/'

wf = pe.Workflow(name='workflow')
wf.base_dir = basedir

##==========gather all the nodes/pipelines
from split_merge import preProc as sm
from convert_2_nii import preProc as conv2nii



##==========inform the input node 
run_list = ['/Data/7T.cmrr/20110630-ST001-olman/MR-SE004-eja_ep2d_bold_1mm_1500TR', '/Data/7T.cmrr/20110630-ST001-olman/MR-SE005-eja_ep2d_bold_1mm_1500TR', '/Data/7T.cmrr/20110630-ST001-olman/MR-SE006-eja_ep2d_bold_1mm_1500TR']
rl = [x+'/MR-ST001-SE%0.3d-0002.dcm' % (i+4) for i,x in enumerate(run_list)] 
conv2nii.inputs.c2nInputnode.run_list = rl
##==========connect convert and mean/merge

	
wf.connect([
	      (conv2nii, sm, [('nii_vols.converted_files', 'smInputnode.run_list')])
	   ])
	   
wf.run()