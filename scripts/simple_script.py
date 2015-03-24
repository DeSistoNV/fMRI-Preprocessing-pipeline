import nipype.pipeline.engine as pe          # pypeline engine
import os

##===========directories / parameter

##CO
#basedir = '/Data/tmp/'
#databasedir = 'CO'#'/Data/7T.cmrr/20110715-ST001-Naselaris_subject/'
#subjects = ['TN', 'CO']
#dummyvol = 'MR-ST001-SE%0.3d-0002.dcm' ##nipype's dcm2nii wrapper needs a filename
#run_template = 'MR-SE%0.3d-eja_ep2d_bold_1mm_1500TR/'+dummyvol

#results_base_dir = '/Data/tmp/CO/'#TN/'
#results_container = '/Data/tmp/CO/mocoresults/'#TN/mocoresults/'
#run_list = []
#for ii in [3,4,5]:
	#run_list.append(basedir+'%s/CO20110630/' % ('CO') + run_template % (ii, ii))

#for ii in [2, 3]:
	#run_list.append(basedir+'%s/CO20110701/' % ('CO') + run_template % (ii, ii))


basedir = '/Data/tmp/'
databasedir = '/Data/7T.cmrr/20110830-ST001-naselaris_QC/'
results_base_dir = '/Data/tmp/QC/'#TN/'
results_container = '/Data/tmp/QC/mocoresults/'#TN/mocoresults/'

run_list = filter(lambda x: x.count('_1500TR'), os.listdir(databasedir))
run_list.sort()
run_list = map(lambda x,y: databasedir+y+'/MR-ST001-'+x[3:8]+'-0001.dcm', run_list, run_list)
ref_run = run_list[0]

##==========create a workflow

##==========gather all the nodes/pipelines
from make_refvol import preProc as mr  ##make a reference volume
from fsl_preproc import preProc as pp  ##the main precprocessing pipeline.

##==========gather inputs for make ref.
##==========(hate that this isn't in the pipeline,but this should only be done once while pipeline may be run many times.)
mr.base_dir = basedir
mr.inputs.mrInputnode.ref_run = ref_run
mr.inputs.mrInputnode.results_base_dir = results_base_dir
mr.inputs.mrInputnode.results_container = results_container
mr.inputs.mrInputnode.data_base_dir = databasedir
mr.inputs.mrInputnode.t_size = 10000;
mr.inputs.mrInputnode.t_min = 1;
mr.run()

##====now grab the ref volume.
ref_run = filter(lambda x: x.endswith('.nii.gz'), os.listdir(results_container+'refvol/'))
ref_run = results_container+'refvol/'+ref_run[0]
print "using %s as the reference volume" %ref_run

pp.base_dir = basedir
pp.inputs.inputnode.run_list = run_list
pp.inputs.inputnode.ref_run = ref_run
pp.inputs.inputnode.results_base_dir = results_base_dir
pp.inputs.inputnode.results_container = results_container
pp.inputs.inputnode.data_base_dir = databasedir
pp.inputs.inputnode.t_size = 10000;
pp.inputs.inputnode.t_min = 1;
pv.inputs.inputnode.padNum = 1
pv.inputs.innputnode.nVols = [170, 170, 170]


###==========see
pp.write_graph(graph2use='exec')

###==========do
#pp.run(plugin='MultiProc', plugin_args={'n_procs' : 4})
pp.run()
	
 