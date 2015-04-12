from fsl_preproc_orig import create_fsl_preproc_workflow
from mriDbObjDefs_pandas import fsl_preproc_inode
from mriDbObjDefs_pandas import append_param_csv
from mriDbObjDefs_pandas import collect_results
from mriDbObjDefs_pandas import add_mask_vols
from mriDbObjDefs_pandas import check_params_used
from mriDbObjDefs_pandas import params_txt
import os
from datetime import datetime
import time
import netifaces as ni
import sys

class DidItAlreadyError(Exception):
    pass


def pipe_it(subject,res,fnirt):
        start = time.time()
        main_inputnode = fsl_preproc_inode() ## in MriDbObjs ; nipype superclass
        fnirt_text = "fnirt" if fnirt else "nofnirt"    
        
        doit = False
        pipeline_data_params = dict() # Select only...
        pipeline_data_params['subject'] = subject
        pipeline_data_params['experiment'] = 'imagery.rf'
        pipeline_data_params['run_list'] = []                      
        pipeline_data_params['sess_list'] = []
        pipeline_data_params['vox_res'] = []
        pipeline_data_params['crop_this'] = ['med', 'med', 'min']  ##note that this will almost never be needed, and isn't need in this example
        pipeline_data_params['db'] = '/musc.repo/Data/nickdesisto/Imagery_DB-updated.csv'


        ## putting above selections into input node
        main_inputnode.panda_fields(
                       subj=pipeline_data_params['subject'],
                           expID=pipeline_data_params['experiment'], 
                            runList = pipeline_data_params['run_list'],
                           sessList = pipeline_data_params['sess_list'],
                           cropRule = pipeline_data_params['crop_this'],
                       db = pipeline_data_params['db'],
                       vox_res = pipeline_data_params['vox_res']
                    
        )	  	##we want all runs here.

        fsl_preproc_params = dict() # THESE ARE THE RUN PARAMS THAT CHANGE WHAT PIPELINE DOES




#        # save the results with current time in file name
#        fsl_preproc_params['results_base_dir'] = '/home/nick/datDump/results-{}'.format(datetime.now().strftime('%b-%d-%Y-%H:%M'))



        san = '128.23.157.102'
        ichi = '128.23.157.70'
        this_ip = ni.ifaddresses('eth0')[2][0]['addr']
        if  this_ip == san:
            fsl_preproc_params['basedir'] = '/home/nickdesisto/Desktop/nipype_dump'
            fsl_preproc_params['results_base_dir'] = '/home/nickdesisto/Desktop/Nipype_Results....'
        elif this_ip == ichi:
            fsl_preproc_params['results_base_dir'] = '/musc.repo/Data/nickdesisto/Imagery_preproc/All_TN_runs'.format(subject,res,fnirt_text)
            fsl_preproc_params['basedir'] = '/mnt/nipype_intermediate_dump' # intermediate pipeline dump
        else:
            sys.exit('what computer are you on?')

        fsl_preproc_params['results_container'] = 'Imagery_RF_test' #output dump specific
        fsl_preproc_params['convert_dicoms'] = False
        #default_params['ref_vol_runList'] = [0]		#grab only the first run for aligning all the other runs to
        fsl_preproc_params['t_size'] = 10000 # just go with it (max possible size).
        fsl_preproc_params['nProc'] = 8 # number of CPUS
        fsl_preproc_params['bet_frac'] = 0.3 # BRAIN EXTRACTION TOOL THRESHOLD

        ##motion correction
        fsl_preproc_params['ref_run'] = [] # reference volume all others will be referenced
        fsl_preproc_params['moco_only'] = False # if true, all FLIRT AND FNIRT is ignored

        ##linear registration#
        fsl_preproc_params['FLIRT_cost_func'] = ['normcorr']
        fsl_preproc_params['interp_FLIRT'] = 'sinc' # linear registration stage (sinc,trilinear,nearestneighbour or spline)
        fsl_preproc_params['dof_FLIRT'] = 12 # degrees of freedom (MAX : 12)
        fsl_preproc_params['rigid2D_FLIRT'] = False # if true, restrict linear reg to rigid body transformations and ignore dof

        ##nonlinear registration
        fsl_preproc_params['do_FNIRT'] = fnirt
        fsl_preproc_params['searchr_x'] = [] # params for linear reg exposed (select the angular range over which the initial optimisation search stage is performed.)
        fsl_preproc_params['searchr_y'] = [] # find out what these guys do
        fsl_preproc_params['searchr_z'] = []
        fsl_preproc_params['interp_FNIRT'] = 'spline' # what kind of interpolation (sinc,trilinear,nearestneighbour or spline)
        fsl_preproc_params['FNIRT_subsamp'] = [[4,2,1,1]] #FNIRT runs a coarse-to-fine algorithm. This is a list specifying the downsampling factor on each iteration.
        fsl_preproc_params['FNIRT_warpres'] = [(5,5,5)] # Resolution of the warping function. Like, how fine is the warping. Can specify different level for each iteration. *Question*: Why is this list shorter than the one above?
# Answer : because the tuple represents (x,y,z) 

        fsl_preproc_params['afni_moco'] = False

        check_params = False
        if check_params:
            # check to see if parameters have been used yet. If theres a problem code will exit.
            check_params_used(fsl_preproc_params,'/home/nick/datDump/result_params.csv')



        # dump params in input node
        for key in fsl_preproc_params.keys():
            setattr(main_inputnode.inputs, key, fsl_preproc_params[key])

        ##====construct the workflow
        pp = create_fsl_preproc_workflow(main_inputnode)

        ##and, for reasons I can't remember, establish the base directory as an attribute of the workflow
        pp.base_dir = fsl_preproc_params['basedir']

        print main_inputnode.inputs
        

     #   if fsl_preproc_params['nProc'] > 1:
      #         pp.run(plugin='MultiProc', plugin_args={'n_procs' : fsl_preproc_params['nProc']})
       # else:
        #       pp.run()
        #Appending Working Volume and Brain Mask file paths to a new CSV saved in results_base_dir
    
        add_mask_vols(pp.get_node('inputnode'),fsl_preproc_params,pipeline_data_params['db'])
    
#        params_txt(fsl_preproc_params)
        
        param_csv = False
        collect_movies = False
        
        if param_csv:
            # Appending the parameters used in this run to a csv to track them
            append_param_csv(fsl_preproc_params,'/home/nick/datDump/result_params.csv')

        if collect_movies:
            # collects all corrected movie files and copies them into one folder.
            collect_results()

        end = time.time()
        t = end - start
        
        print "Pipeline ran in {} hours on {} items".format(time.strftime("%H:%M:%S", time.gmtime(t)),len(main_inputnode.inputs.abs_run_id))

def main():
    
#    for subject in ('s1000','s1032'):
#        for res in ('3','1','2.4'):
#            for fnirt in (False,True):
#                pipe_it(subject,res,fnirt)
#                
    pipe_it('TN','1.6',True)

                
 



main()
