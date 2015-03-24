import nipype.pipeline.engine as pe          # pypeline engine

##===========directories / parameter
basedir = '/Data/tmp/'
databasedir = 'basedir'
subjects = ['TN', 'CO']
dummyvol = 'MR-ST001-SE%0.3d-0002.dcm' ##nipype's dcm2nii wrapper needs a filename
run_template = 'MR-SE%0.3d-eja_ep2d_bold_1mm_1500TR/'+dummyvol

results_base_dir = basedir
results_container = '/Data/tmp/test.refvol/'

##===========name the runs
run_list = []
for ii in [3,4,5]:
	run_list.append(basedir+'%s/CO20110630/' % ('CO') + run_template % (ii, ii))

for ii in [2, 3]:
	run_list.append(basedir+'%s/CO20110701/' % ('CO') + run_template % (ii, ii))

ref_run = run_list[0]

##==========gather all the nodes/pipelines
from make_refvol import preProc as mr


##==========inform the convert 2 nii node 
mr.inputs.mrInputnode.ref_run = ref_run
mr.inputs.mrInputnode.results_base_dir = results_base_dir
mr.inputs.mrInputnode.results_container = results_container
mr.inputs.mrInputnode.data_base_dir = databasedir


##==========connect convert and mean/merge

mr.run()	
 