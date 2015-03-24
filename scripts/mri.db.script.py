##==========gather all the nodes/pipelines
import nipype.pipeline.engine as pe          		# pypeline engine
import os
from mriDatabase.mriDbObjDefs import fsl_preproc_inode	#a special IdentityInterface node with dedicated fields
from fsl_preproc import create_fsl_preproc_workflow
##===========directories / parameter
subject = 'MY'							##mri.DB subject field
experiment = 'lotusHill.7T.em9K.1.5iso'
basedir = '/Data/tmp/'+subject+'_1x1.flirt.cost.func/'  				##this is where nipype's default output for each node goes. check here if the pipeline crashes 
results_base_dir = basedir					##directory for the datasinks
ref_results_container = results_base_dir+'refvol'		##sub-directory for the reference pipeline datasink
results_container = results_base_dir+'mocoresults/'#TN/moc      ##sub-directory for the main pipeline datasink
ref_vol_ref_run = []						##tells the ref vol pipline to align to middle volume of reference run
sess_list = [0]
db = '/Data/tmp/mri.complete.db'				##get files for this database
ref_vol_runList = [0]						##grab only the first run for aligning all the other runs to
TOOBIG = 10000;							##a hack. need it for extracting the initial siemens ref vol.
do_FNIRT = False
cropThis = ['med', 'med', 'min']

##==========make a reference volume by cloning the pp workflow and leaving the ref_run field blank. this will
##==========cause pp to align the volumes in the ref_run to the middle volume.
##==========(hate that this isn't in the pipeline,but this should only be done once while pipeline may be run many times.)
#ref_inputnode = fsl_preproc_inode()								##get a modified IdentityInterface that can read from a sqlite database.
#ref_inputnode.open_db(db)									##open the database
#ref_inputnode.populate_fields(subj=subject, expID=experiment, runList=ref_vol_runList)		##populate the fields of the inputnode
#ref_inputnode.close_db()									##close the database.
#ref_inputnode.inputs.results_base_dir = results_base_dir		
#ref_inputnode.inputs.results_container = ref_results_container
#ref_inputnode.inputs.t_size = TOOBIG								
#ref_inputnode.inputs.ref_run = ref_vol_ref_run #'/Data/tmp/testFlirt/20110825_084833ejaep2dbold1mm1500TRs017a001_roi_brain_mcf_mean.nii.gz' #
#ref_inputnode.inputs.do_FNIRT = False
#mr = create_fsl_preproc_workflow(ref_inputnode)
#mr.base_dir = basedir

##mr.run(plugin='MultiProc', plugin_args={'n_procs' : 4})
#mr.run()

###====now grab the ref volume.
#ref_run = filter(lambda x: x.endswith('.nii.gz'), os.listdir(ref_results_container+'/corrected_movie/'))
#ref_run = ref_results_container+'/corrected_movie/'+ref_run[0]
#print "using %s as the reference volume" %ref_run


###===prepare the main pipeline
main_inputnode = fsl_preproc_inode()
main_inputnode.open_db(db)
main_inputnode.populate_fields(subj=subject, expID=experiment, cropRule = cropThis)	  	##we want all runs here.
main_inputnode.close_db()
main_inputnode.inputs.results_base_dir = results_base_dir
main_inputnode.inputs.results_container = results_container
main_inputnode.inputs.t_size = TOOBIG
main_inputnode.inputs.ref_run = []#ref_run
main_inputnode.inputs.do_FNIRT = do_FNIRT
#main_inputnode.iterables = ('do_FNIRT', ['False', 'True'])


pp = create_fsl_preproc_workflow(main_inputnode)
pp.base_dir = basedir

#==========see
#pp.write_graph(graph2use='exec')

##==========do
pp.run(plugin='MultiProc', plugin_args={'n_procs' : 8})
#pp.run()
	
 