##==========gather all the nodes/pipelines
import nipype.pipeline.engine as pe          		# pypeline engine
from mriDatabase.mriDbObjDefs import fsl_preproc_inode	#a special IdentityInterface node with dedicated fields: linked to a sqlite db to populate fields
from nipype_mri.fsl_preproc import create_fsl_preproc_workflow     #function for creating the standard fsl alignment preprocessing pipeline.
import pickle
import sys

from nipype import config
config.enable_debug_mode()

##====load in the directories
fsl_preproc_params_npz = sys.argv[1]
print "========these are your running args: %s" %fsl_preproc_params_npz
fsl_preproc_params = pickle.load(open(fsl_preproc_params_npz, 'rb'))

###===prepare the main pipeline
main_inputnode = fsl_preproc_inode()
main_inputnode.open_db(fsl_preproc_params['db'])
main_inputnode.populate_fields(subj=fsl_preproc_params['subject'],
			       expID=fsl_preproc_params['experiment'],
			       runList = fsl_preproc_params['run_list'],
			       sessList = fsl_preproc_params['sess_list'],
			       cropRule = fsl_preproc_params['crop_this'])	  	##we want all runs here.
main_inputnode.close_db()
main_inputnode.inputs.results_base_dir = fsl_preproc_params['results_base_dir']
main_inputnode.inputs.results_container = fsl_preproc_params['results_container']
main_inputnode.inputs.t_size = fsl_preproc_params['TOOBIG']
main_inputnode.inputs.ref_run = fsl_preproc_params['ref_run']#ref_run
main_inputnode.inputs.do_FNIRT = fsl_preproc_params['do_FNIRT']
main_inputnode.inputs.FNIRT_subsamp = fsl_preproc_params['FNIRT_subsamp']
main_inputnode.inputs.FNIRT_warpres = fsl_preproc_params['FNIRT_warpres']
main_inputnode.inputs.FLIRT_cost_func = fsl_preproc_params['FLIRT_cost_func']
main_inputnode.inputs.bet_frac = fsl_preproc_params['bet_frac']
main_inputnode.inputs.moco_only = fsl_preproc_params['moco_only']
main_inputnode.inputs.searchr_x = fsl_preproc_params['searchr_x']
main_inputnode.inputs.searchr_y = fsl_preproc_params['searchr_y']
main_inputnode.inputs.searchr_z = fsl_preproc_params['searchr_z']
main_inputnode.inputs.interp_FNIRT = fsl_preproc_params['interp_FNIRT']
main_inputnode.inputs.interp_FLIRT = fsl_preproc_params['interp_FLIRT']
main_inputnode.inputs.dof_FLIRT = fsl_preproc_params['dof_FLIRT']
main_inputnode.inputs.rigid2D_FLIRT = fsl_preproc_params['rigid2D_FLIRT']
main_inputnode.inputs.convert_dicoms = fsl_preproc_params['convert_dicoms']

##====construct the workflow
pp = create_fsl_preproc_workflow(main_inputnode)
pp.base_dir = fsl_preproc_params['basedir']

##==========do
if fsl_preproc_params['nProc'] > 1:
  pp.run(plugin='MultiProc', plugin_args={'n_procs' : fsl_preproc_params['nProc']})
else:
  pp.run()
	
 