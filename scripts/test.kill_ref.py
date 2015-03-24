from kill_ref import preProc as kr
##===========directories / parameter
basedir = '/Data/tmp/test.spatial.crop'

##===========name the runs
run_list = ['/Data/tmp/test.spatial.crop/MR-SE005-eja_ep2d_bold_1mm_1500TR/20110715_141537ejaep2dbold1mm1500TRs005a001.nii.gz', '/Data/tmp/test.spatial.crop/MR-SE047-eja_ep2d_bold_1mm_1500TR_st31]/20110715_141537ejaep2dbold1mm1500TRst31s047a001.nii.gz']

##==========inform the convert 2 nii node 
kr.inputs.krInputnode.run_list = run_list
kr.inputs.krInputnode.t_min = [0, 0]
kr.inputs.krInputnode.t_size = [170]
kr.inputs.krInputnode.spatial_crop['x_min'] = [0, 5]
kr.inputs.krInputnode.spatial_crop['x_size'] = [126, 131]
kr.inputs.krInputnode.spatial_crop['y_min'] = [0, 0]
kr.inputs.krInputnode.spatial_crop['y_size'] = [140, 140]
kr.inputs.krInputnode.spatial_crop['z_min'] = [0, 0]
kr.inputs.krInputnode.spatial_crop['z_size'] = [29, 29]

##==========connect convert and mean/merge

kr.run()	
 