import nipype.pipeline.engine as pe          # pypeline engine

##===========directories / parameter
basedir = '/Data/tmp/testpadvol/'

wf = pe.Workflow(name='workflow')
wf.base_dir = basedir

##==========gather all the nodes/pipelines
from pad_vol import preProc as pv
from convert_2_nii import preProc as conv2nii
from kill_ref import preProc as kr


##==========inform the input node 
run_list = ['/Data/7T.cmrr/20110630-ST001-olman/MR-SE004-eja_ep2d_bold_1mm_1500TR', '/Data/7T.cmrr/20110630-ST001-olman/MR-SE005-eja_ep2d_bold_1mm_1500TR', '/Data/7T.cmrr/20110630-ST001-olman/MR-SE006-eja_ep2d_bold_1mm_1500TR']
rl = [x+'/MR-ST001-SE%0.3d-0002.dcm' % (i+4) for i,x in enumerate(run_list)] 
splooge = 'def func(vol, mean, padNum): return [vol]+[mean]*padNum'
conv2nii.inputs.c2nInputnode.run_list = rl
kr.inputs.krInputnode.t_size = 100000
kr.inputs.krInputnode.t_min = 1
pv.inputs.pvInputNode.padNum = 1
pv.inputs.pvInputNode.nVols = [170, 170, 170]
pv.inputs.padList.function_str = splooge
##==========connect convert and mean/merge

	
wf.connect([
	      (conv2nii, kr, [('nii_vols.converted_files', 'krInputnode.run_list')]),
	      (kr, pv,       [('dropref.roi_file', 'pvInputNode.run_list')])
	   ])
	   
wf.run()