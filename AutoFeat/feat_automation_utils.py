import pandas as pd
import subprocess
pd.set_option('display.max_columns', 500)
from os import listdir
from subprocess import check_output

inputs = dict()


# run fslstats to get nvols
def get_nvols(file_path):
    return subprocess.check_output(['fslstats',data,'-w']).split()[-1]

# load a database, subject wise
def load_db(csv,subj):
    ret = pd.read_csv(csv)
    return ret[ret.subject == subj]

# load in template fsf file
def get_template():
    with open('template.fsf') as f:
        cmds = [line[:-1] for line in f if line[0] != '#' and line[:-1] != '']
    return cmds


def build_runs(df,inp):
    r = []
    for i in df.index:
        fmri = dict()
        fmri['input'] = df.run_data_file[i]
        fmri['outputdir'] = '{}/{}'.format(inp['out_dir'],df.runID[i])
        fmri['tr'] = df.TR[i]
        fmri['npts'] = df.nvols[i] # if we need to check : # get_nvols(fmri['input']) # n volumes
        fmri['multiple'] =  1
        fmri['mc'] = 1 if inp['Motion Correction'] else 0 # motion correction BOOL
        fmri['regunwarp_yn'] = 1 if inp['B0 Unwarping'] else 0 # B0 fieldmap unwarping?
        fmri['bet_yn'] = 1 if inp['Brain Extraction'] else 0 # BET brain extraction BOOL
        fmri['smooth'] = inp['Spatial Smooth'] # Spatial smoothing FWHM (mm)
        fmri['reginitial_highres_dof'] = inp['BBR DOF'] # Degrees of Freedom for registration to initial structural
        fmri['unwarp_dir'] = inp['Unwarp Direction'] # NO QOUTES # Unwarp direction
        fmri['reghighres_yn'] =  1 if inp['Register to Structural'] else 0 # Registration to main structural BOOL

        files = dict()
        files['feat_files(1)'] =  df.run_path[i] + '/' + df.run_data_file[i] + '/'
        files['feat_files(1)'] += [f for f in listdir(files['feat_files(1)']) if '.nii' in f][0]
        files['unwarp_files(1)'] =  df.field_map_phase[i]
        files['unwarp_files_mag(1)'] = df.field_map_mag[i]
        fmri['st_file'] = df.st_file[i]
        files['highres_files(1)'] = df.anatomical[i]
        fmri['dwell'] = df.dwell[i] # EPI dwell time (ms)
        fmri['te'] = df.TE[i]# EPI TE (ms)
        r.append((fmri,files))
    return r

# replace inputs in the template fsf
def build_fsf(fmri,files):
    cmds = get_template()
    ignores = ['ncopeinputs','filtering_yn','temphp_yn','templp_yn','ndelete','prewhiten_yn',
              'scriptevsbeta','nftests_orig','nftests_real','alternateReference_yn',
              'tempfilt_yn1','alternative_mask','overwrite_yn']
    remove = ['set feat_files(','set unwarp_files','set highres']
    cmds = [c for c in cmds if not any(rem in c for rem in remove)]
    for key in fmri:
        for i,cmd in enumerate(cmds):
            cmd_splt = cmd.replace('(',',').replace(')',',').split(',')[1] # grabbing the param out of the line
            if key in cmd and cmd_splt not in ignores:
                cmds[i] = 'set fmri({}) {}'.format(key,fmri[key])
    for key in files:
        cmds.append('set {} "{}"'.format(key,files[key]))
    return cmds

# save all the fsf files and return list of their paths
def save_fsf(out,fsfs):
    p = []
    for i,f in enumerate(fsfs):
        location = '{}/{}.fsf'.format(out,i)
        with open(location,'w') as fi:
            for cmd in f:
                fi.write(cmd + '\n')
        p.append(location)
    return p

# runs feat on all the fsfs
def run_feat_all(dataframe):
    for i, fsf in enumerate(dataframe.fsf_files):
        print fsf
        print 'run {}/{} running'.format(i+1,len(dataframe.fsf_files))
        output = subprocess.check_output(['feat',fsf])
        print output
        print 'run {}/{} complete'.format(i+1,len(dataframe.fsf_files))


# def prepare_field_maps(dataframe):
#     for i in dataframe.index:
#         prepare_location = '/'.join(dataframe.field_map_mag[i].split('/')[:-1]) + '/prepped_map.nii'
#         fpf_cmd = 'fsl_prepare_fieldmap SIEMENS {} {} {} {}'.format(dataframe.field_map_phase[i],dataframe.field_map_mag[i],prepare_location,dataframe.dwell[i])
#         print fpf_cmd + '\n'
#         subprocess.check_output([fpf_cmd])
#         dataframe.field_map_mag[i] = prepare_location
#     return dataframe

# fsl_prepare_fieldmap <scanner> <phase_image> <magnitude_image> <out_image> <deltaTE (in ms)> [--nocheck]


#### TESTING VARS #####
# df['field_map_mag'] =  '/home/nick/Desktop/1_015_gre_field_mapping_1x1x2_20111013/naselaris_ca_20111013_001_015_gre_field_mapping_1x1x2.nii.gz'
# df['field_map_phase'] ='/home/nick/Desktop/1_016_gre_field_mapping_1x1x2_20111013/naselaris_ca_20111013_001_016_gre_field_mapping_1x1x2.nii'
# df['anatomical']= '/home/nick/Desktop/CO_s1000_T1.nii'
# df['dwell'] = .3
# df['run_path'] = '/home/nick/ichi/mnt/vison_conv/naselaris_ca'

# df
