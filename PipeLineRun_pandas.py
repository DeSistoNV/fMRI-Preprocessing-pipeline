from fsl_preproc import create_fsl_preproc_workflow
from mriDbObjDefs_pandas import fsl_preproc_inode
from mriDbObjDefs_pandas import append_param_csv
from mriDbObjDefs_pandas import collect_results
from mriDbObjDefs_pandas import append_pandas
from mriDbObjDefs_pandas import check_params_used
import os


def pipe_it(subject,res,fnirt):
        main_inputnode = fsl_preproc_inode() ## in MriDbObjs ; nipype superclass
        fnirt_text = "fnirt" if fnirt else "nofnirt"    
        
        pipeline_data_params = dict() # Select only...
        pipeline_data_params['subject'] = subject
        pipeline_data_params['experiment'] = '3T.v.7T'
        pipeline_data_params['run_list'] = []
        pipeline_data_params['sess_list'] = []
        pipeline_data_params['crop_this'] = ['med', 'med', 'min']  ##note that this will almost never be needed, and isn't need in this example
#        pipeline_data_params['db'] = '/media/nick/10259e32-b12f-4a45-a7aa-c73d797b1566/3Tv7T/Databii/res{}.csv'.format(res)
        pipeline_data_params['db'] = '/media/nick/10259e32-b12f-4a45-a7aa-c73d797b1566/3Tv7T/Databii/res1.csv'


        ## putting above selections into input node
        main_inputnode.panda_fields(
                       subj=pipeline_data_params['subject'],
                           expID=pipeline_data_params['experiment'],                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        			       runList = pipeline_data_params['run_list'],
                           sessList = pipeline_data_params['sess_list'],
                           cropRule = pipeline_data_params['crop_this'],
                       db = pipeline_data_params['db'])	  	##we want all runs here.

        fsl_preproc_params = dict() # THESE ARE THE RUN PARAMS THAT CHANGE WHAT PIPELINE DOES
        fsl_preproc_params['basedir'] = '/media/nick/10259e32-b12f-4a45-a7aa-c73d797b1566/nipype_intermediate_dump' # intermediate pipeline dump


        # save the results with current time in file name
        # fsl_preproc_params['results_base_dir'] = '/home/nick/datDump/results-{}'.format(datetime.now().strftime('%b-%d-%Y-%H:%M'))


#        fsl_preproc_params['results_base_dir'] = '/media/nick/10259e32-b12f-4a45-a7aa-c73d797b1566/3Tv7T/pipelined/{}/res{}/{}'.format(subject,res,fnirt_text)
        fsl_preproc_params['results_base_dir'] = '/media/nick/10259e32-b12f-4a45-a7aa-c73d797b1566/3Tv7T/pipelined'
        fsl_preproc_params['results_container'] = 'Imagery_RF_test' #output dump specific
        fsl_preproc_params['convert_dicoms'] = False
        #default_params['ref_vol_runList'] = [0]		#grab only the first run for aligning all the other runs to
        fsl_preproc_params['t_size'] = 10000 # just go with it (max possible size).
        fsl_preproc_params['nProc'] = 8 # number of CPUS
        fsl_preproc_params['bet_frac'] = .3 # BRAIN EXTRACTION TOOL THRESHOLD

        ##motion correction
        fsl_preproc_params['ref_run'] = [] # reference volume all others will be referenced
        fsl_preproc_params['moco_only'] = False # if true, all FLIRT AND FNIRT is ignored

        ##linear registration#
        fsl_preproc_params['FLIRT_cost_func'] = ['normcorr']
        fsl_preproc_params['interp_FLIRT'] = 'sinc' # linear registration stage (sinc,trilinear,nearestneighbour or spline)
        fsl_preproc_params['dof_FLIRT'] = 12 # degrees of freedom (MAX : 12)
        fsl_preproc_params['rigid2D_FLIRT'] = False # if true, restrict linear reg to rigid body transformations and ignore dof

        ##nonlinear registration
#        fsl_preproc_params['do_FNIRT'] = fnirt
        fsl_preproc_params['do_FNIRT'] = False
        fsl_preproc_params['searchr_x'] = [] # params for linear reg exposed (select the angular range over which the initial optimisation search stage is performed.)
        fsl_preproc_params['searchr_y'] = [] # find out what these guys do
        fsl_preproc_params['searchr_z'] = []
        fsl_preproc_params['interp_FNIRT'] = 'spline' # what kind of interpolation (sinc,trilinear,nearestneighbour or spline)
        fsl_preproc_params['FNIRT_subsamp'] = [[4,2,1,1]] #FNIRT runs a coarse-to-fine algorithm. This is a list specifying the downsampling factor on each iteration.
        fsl_preproc_params['FNIRT_warpres'] = [(5,5,5)] # Resolution of the warping function. Like, how fine is the warping. Can specify different level for each iteration. *Question*: Why is this list shorter than the one above?


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
        if fsl_preproc_params['nProc'] > 1:
           pp.run(plugin='MultiProc', plugin_args={'n_procs' : fsl_preproc_params['nProc']})
        else:
           pp.run()


        append = False
        param_csv = False
        collect_movies = False


        if append:
            #Appending Working Volume and Brain Mask file paths to the pandas DataFrame (repickles and saves it to the same location)
            append_pandas(pp.get_node('inputnode'),fsl_preproc_params,pipeline_data_params['db'])

        if param_csv:
            # Appending the parameters used in this run to a csv to track them
            append_param_csv(fsl_preproc_params,'/home/nick/datDump/result_params.csv')

        if collect_movies:
            # collects all corrected movie files and copies them into one folder.
            collect_results()

        
def main():

            pipe_it('s1000','1',False)        
#            pipe_it('s1000','1',True)
#            pipe_it('s1000','3',False)        
#            pipe_it('s1000','3',True)
#            pipe_it('s1000','2.4',False)        
#            pipe_it('s1000','2.4',True)
#
#
#            pipe_it('s1032','1',False)
#            pipe_it('s1032','1',True)
#            pipe_it('s1032','2.4',False)
#            pipe_it('s1032','2.4',True)
#            pipe_it('s1032','3',True)
#            pipe_it('s1032','3',False)



main()
    





