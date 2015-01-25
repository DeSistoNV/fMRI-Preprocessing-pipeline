# #this creates a modified "inputnode" for the fsl_preproc pipeline. It inherits a specific nipype class and creates the
# # appropriate input fields.
from nipype.interfaces.utility import IdentityInterface
import os
import sys



class fsl_preproc_inode(IdentityInterface):
    ##this __init__ definition uses a trick from stack overflow to initialize a super class
    ##creates the input node fields needed to start an fsl_preproc pipeline
    ##provides connection and cursor for mri db
    def __init__(self):
        self.pandars= 0
        super(fsl_preproc_inode, self).__init__(fields=[
            't_min',  # [], 1 = remove the reference scan, 0 = don't need to bother
            't_size',  # always set larger than the number of vols in the longest run
            'ref_run',  # this is going to be the reference volume for motion correction.
            'padNum',  # = the largest number of padding vols. required for any run in the run_list
            'nVols',  # [], the total number of volumes that you need to end up with for each run.
            'run_list',  # [], list of runs to preprocess
            'results_base_dir',  # directory for where results go
            'results_container',
            'do_FNIRT',
            'spatial_crop',
            'abs_run_id',
            'moco_only',
            'searchr_x',
            'searchr_y',
            'searchr_z',
            'interp_FNIRT',
            'interp_FLIRT',
            'dof_FLIRT',
            'rigid2D_FLIRT'
            'convert_dicoms'
        ])

        ###method for populating the input node fields with data from mri db
        ##NEED TO ADD AS KEYWORD INPUTS: runtype and runnum (in case I only want first or last or whatever)

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

        if not 'db' in kwargs.keys():
            sys.exit("Exception in panda_fields: need a ['db'] arg\nExecution Stopped")
        if not os.path.isfile(kwargs['db']):
            sys.exit('Exception in panda_fields: db file: ' + kwargs['db'] + ' not found\nExecution Stopped')

        # if DB is a pickled pandas dataFrame
        if kwargs['db'][-2:] == '.p':
            import pandas as pd

            # unpickling and loading DataFrame
            open_panda = pd.read_pickle(kwargs['db'])
            self.pandars = open_panda


            if not 'subj' in kwargs.keys():  # if subject not passed, lists subjects in df and exits
                print "Available subjects are:"
                x = set(open_panda.subject)
                for y in x:
                    print y
                sys.exit("Execution Stopped, please choose a subject")
            elif not 'expID' in kwargs.keys():  # if expID not passed, lists expIDs in df and exits
                print "Available experiments are:\n"
                x = set(open_panda.expID)
                for y in x:
                    print y
                sys.exit("Execution Stopped, please choose a expID")

            ##  if subject and expid are passed
            if not 'runType' in kwargs.keys():  # if no runType is passed, gets all runTypes from df
                kwargs['runType'] = [i for i in set(open_panda.runType)]

            ## here we need to get all session ids | subject and exp id are good
            sessions = []

            # for the number of runs in the dataFrame
            for i in xrange(len(open_panda.index) - 1):
                # sessions = [(subject,sessionID)] for all runs in dataFrame
                sessions.append((open_panda.subject[i], open_panda.sessionID[i]))

            # dropping all runs that are not passed subject initials
            sess_list = [i for i in set(int(i[1]) for i in sessions if i[0] == kwargs['subj'])]
            #inserting expid and subject at beginning of list
            sess_list.insert(0, kwargs['expID'])
            sess_list.insert(0, kwargs['subj'])
            run_temp = []

            # for number of runs in DataFrame
            for i in xrange(len(open_panda.index) - 1):
                run_temp.append((i, open_panda.sessionID[i]))
            # here run_temp is list[(int,sessionID)]

            # keeping only tuples from run_temp if sessionID is in session list
            runIDs = [i[0] for i in run_temp if int(i[1]) in sess_list]

            # NEED TO LOOK AT THIS SEEMS JACKED
            if 'runList' in kwargs.keys():
                if kwargs['runList']:
                    runIDs = [runIDs[ii] for ii in kwargs['runList']]
            self.inputs.abs_run_id = runIDs

            ## (runPath,runName,nVols,Sref,Padvol) for where runID in runIDs
            res = []
            for i in xrange(len(open_panda.index) - 1):
                res.append(
                    (i, open_panda.run_path[i], open_panda.run_data_file[i], open_panda.nvols[i], open_panda.siemensRef[i],
                     open_panda.padVol[i]))
            res = [i[1:] for i in res if i[0] in runIDs]

            #populate the run_list field
            self.inputs.run_list = []
            self.inputs.t_min = []
            self.inputs.nVols = []

            for row in res:
                self.inputs.t_min.append(int(row[3]))
                self.inputs.nVols.append(int(row[2]))
            self.inputs.t_min = [int(row[3]) for row in res]
            self.inputs.run_list = [row[0] + '/' + row[1] for row in res]
            self.inputs.padNum = max([int(row[4]) for row in res])

            ##need to add a specific volume each of the elements in the run_list. so we add the last one
            for ii, runs in enumerate(self.inputs.run_list):
                self.inputs.run_list[ii] += ('/' + sorted([i for i in os.listdir(runs) if '.nii' in i]).pop())

            ##finally, deal with spatial cropping issues if any of the volumes don't have the same size
            #grab the dimensions for each of the runs
            preDims = []
            for i in xrange(len(open_panda.index) - 1):
                preDims.append((i, open_panda.matrix_x[i], open_panda.matrix_y[i], open_panda.n_slices[i]))
            preDims = [list(i[1:]) for i in preDims if i[0] in runIDs]
            # noinspection PyUnusedLocal
            dims = [[] for x in xrange(3)]
            for li in preDims:
                dims[0].append(int(li[0]))
                dims[1].append(int(li[1]))
                dims[2].append(int(li[2]))
            dims = [tuple(dims[0]), tuple(dims[1]), tuple(dims[2])]

            mn = map(min, dims)
            self.inputs.spatial_crop = {}
            keys = [('x_min', 'x_size'), ('y_min', 'y_size'),
                    ('z_min', 'z_size')]  # these keys refer to input args. in fslroi. kinda hacky.
            for jj, ii in enumerate(kwargs['cropRule']):
                if ii == 'min':  # from left to right
                    self.inputs.spatial_crop[keys[jj][0]] = [0 for ff in dims[jj]]
                    self.inputs.spatial_crop[keys[jj][1]] = [mn[jj] for ff in dims[jj]]
                elif ii == 'max':  # from right to left
                    self.inputs.spatial_crop[keys[jj][0]] = [ff - mn[jj] for ff in dims[jj]]
                    self.inputs.spatial_crop[keys[jj][1]] = [mn[jj] for ff in dims[jj]]
                elif ii == 'med':  # from the center out
                    self.inputs.spatial_crop[keys[jj][0]] = [(ff - mn[jj]) / 2 for ff in dims[jj]]
                    self.inputs.spatial_crop[keys[jj][1]] = [mn[jj] for ff in dims[jj]]

        ###########################
        ## SQL STUFF STARTS HERE ##
        ###########################
        elif kwargs['db'][-2:] == 'db':
            import sqlite3

            self.connection = sqlite3.connect(kwargs['db'])
            self.connection.row_factory = sqlite3.Row
            self.cursor = self.connection.cursor()
            if not 'subj' in kwargs.keys():
                self.cursor.execute('SELECT DISTINCT subject FROM mri')
                res = self.cursor.fetchall()
                print "Available subjects are:\n"
                res = [this[0] for this in res]
                for col in res:
                    print col
                return
            elif not 'expID' in kwargs.keys():
                self.cursor.execute('SELECT DISTINCT expID FROM mri WHERE subject=:subj', kwargs)
                res = self.cursor.fetchall()
                print "Available experiments are:\n"
                res = [this[0] for this in res]
                for col in res:
                    print col
                return
            if not 'runType' in kwargs.keys():
                self.cursor.execute('SELECT DISTINCT runType FROM mri')
                res = self.cursor.fetchall()
                kwargs['runType'] = [this[0] for this in res]

            ##get the right sessions
            self.cursor.execute('SELECT DISTINCT sessionID FROM mri WHERE subject=:subj', kwargs)
            res = self.cursor.fetchall()
            getThese = [this[0] for this in res]
            sessList = getThese
            if 'sessList' in kwargs.keys():
                if kwargs['sessList']:
                    sessList = [getThese[ii] for ii in kwargs['sessList']]

            ##construct the query
            query = 'SELECT runID FROM mri WHERE subject=? AND expID=? AND sessionID IN (%s)' % ', '.join('?' for ii in
                                                                                                          sessList)

            ##collect the query data
            sessList.insert(0, kwargs['expID'])
            sessList.insert(0, kwargs['subj'])

            ##fetch the run id's
            self.cursor.execute(query, sessList)
            res = self.cursor.fetchall()
            runIDs = [this[0] for this in res]

            ##select the runs you want from run list
            if 'runList' in kwargs.keys():
                if kwargs['runList']:
                    runIDs = [runIDs[ii] for ii in kwargs['runList']]

            self.inputs.abs_run_id = runIDs

            ##get the fields
            query = 'SELECT runPath,runName,nVols,seimensRef,padVol FROM mri WHERE runID IN (%s)' % ', '.join(
                '?' for ii in runIDs)
            self.cursor.execute(query, runIDs)
            res = self.cursor.fetchall()



            ##populate the run_list field
            self.inputs.run_list = []
            self.inputs.t_min = []
            self.inputs.nVols = []
            padNum = []
            for rows in res:
                self.inputs.run_list.append(rows['runPath'] + '/' + rows['runName'])
                self.inputs.t_min.append(rows['seimensRef'])
                self.inputs.nVols.append(rows['nVols'])
                padNum.append(rows['padVol'])
            self.inputs.padNum = max(padNum)

            ##need to add a specific volume each of the elements in the run_list. so we add the last one
            for ii, runs in enumerate(self.inputs.run_list):
                self.inputs.run_list[ii] += ('/' + sorted([i for i in os.listdir(runs) if '.nii' in i]).pop())

            ##finally, deal with spatial cropping issues if any of the volumes don't have the same size
            #grab the dimensions for each of the runs
            sizes = 'matrixSizeX,matrixSizeY,matrixSizeZ'
            query = 'SELECT ' + sizes + ' FROM mri WHERE runID in (%s)' % ', '.join('?' for ii in runIDs)
            self.cursor.execute(query, runIDs)
            res = self.cursor.fetchall()
            #find the min of each dimension across runs
            dims = [[rr[dd] for rr in res] for dd in sizes.split(',')]  ##puts dimensions in a list of 3 lists

            mn = map(min, dims)
            self.inputs.spatial_crop = {}
            keys = [('x_min', 'x_size'), ('y_min', 'y_size'),
                    ('z_min', 'z_size')]  ##these keys refer to input args. in fslroi. kinda hacky.
            for jj, ii in enumerate(kwargs['cropRule']):
                if ii == 'min':  ##from left to right
                    self.inputs.spatial_crop[keys[jj][0]] = [0 for ff in dims[jj]]
                    self.inputs.spatial_crop[keys[jj][1]] = [mn[jj] for ff in dims[jj]]
                elif ii == 'max':  ##from right to left
                    self.inputs.spatial_crop[keys[jj][0]] = [ff - mn[jj] for ff in dims[jj]]
                    self.inputs.spatial_crop[keys[jj][1]] = [mn[jj] for ff in dims[jj]]
                elif ii == 'med':  ##from the center out
                    self.inputs.spatial_crop[keys[jj][0]] = [(ff - mn[jj]) / 2 for ff in dims[jj]]
                    self.inputs.spatial_crop[keys[jj][1]] = [mn[jj] for ff in dims[jj]]
            try:
                self.cursor.close()
                del self.cursor     # this will actually destroy attribute
                del self.connection
            except:
                print "no database open"
                pass
        else:
            sys.exit('invalid database type. need .db or .p')

