import nipype.pipeline.engine as pe          # pypeline engine

##===========directories / parameter
basedir = '/auto/k5/thomas/Data/bullshit/'
databasedir = 'basedir'
subjects = ['TN', 'CO']
dummyvol = 'MR-ST001-SE010-0001.dcm' ##nipype's dcm2nii wrapper needs a filename
run_template = 'MR-SE%0.3d-eja_ep2d_bold_1mm_1500TR/'+dummyvol
ref_run = 3
results_base_dir = basedir
results_container = '/results/'



##===========helper functions

##give all the sessions associated with a subject
def sessioninfo(subject_id):
	tbl = dict(CO = ['CO20110630', 'CO20110701'], 
		   	   TN = ['TN20110904', 'TN20111007'])
	return tbl[subject_id]

##give all the volume numbers for the runs
def runlist(session_id): 
	tbl = dict(CO20110630=[3,4,5],
			   CO20110701 = [2, 3],
			   TN20110904 = [2, 3],
			   TN20111007 = [11, 12, 13])
	return tbl[session_id]

##==========create a workflow
wf = pe.Workflow(name='workflow')
wf.base_dir = basedir

##==========gather all the nodes/pipelines
from fsl_preproc import preProc as pp
from metanodes import meta_engine as meta

##==========inform the metanode engine
meta.base_dir = basedir
subjs = meta.get_node('subjectnode')
subjs.iterables = ('subject_id', subjects)
sess = meta.get_node('sessionnode')
sess.iterables = ('session_id', ('subject_id', sessioninfo))

##==========inform the pipeline engine 
pp.base_dir = basedir
pp.inputs.inputnode.ref_run = ref_run
pp.inputs.inputnode.run_templ = run_template
pp.inputs.inputnode.results_base_dir = results_base_dir
pp.inputs.inputnode.results_container = results_container
##<<this is the current problem...should there an iterable for runlist?
pp.inputs.inputnode.data_base_dir = databasedir


##==========connect session metanode to pipline input node

wf.connect([
		    (meta, pp, [('sessionnode.session_id', 'inputnode.session_id'),
		    		   (('sessionnode.session_id', runlist), 'inputnode.run_list')]
		    )		    		   
		  ])

##==========see
wf.write_graph(graph2use='exec')

##==========do
wf.run()

	
 