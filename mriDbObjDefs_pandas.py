# #this creates a modified "inputnode" for the fsl_preproc pipeline. It inherits a specific nipype class and creates the
# # appropriate input fields.
from nipype.interfaces.utility import IdentityInterface
import os
import sys
import pandas as pd

class fsl_preproc_inode(IdentityInterface):
    # this __init__ definition uses a trick from stack overflow to initialize a super class
    # creates the input node fields needed to start an fsl_preproc pipeline
    # provides connection and cursor for mri db
    def __init__(self):
        super(fsl_preproc_inode, self).__init__(fields=[
            't_min',  # [], 1 = remove the reference scan, 0 = don't need to bother
            't_size',  # always set larger than the number of vols in the longest run
            'ref_run',  # this is going to be the reference volume for motion correction.
            'padNum',  # = the largest number of padding vols. required for any run in the run_list
            'nVols',  # [], the total number of volumes that you need to end up with for each run.
            'run_list',  # [], list of runs to pre-process
            'results_base_dir',  # directory for where results go
            'results_container',
            'do_FNIRT',
            'spatial_crop',
            'abs_run_id',
            'moco_only',
            'interp_FNIRT',
            'interp_FLIRT',
            'dof_FLIRT',
            'rigid2D_FLIRT'
            'convert_dicoms',
            'mags',  # Field map magnitude images
            'phase', # Field map phase images
            'delta_TE',
            'mag_frac',
            'dwell_time',
            'unwarp_direction',
            'do_fugue'
            ])
        self.DF = 'PlaceHolder for Pandas DataFrame'

    # method to display options
    def check_options(self, kwargs):
        if 'subj' not in kwargs:  # if subject not passed, lists subjects in df and exits
                print 'Available Subjects are:'
                for sub in set(self.Df.subject):
                    print sub
                sys.exit('Execution Stopped, please choose a Subject')

        elif 'expID' not in kwargs:  # if expID not passed, lists expIDs in df and exits
            print 'Available expIDs are:'
            for exp in set(self.Df.experiment):
                print exp
            sys.exit('Execution Stopped, please choose an expID')




    def open_db(self,kwargs):
        if 'db' not in kwargs: # if no db passed, exit.
                sys.exit("Exception in panda_fields: need a ['db'] arg\nExecution Stopped")
        if not os.path.isfile(kwargs['db']): # if db does not exist, exit.
                sys.exit('Exception in panda_fields: db file: ' + kwargs['db'] + ' not found\nExecution Stopped')
        # if DB is a pickled pandas dataFrame
        if kwargs['db'][-2:] == '.p' or kwargs['db'][-3:] == 'csv':
            if kwargs['db'][-2:] == '.p':
                # unpickling and loading DataFrame
                Df = pd.read_pickle(kwargs['db'])
            else:
                Df = pd.read_csv(kwargs['db'],index_col = False)
        else:
            sys.exit('Need a pickled pandas DataFrame  or CSV as db arg')
        self.DF = Df
    def panda_fields(self, **kwargs):

        """
        populate_fields(subj, expID, runType, sess_list, runList)
        subj ~ a single string to identify one subject
        expID ~ a single string to identify the experiment
        runType ~ a tuple of strings specifying the type of run 'img', 'val', 'trn', etc.
        sess_list ~ a list of integers specifying which sessions you want from this subject/experiment (in chronological
        order)
        runList ~ a list of numbers specifying which runs you want (in chronological order)
        returns a list of run volume names given the specified subject, experiment, and sessions, runType and runList
        if subj or expID not specified, will print all distinct possibilities.
        if sess_list, runType or runList not specified, will assume all distinct possibilities.
        note runList is not a field in the mri db. it is an index into the list of runs associated with a query. we
        assume entered in chronological order.
        """
        
        ## opening database
        self.open_db(kwargs)
        ## checks subject and expID 
        self.check_options(kwargs)
        
        # if runtype or sess_list aren't passed,
        if not kwargs['run_type']:
            kwargs['run_type'] = self.DF.run_type.unique()
        if not kwargs['sess_list']:
            kwargs['sess_list'] = self.DF.sessionID.unique()
        
        working_DF = self.DF.copy()[self.DF.subject.isin(kwargs['subj']) & self.DF.sessionID.isin(kwargs['sess_list']) & self.DF.run_type.isin(kwargs['run_type']) & self.DF.experiment.isin(kwargs['expID']) ]
        if kwargs['TEST']:
            working_DF = working_DF[:3]
        self.inputs.abs_run_id = list(working_DF.runID)
        self.inputs.nVols = list(working_DF.nvols)
        self.inputs.t_min  = list(working_DF.siemensRef)
        self.inputs.padNum = max(list(self.DF.padVol))

        path_tuples = zip(working_DF.run_path,working_DF.run_data_file)
        paths = map(lambda x,:os.path.join(*x),path_tuples)
        self.inputs.run_list = [os.path.join(path, filter(lambda x : '.nii' in x,os.listdir(path)).pop()) for path in paths]

        self.inputs.mags = list(working_DF.mag)
        self.inputs.phase = list(working_DF.phase)

        # finally, deal with spatial cropping issues if any of the volumes don't have the same size
        # grab the dimensions for each of the runs
        dims = zip(*[(row.matrix_x,row.matrix_y,row.n_slices) for _,row in working_DF.iterrows()])