## Added 1.13.15
## Method to add working volume and brain mask file paths
## Precondition : pipeline has been run
## Param results_base_directory : base directory where pipeline stores results
## Param inputs : main_inputnode.inputs ; this is to get the run list
## Param db : location of pickled pandas DataFrame file
def append_pandas(inputnode,params_dict,db):
    try:

        if not os.path.isdir(inputnode.inputs.basedir):  ## check if the results_base_directory exists
            raise IOError()
        import pandas as pd
        open_panda = pd.read_pickle(db)

        container = params_dict['results_container']
        container = container if container[0] == '/' else '/' + container
        results = params_dict['results_base_dir'] + container
        brain_mask = results + '/brain_mask'
        while os.path.isdir(brain_mask):
            brain_mask += '/' + os.listdir(brain_mask)[0]
        for run in inputnode.inputs.abs_run_id:   # adding brain mask for all the runs in the run list
            print 'brain mask for runID ' + str(run) + ' added'
            open_panda.ix[run,'brain_mask'] = brain_mask

        working_vols = results + '/final_aligned'
        while '_work' not in os.listdir(working_vols).pop():
            working_vols+= '/' + os.listdir(working_vols).pop()
        vol_dirs = [working_vols  +'/' + vol for vol in os.listdir(working_vols)]
        vol_dirs = [vol + '/' + os.listdir(vol)[0] for vol in vol_dirs]


        for vol in vol_dirs:
            #print 'working volume for runID ' + str(vol) + ' added'
            index = int(vol[-8:-7])
            open_panda.ix[index,'working_vol'] = vol

    except IOError:
        print "\nERROR ADDING BRAIN MASK AND WORKING VOLUME: CAN'T APPEND A NON-EXISTING FILE \n\t run pipeline first."



