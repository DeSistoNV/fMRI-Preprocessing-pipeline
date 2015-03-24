from palmetto.palmetto_pbs import pbs_job
from os import system
##============root directory
root_dir = '/Data/tmp/'

##===========general pbs options  
n_nodes = 1   						#nNodes ~ integer. number of nodes requested. will usually be 1.
n_cpus = 8    						#nCpus ~ number of cores per node. NOTE: set to 1 to run in serial mode.
mem_gb = 16    						#memGb ~ iteger. memory request in Gb.
wall_time = [11, 0, 0]    				#wallTime ~ [HRS, MINS, SECS] ~ [INT, INT, INT]
							#scriptName ~ string. full path to your script
run_script = '/home/tnaselar/code/Python/nipype_mri/scripts/fsl_preproc_go.py'    
repo = '/Data/tmp/pbs.reports/'        			#repo ~ a path to a place where the script argument data, the .sh script, and stdout and stderr go
user = 'tnaselaris'

##===========general fsl_preproc options that won't change across subjects
default_params = {}
default_params['db'] = '/Data/7T.cmrr/databases/mri.ichi.db'		 		##get subject and run information from this database
default_params['ref_vol_runList'] = [0]							##grab only the first run for aligning all the other runs to
default_params['TOOBIG'] = 10000;							##HACK. need it for extracting the initial siemens ref vol.
default_params['crop_this'] = ['med', 'med', 'min']					##if one of the runs has volumes bigger than the ref run, this says how to truncate the too-big volumes
default_params['nProc'] = n_cpus							##should always makes sure that nipype and palmetto are dealing with the same number of cores
default_params['bet_frac'] = 0.1
default_params['ref_run'] = [] 


##===========dumb function for creating directories from a subject name
def make_subj_dir(root_dir, version, subj):
    dir_dict = {}
    dir_dict['basedir'] = root_dir+subject+version+'/'  		         ##this is where nipype's default output for each node goes. check here if the pipeline crashes 
    dir_dict['results_base_dir'] = dir_dict['basedir']			         ##directory for the datasinks
    dir_dict['results_container'] = dir_dict['results_base_dir']+'mocoresults/'  ##sub-directory for the main pipeline datasink
    dir_dict['subject'] = subj	
    return dir_dict

##==========subject MY: the arguments required by run_script to do work
subject = 'KH'
experiment = 'lotusHill.7T.em6K.hires'
fsl_preproc_params = {}
fsl_preproc_params.update(make_subj_dir(root_dir, experiment, subject))
fsl_preproc_params.update(default_params)						
fsl_preproc_params['experiment'] = experiment
fsl_preproc_params['sess_list'] = []							##NOTE: Leave empty to use ALL available sessions
fsl_preproc_params['run_list'] = []						        ##NOTE: Leave empty to use ALL available runs
fsl_preproc_params['do_FNIRT'] = True
fsl_preproc_params['FNIRT_subsamp'] = [[4,2,1,1]]   					##[[8, 4, 2, 2], [4, 4, 2, 2], [4, 2, 1, 1]]
fsl_preproc_params['FNIRT_warpres'] = [(5,5,5)]   					##[(5,5,5), (15,15,15), (10,10,10)]  
fsl_preproc_params['FLIRT_cost_func'] = ['normcorr']					#['normcorr']#['mutualinfo', 'corratio', 'normcorr', 'normmi', 'leastsq']  
fsl_preproc_params['moco_only'] = False
fsl_preproc_params['searchr_x'] = []							#[-180, 180], [-75, 75], 
fsl_preproc_params['searchr_y'] = []
fsl_preproc_params['searchr_z'] = []
fsl_preproc_params['interp_FNIRT'] = 'spline'
fsl_preproc_params['interp_FLIRT'] = 'nearestneighbour'
fsl_preproc_params['dof_FLIRT'] = 12
fsl_preproc_params['rigid2D_FLIRT'] = False
job_name = '%s_%s' %(subject, experiment)							#jobName ~ string (must be 7 characters long)
job_name = job_name[0:3]+job_name[-4:]								##this little bit of retardation is because jobnames must be 7 chars long.

run_it = pbs_job(job_name, n_nodes, n_cpus, mem_gb, wall_time, user, run_script, fsl_preproc_params, repo)
run_it.make_script()
run_it.local()
#run_it.submit()