#       pipeline_data_params['crop_this'] = ['med', 'med', 'min']  ##note that this will almost never be needed, and isn't need in this example
        mn = map(min, dims)
        self.inputs.spatial_crop = {}

        keys = [('x_min', 'x_size'), ('y_min', 'y_size'),('z_min', 'z_size')]  # these keys refer to input args. in fslroi. kinda hacky.
        for index, item in enumerate(kwargs['cropRule']):
            if item == 'min':  # from left to right
                self.inputs.spatial_crop[keys[index][0]] = [0] * len(dims[index])
                self.inputs.spatial_crop[keys[index][1]] = [mn[index] for ff in dims[index]]
            elif item == 'max':  # from right to left
                self.inputs.spatial_crop[keys[index][0]] = [ff - mn[index] for ff in dims[index]]
                self.inputs.spatial_crop[keys[index][1]] = [mn[index] for ff in dims[index]]
            elif item == 'med':  # from the center out
                self.inputs.spatial_crop[keys[index][0]] = [(ff - mn[index]) / 2 for ff in dims[index]]
                self.inputs.spatial_crop[keys[index][1]] = [mn[index] for ff in dims[index]]


# Added 1.13.15
# Method to add working volume and brain mask file paths
# Precondition : pipeline has been run
# Param results_base_directory : base directory where pipeline stores results
# Param inputs : main_inputnode.inputs ; this is to get the run list
# Param db : location of pickled pandas DataFrame file
def add_mask_vols(inputnode, params_dict, db):
#    try:
#
#        if not os.path.isdir(inputnode.inputs.basedir):  # check if the results_base_directory exists
#            raise IOError()

        self.DF = pd.read_csv(db,index_col=False)  # opening the csv file

        # building top path for files
        container = params_dict['results_container']
        container = container if container[0] == '/' else '/' + container
        results = params_dict['results_base_dir'] + container
        
        # building path for brain_mask
        brain_mask = results + '/brain_mask'
        while os.path.isdir(brain_mask):
            brain_mask += '/' + os.listdir(brain_mask)[0]

        # adding brain mask for all the runs in the run list
        for run in inputnode.inputs.abs_run_id:
            self.DF.ix[self.DF.runID == run, 'brain_mask'] = brain_mask

        # building working volume paths
        working_vols = results + '/final_aligned'
        while '_work' not in os.listdir(working_vols).pop():
            working_vols += '/' + os.listdir(working_vols).pop()
        vol_dirs = [working_vols + '/' + vol for vol in os.listdir(working_vols) if vol[-3:] == '.gz']
        vol_dirs = [vol + '/' + os.listdir(vol)[0] for vol in vol_dirs]

        # adding working volumes to their respective runs
   
        for vol in vol_dirs:
            self.DF.ix[self.DF.runID == int(vol[-10:-7]) , 'working_vol'] = vol

        self.DF.to_csv(params_dict['results_base_dir'] + '/db.csv', index=False, float_format='%.3f')  # re-exporting to a csv of the same name.