# Added 1.16.15
# Method to update csv file that keeps tracks of params used for various pipeline runs
#param fsl : fsl_preproc_params dictionary
#param csv : .csv file of the parameters db
def append_param_csv(fsl,csv):
    try:
        if not os.path.isfile(csv):
            raise IOError
        import pandas as pd
        df = pd.read_csv(csv,index_col = False)

        df.loc[len(df)+1]=[fsl['results_base_dir'].split('/')[-1],fsl['t_size'],fsl['bet_frac'],str(fsl['FLIRT_cost_func'])[2:len(fsl['FLIRT_cost_func']) - 3],
                           fsl['interp_FLIRT'],fsl['dof_FLIRT'],str(fsl['rigid2D_FLIRT']),fsl['interp_FNIRT'],
                           fsl['FNIRT_subsamp'],fsl['FNIRT_warpres']]
        df.to_csv(csv,index=False,float_format='%.3f')
        print df

        print 'results csv updated'
    except IOError:
        print csv + 'does not exist.'

# Added 1.23.15
# Method to check if params have been used against csv file
#param fsl : fsl_preproc_params dictionary
#param csv: csv file of the paramters db
def check_params_used(fsl,csv):
    try:
        if not os.path.isfile(csv):
            raise IOError
        import pandas as pd
        df = pd.read_csv(csv,index_col = False)
        keys = [df.columns[i] for i in range(len(df.columns)) ]
        vals = [fsl['results_base_dir'].split('/')[-1],fsl['t_size'],fsl['bet_frac'],str(fsl['FLIRT_cost_func'])[2:len(fsl['FLIRT_cost_func']) - 3],
                           fsl['interp_FLIRT'],fsl['dof_FLIRT'],fsl['rigid2D_FLIRT'],fsl['interp_FNIRT'],
                           str([str(i) for i in fsl['FNIRT_subsamp']]).replace("'",''),str([str(i) for i in fsl['FNIRT_warpres']]).replace("'",'')]
        test = dict(zip(keys,vals))
        counts = []
        for i in df.index:
            test_row = df.loc[i].to_dict()
            test_row['bet_frac'] = round(test_row['bet_frac'],2)
            diff = set(test_row.items()) ^ set(test.items())
            counts.append(len(diff))
        if 0 in counts:
            print 'parameters have already been used'
            return True
        else:
            print 'parameters have not been tested yet'
            return False

    except IOError:
        print csv + 'does not exist.'
# Added 1.19.15
# Method that grabs all the corrected movies and copies them into a single folder for easier veiwing
#
# !! Needs params
def collect_results():
    import os
    from shutil import copyfile


    result_dirs = ['/home/nick/datDump/' + dir for dir in list(os.listdir('/home/nick/datDump')) if 'results' in dir]
    result_dirs = [dir + '/Imagery_RF_test/corrected_movie' for dir in result_dirs]
    finals = []
    for dir in result_dirs:
        while '.nii' not in os.listdir(dir)[0]:
            dir += '/' + os.listdir(dir)[0]
        dir += '/' + os.listdir(dir)[0]
        finals.append(dir)
    copy_count = 0
    for file in finals:
        dest = '/home/nick/datDump/corrected_movies/' + file.split('/')[4][7:] + '.nii.gz'
        if os.path.isfile(dest):
            pass
        else:
            copyfile(file,dest)
            copy_count += 1
    print str(copy_count) + ' files copied.'


