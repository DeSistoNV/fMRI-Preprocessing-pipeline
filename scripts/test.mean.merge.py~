import nipype.pipeline.engine as pe          # pypeline engine

##===========directories / parameter
basedir = '/Data/tmp/'
databasedir = 'basedir'
subjects = ['TN', 'CO']
dummyvol = 'MR-ST001-SE%0.3d-0002.dcm' ##nipype's dcm2nii wrapper needs a filename
run_template = 'MR-SE%0.3d-eja_ep2d_bold_1mm_1500TR/'+dummyvol

results_base_dir = basedir
results_container = '/Data/tmp/results/'

##===========name the runs
run_list = []
for ii in [3,4,5]:
	run_list.append(basedir+'%s/CO20110630/' % ('CO') + run_template % (ii, ii))

for ii in [2, 3]:
	run_list.append(basedir+'%s/CO20110701/' % ('CO') + run_template % (ii, ii))

ref_run = run_list[0]

##==========create a workflow
wf = pe.Workflow(name='workflow')
wf.base_dir = basedir

##==========gather all the nodes/pipelines
from convert_2_nii import preProc as conv2nii
from mean_merge import preProc as meanmerge

##==========inform the convert 2 nii node 
conv2nii.inputs.inputnode.run_list = run_list


##==========connect convert and mean/merge
wf.connect([
		    (conv2nii, meanmerge, [('nii_vols.converted_files', 'mmInputnode.run_list')])		    		   
		  ])

wf.run()	
 