#
#
#    except IOError:
#        print "\nERROR ADDING BRAIN MASK AND WORKING VOLUME: CAN'T APPEND A NON-EXISTING FILE \n\t run pipeline first."


# Added 1.16.15
# Method to update csv file that keeps tracks of params used for various pipeline runs
# param fsl : fsl_preproc_params dictionary
# param csv : .csv file of the parameters db
def append_param_csv(fsl, csv):
    try:
        if not os.path.isfile(csv):  # checking if csv file exists
            raise IOError

        df = pd.read_csv(csv, index_col=False)  # reading the csv into a pandas DataFrame

        # appending new parameters to the next empty row of DataFrame
        df.loc[len(df) + 1] = [fsl['results_base_dir'].split('/')[-1], fsl['t_size'], fsl['bet_frac'],
                               str(fsl['FLIRT_cost_func'])[2:len(fsl['FLIRT_cost_func']) - 3],
                               fsl['interp_FLIRT'], fsl['dof_FLIRT'], str(fsl['rigid2D_FLIRT']), fsl['interp_FNIRT'],
                               fsl['FNIRT_subsamp'], fsl['FNIRT_warpres']]

        df.to_csv(csv, index=False, float_format='%.3f')  # re-exporting to a csv of the same name.

        print df.tail(3)  # printing last 3 lines of DF

        print 'results csv updated'
    except IOError:
        print csv + 'does not exist.'


# Added 1.23.15
# Method to check if params have been used against csv file as well as checking if the base_dir is used
# param fsl : fsl_preproc_params dictionary
# param csv: csv file of the parameters db
def check_params_used(fsl, csv):
    try:
        if not os.path.isfile(csv):
            raise IOError
        if os.path.isdir(fsl['results_base_dir']):
            sys.exit('Execution Stopped: ' + fsl['results_base_dir'] + ' already exists.')

        df = pd.read_csv(csv, index_col=False)
        keys = [df.columns[i] for i in range(len(df.columns))]
        vals = [fsl['results_base_dir'].split('/')[-1], fsl['t_size'], fsl['bet_frac'],
                str(fsl['FLIRT_cost_func'])[2:len(fsl['FLIRT_cost_func']) - 3],
                fsl['interp_FLIRT'], fsl['dof_FLIRT'], fsl['rigid2D_FLIRT'], fsl['interp_FNIRT'],
                # forcing this value to look the same as the loaded csv
                str([str(i) for i in fsl['FNIRT_subsamp']]).replace("'", ''),
                str([str(i) for i in fsl['FNIRT_warpres']]).replace("'", '')]
        test = dict(zip(keys, vals))

        counts = []
        for i in df.index:
            test_row = df.loc[i].to_dict()
            test_row['bet_frac'] = round(test_row['bet_frac'], 2)
            diff = set(test_row.items()) ^ set(test.items())
            counts.append(len(diff))
        if 0 in counts:
            sys.exit('Execution Stopped: Parameters already used.')
        else:
            print 'parameters have not been tested yet'

    except IOError:
        sys.exit('Execution Stopped: ' + csv + ' does not exist.')


def params_txt(params):
        f = open(params['results_base_dir'] + '/parameters.txt', 'w')
        for key in params:
            f.write(" {} : {} \n".format(key, params[key]))

