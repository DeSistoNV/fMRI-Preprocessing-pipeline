from fsl_preproc import create_fsl_preproc_workflow
from mriDbObjDefs_pandas import *
import time
import socket
import sys


def pipe_it(subject, vox_res, fnirt, experiment):
    start = time.time()
    main_inputnode = fsl_preproc_inode()  # in mriDbObjDefs
    fnirt_text = "fnirt" if fnirt else "nofnirt"

    CHECK_SOCKET = True

    pipeline_data_params = dict()  # Select only...
    pipeline_data_params['subject'] = [subject]
    pipeline_data_params['experiment'] = [experiment]
    pipeline_data_params['run_list'] = []
    pipeline_data_params['sess_list'] = []
    pipeline_data_params['vox_res'] = []
    pipeline_data_params['run_type'] = []
    pipeline_data_params['crop_this'] = ['med', 'med', 'min']  # Almost never used
    if experiment == 'imagery.rf':
        pipeline_data_params['db'] = '/musc.repo/Data/nickdesisto/Imagery_preproc/Imagery_DB.csv'
    elif experiment == '3T.v.7T':
        pipeline_data_params['db'] = '/musc.repo/Data/nickdesisto/3T.v.7T/Databii/res{}.csv'.format(vox_res)
    elif experiment == 'lotusHill.7T.em9K.1.5iso' or 'lotusHill.7T.em9K.1.5iso_first_try':
        pipeline_data_params['db'] = '/mnt/em9k.csv'
    else:
        sys.exit('invalid experiment passed')

    main_inputnode.panda_fields(
        subj = pipeline_data_params['subject'],
        expID = pipeline_data_params['experiment'],
        runList = pipeline_data_params['run_list'],
        sess_list=pipeline_data_params['sess_list'],
        cropRule = pipeline_data_params['crop_this'],
        db = pipeline_data_params['db'],
        run_type = pipeline_data_params['run_type'],
        TEST = False # if True, we are in test mode ; only pass 3 runs in

        )
    fsl_preproc_params = dict()

    if CHECK_SOCKET:
        host_name = socket.gethostname()
        # basedir is the intermediary dump
        # results_base_dir is where the final aligned data goes from the datasink node
        if host_name == 'san':
            fsl_preproc_params['basedir'] = '/home/nickdesisto/Desktop/nipype_dump'
            base = '/home/nickdesisto/ichi/musc.repo/Data/nickdesisto/Imagery_preproc/testing/no_fnirt/{}_{}'
            fsl_preproc_params['results_base_dir'] = base.format(subject, vox_res, fnirt_text)
        elif host_name == 'Ichi':
            results = '/mnt/initial_em9k_pipe/{}_{}_first_try/'
            fsl_preproc_params['results_base_dir'] = results.format(subject, fnirt_text)
            base = '/mnt/nipype_intermediate_dump/{}/{}_{}_{}'
            fsl_preproc_params['basedir'] = base.format(experiment, subject, vox_res, fnirt_text)
        else:
         results = '/home2/initial_3t7t_pipe/{}_{}_first_try/'
         fsl_preproc_params['results_base_dir'] = results.format(subject, fnirt_text)
         base = '/home2/nipype_intermediate_dump/{}/{}_{}_{}'
    	 fsl_preproc_params['basedir'] = base.format(experiment, subject, vox_res, fnirt_text)
    else: 
        fsl_preproc_params['basedir'] = '/home/nick/nipype_intermediate_dump/'
        fsl_preproc_params['results_base_dir'] = '/home/nick/results/'

    # default_params['ref_vol_runList'] = [0]       #grab only the first run for aligning all the other runs to
    fsl_preproc_params['results_container'] = experiment
    fsl_preproc_params['convert_dicoms'] = False
    fsl_preproc_params['t_size'] = 10000  # just go with it (max possible size).
    fsl_preproc_params['bet_frac'] = 0.3  # BRAIN EXTRACTION TOOL THRESHOLD
    # motion correction
    fsl_preproc_params['ref_run'] = []  # reference volume all others will be referenced
    fsl_preproc_params['moco_only'] = False  # if true, all FLIRT AND FNIRT is ignored
    # linear registration#
    fsl_preproc_params['FLIRT_cost_func'] = ['normcorr']
    fsl_preproc_params['interp_FLIRT'] = 'sinc'  # linear registration stage (sinc, trilinear, nearestneighbour, spline)
    fsl_preproc_params['dof_FLIRT'] = 6  # degrees of freedom (MAX : 12)
    fsl_preproc_params['rigid2D_FLIRT'] = False  # if true, restrict linear reg to rigid body transformations and ignore dof
    # nonlinear registration
    fsl_preproc_params['do_FNIRT'] = True
    fsl_preproc_params['interp_FNIRT'] = 'spline'  # what kind of interpolation (sinc,trilinear,nearestneighbour or spline)
    fsl_preproc_params['FNIRT_subsamp'] = [[4, 2, 1, 1]]  # FNIRT runs a coarse-to-fine algorithm. This is a list specifying the downsampling factor on each iteration.
    fsl_preproc_params['FNIRT_warpres'] = [(5, 5, 5)]  # Resolution of the warping function. Like, how fine is the warping. Can specify different level for each iteration. *Question*: Why is this list shorter than the one above?
    # run settings



    fsl_preproc_params['do_fugue'] = True
    fsl_preproc_params['delta_TE'] = 1.02 # FOR FUGUE
    fsl_preproc_params['dwell_time'] = .00032  # FOR FUGUE
    fsl_preproc_params['mag_frac'] = .5 # BET Fractional Intensity Threshold for the Field Map Magnitude Image
    fsl_preproc_params['unwarp_direction'] = 'z' # FOR FUGUE

    fsl_preproc_params['nProc'] = 6 # number of CPUS


    check_params = False
    if check_params:
        # check to see if parameters have been used yet. If theres a problem code will exit.
        check_params_used(fsl_preproc_params, '/home/nick/datDump/result_params.csv')

    # dump params in input node
    for key in fsl_preproc_params.keys():
        setattr(main_inputnode.inputs, key, fsl_preproc_params[key])
    # => construct the workflow
    pp = create_fsl_preproc_workflow(main_inputnode)
    pp.write_graph()
    # and, for reasons I can't remember, establish the base directory as an attribute of the workflow
    pp.base_dir = fsl_preproc_params['basedir']
    # print inputs after being processed by mriDbObjDefs for sanity check
    print main_inputnode.inputs
    # run the pipeline


    if fsl_preproc_params['nProc'] > 1:
        pp.run(plugin='MultiProc', plugin_args={'n_procs': fsl_preproc_params['nProc']})
    else:
        pp.run()

    # # Appending Working Volume and Brain Mask file paths to a new CSV saved in results_base_dir
    # # add_mask_vols(pp.get_node('inputnode'), fsl_preproc_params, pipeline_data_params['db'])
    # # outputs a text file of parameters used
    # #params_txt(fsl_preproc_params)
    # # option to append a parameters csv to keep track when doing iterative optimization
    # param_csv = False

    # if param_csv:
    #     # Appending the parameters used in this run to a csv to track them
    #     append_param_csv(fsl_preproc_params, '/home/nick/datDump/result_params.csv')

    # last_words = "Pipeline ran in {} hours on {} items"
    # print last_words.format(time.strftime("%H:%M:%S", time.gmtime(time.time() - start)), len(main_inputnode.inputs.abs_run_id))


def main():
    # current experiments : imagery.rf , 3T.v.7T, lotusHill.7T.em9K.1.5iso
    # pipe_it(subject (str), vox_res (str), fnirt (bool), experiment(str) ):
    host_name = socket.gethostname()
    if host_name == 'Ichi':
        #      (Subject, VoxelRes, FNIRT?, expID)
       # pipe_it('CO', '1.5', False, 'lotusHill.7T.em9K.1.5iso')
       # pipe_it('DM', '1.5', True, 'lotusHill.7T.em9K.1.5iso')
       # pipe_it('MY', '1.5', False, 'lotusHill.7T.em9K.1.5iso')
       # pipe_it('PHIL', '1.5', True, 'lotusHill.7T.em9K.1.5iso')
       #pipe_it('TN', '1.5', False, 'lotusHill.7T.em9K.1.5iso')
       pipe_it('TN','1.6',True,'imagery.rf')
       #pipe_it('s1000','3',False, '3T.v.7T')
       

    if host_name == 'san':
        pass

    #pipe_it('s1000','3',False, '3T.v.7T')



main()
