def create_fsl_preproc_workflow(fsl_preproc_inputnode):
	"""
	pp = create_fsl_preproc_workflow(fsl_preproc_inputnode)

	Constructs an FSL based preprocessing pipeline.
	1) conversion to nii
	2) seimens reference volume removal 
	3) pads or truncates runs that were either too short or too long by accident.
	4) skull stripping
	5) motion correction
	6) flrt
	7) fnrt (optional)
	8) concatenates xforms so that interpolation done only once
	9) makes "before" and "after" movies for quality checking
	Final analyzable functional volumes end up in "final_aligned" subfolder. "before" / "after" movies end up in "uncorrected_movie" and "corrected_movie"

	Input supplied through a specialized IdentityInterface sub-class that connect directly to the mri.db. List of fields for the input node as follows:
	t_min,			##[], 1 = remove the reference scan, 0 = don't need to bother  
	t_size,			##always set larger than the number of vols in the longest run  
	ref_run, 			##this is going to be the reference volume for motion correction.
	padNum,   			## = the largest number of padding vols. required for any run in the run_list
	nVols,			##[], the total number of volumes that you need to end up with for each run.
	run_list,    			##[], list of runs to preprocess 
	results_base_dir,		##directory for where results go
	results_container		##subdirectory for results

	"""

	import os                                    		# system functions
	import nipype.interfaces.fsl as fsl          		# fsl
	import nipype.pipeline.engine as pe          		# pypeline engine
	import nipype.interfaces.io as nio			# for data sink node
	from convert_2_nii import preProc as c2n		# conversion from dicom to nii
	# to create volume movies before and after moco
	from mean_merge import preProc as mm
	# to remove the siemens reference scan for runs that need it
	from kill_ref import preProc as kr
	# to truncate or pad runs that went too long / short during the experiment
	from pad_vol import preProc as pv
	import nipype.interfaces.utility as util              # for defining input node
	import nipype.interfaces.fsl.utils as fslutils
	from fugue import preProc as fugue_file


	# from list_helpers import flatten                      # needed to
	# flatten lists of lists

	# ==============function definitions

	# needed for the pad_vol workflow
	splooge = 'def func(vol, mean, padNum): return [vol]+[mean]*padNum'
	# this is a interfaces.utility.Function node that concatenates volumes for
	# padding.
	pv.inputs.padList.function_str = splooge

	# needed to prepare for the concatenation node: see expand_by_n in
	# list_helpers
	expand_by_n = 'def func(mat_list, nVols): return [mat_list[k] for k,num in enumerate(nVols) for j in range(num)]'

	# needed to prepare lists for the final merge
	reduce_by_n = 'def func(run_list, nVols): return [[run_list.pop(0) for ii in range(num)] for num in nVols]'

	# for flattening lists of lists
	def flatten(l):
		import itertools
		return list(itertools.chain.from_iterable(l))

	# for flattening lists of lists and then taking the first element
	def flatten_first(l):
		import itertools
		return list(itertools.chain.from_iterable(l))[0]

	# for grabbing the first element of each list in a list of lists.
	def grab_first_element(l):
		return [ii[0] for ii in l]

	# for grabbing just the first element in a list
	def grab_first(l):
		return l[0]

	# =====function def
	def get_key(mydict, key):
		return mydict[key]

	# ================================================create workflows

	# clone the mean/merge workflow
	cor_mm = mm.clone('corrected_meanmerge')
	uncor_mm = mm.clone('uncorrected_meanmerge')

	# define the pre-processing workflow
	preProc = pe.Workflow(name='fsl_preproc')

	# ================================================define workflow nodes
	# input node to distribute inputs
	inputnode = pe.Node(interface=fsl_preproc_inputnode,
	                    name='inputnode')

	bet_vols = pe.MapNode(	interface=fsl.BET(functional=True, frac=inputnode.inputs.bet_frac, mask=True),
	                       name='bet_vols',
	                       iterfield='in_file'
	                       )

	moco_vols = pe.MapNode(interface=fsl.MCFLIRT(ref_vol=0, save_mats=True),
	                       name='moco_vols',
	                       iterfield='in_file'
	                       )

	# For concatenating transformations matrices
	convertX = pe.MapNode(interface=fslutils.ConvertXFM(concat_xfm=True),
	                   iterfield=['in_file', 'in_file2'],
	                   name='convertX'
	                   )

	flrt = pe.MapNode(interface=fsl.FLIRT(rigid2D=inputnode.inputs.rigid2D_FLIRT, dof=inputnode.inputs.dof_FLIRT),
	                  name='flrt',
	                  iterfield=['in_file'])

	# Forcing user to specifiy cost function
	flrt.iterables = [('cost_func', inputnode.inputs.FLIRT_cost_func)]

	# split the 4D volumes up into individual 3D files
	splt = pe.MapNode(interface=fslutils.Split(dimension='t'),
	                  name='splt',
	                  iterfield=['in_file']
	                  )

	# apply the concatenated flirt/mcflrit or mcflirt/flirt/fnirt transform to
	# each volume of each run
	if not inputnode.inputs.do_FNIRT:
	    appX = pe.MapNode(interface=fsl.ApplyXfm(apply_xfm=True, interp=inputnode.inputs.interp_FLIRT),
	                      name='appX',
	                      iterfield=['in_file', 'in_matrix_file']
	                      )
	    appX_ref = 'reference'

	else:
	    appX = pe.MapNode(interface=fsl.ApplyWarp(interp=inputnode.inputs.interp_FNIRT),
	                      name='appX',
	                      iterfield=['in_file', 'field_file',
	                                 'premat',]
	                      )
	    appX_ref = 'ref_file'
	    fnrt = pe.MapNode(interface=fsl.FNIRT(field_file=True),
	                      name='fnrt',
	                      iterfield=['in_file', 'affine_file']
	                      )

	    if inputnode.inputs.FNIRT_subsamp and inputnode.inputs.FNIRT_warpres:
	        fnrt.iterables = [('subsampling_scheme', inputnode.inputs.FNIRT_subsamp),
	                          ('warp_resolution', inputnode.inputs.FNIRT_warpres)]
	    elif inputnode.inputs.FNIRT_subsamp:
	        fnrt.iterables = ('subsampling_scheme',
	                          inputnode.inputs.FNIRT_subsamp)
	    elif inputnode.inputs.FNIRT_warpres:
	        fnrt.iterables = ('warp_resolution',
	                          inputnode.inputs.FNIRT_warpres)
	    else:
	        print "=================using default FNIRT parameters"

	# merge the volumes that have been split up back into single 4D run files
	remerge = pe.MapNode(interface=fslutils.Merge(dimension='t'),
	                     name='remerge',
	                     iterfield=['in_files']
	                     )

	# pepare the flrt xfm matrices for concatenation with the mcflrt xfm
	# matrices
	expand_flrt_mats = pe.Node(interface=util.Function(input_names=['mat_list', 'nVols'],
	                                                   output_names=['out']),
	                           # function_str = expand_by_n),
	                           name='expand_flrt_mats')
	# <<that this is necessary must be a bug.
	expand_flrt_mats.inputs.function_str = expand_by_n

	expand_final_mats = pe.Node(interface=util.Function(input_names=['mat_list', 'nVols'],
	                                                     output_names=['out']),
	                             # function_str = expand_by_n),
	                             name='expand_final_mats')
	# <<that this is necessary must be a bug.
	expand_final_mats.inputs.function_str = expand_by_n

	concat_fugue_and_fnrt = pe.MapNode(interface=fsl.ConvertWarp(),
	                                iterfield=['shift_in_file',
	                                           'reference', 'warp1'],
	                                name='concat_fugue_and_fnrt'
	                                )

	# prepare the fnrt xfm fields for applywarp
	if inputnode.inputs.do_FNIRT:
	    expand_fnrt_mats = pe.Node(interface=util.Function(	input_names=['mat_list', 'nVols'],
															output_names=['out']),
															name='expand_fnrt_mats')
	    expand_fnrt_mats.inputs.function_str = expand_by_n

	# re-group the list of volumes into a list of lists, with each list
	# collecting all volumes for a single run.
	group_aligned_vol_list = pe.Node(interface=util.Function(input_names=['run_list', 'nVols'],
	                                                         output_names=['out']),
	                                 name='group_aligned_vol_list')
	group_aligned_vol_list.inputs.function_str = reduce_by_n

	# datasink
	datasink = pe.Node(interface=nio.DataSink(parameterization=True),
	                   name='datasink')

	# file naming
	rename = pe.MapNode(interface=util.Rename(format_string='%(run_id).05d',
	                                          keep_ext=True),
	                    iterfield=['in_file', 'run_id'],
	                    name='working_vol')

	fuguepipe = fugue_file.clone('fugue')
	# ====================================================================================connect nodes
	# ====================================================================================connect nodes
	# ====================================================================================connect nodes

	# prepare the datasink for receiving sweet, sweet data
	preProc.connect(inputnode,'results_base_dir',datasink,'base_directory')
	preProc.connect(inputnode,'results_container',datasink,'container')

	# correct dimensions (applied if needed. otherwise, just passes data through).
	for dims in inputnode.inputs.spatial_crop.keys():
		preProc.connect([(inputnode, kr,[(('spatial_crop', get_key, dims), 'krInputnode.' + dims)])])


	preProc.connect(inputnode,'t_min',kr,'krInputnode.t_min')
	preProc.connect(inputnode,'t_size',kr,'krInputnode.t_size')
	preProc.connect(kr,'dropref.roi_file',pv,'pvInputNode.run_list')
	preProc.connect(inputnode,'padNum',pv,'pvInputNode.padNum')
	preProc.connect(inputnode,'nVols',pv,'pvInputNode.nVols')

	if inputnode.inputs.convert_dicoms:
		preProc.connect(inputnode,'run_list',c2n,'c2nInputnode.run_list')
		preProc.connect(c2n,'nii_vols.converted_files',kr,'krInputnode.run_list') # pad / truncate runs with too few / many volumes.
		
	else:
		preProc.connect(inputnode,'run_list',kr,'krInputnode.run_list')



    # skull stripping
	preProc.connect(pv, 'extract.roi_file', bet_vols, 'in_file')
    # motion correction branch
	preProc.connect(bet_vols, 'out_file', moco_vols, 'in_file')

	if not inputnode.inputs.moco_only:
        # split vols and send to applyXform (or applyWarp if we're doing fnrt)
		preProc.connect(moco_vols, 'out_file', splt, 'in_file')
		preProc.connect(splt, ('out_files',flatten), appX, 'in_file')

        # determine the reference run file and distribute to flrt and appX
        # if no ref_run specified, then we grab the first run of the first vol
		if not inputnode.inputs.ref_run:
			preProc.connect(splt,('out_files',flatten_first),flrt,'reference')
			preProc.connect(splt,('out_files',flatten_first),appX,appX_ref)
 
        # prepare the reference file for the case that we're doing fnirt
		if (not inputnode.inputs.ref_run) and inputnode.inputs.do_FNIRT:
			preProc.connect(splt,('out_files',flatten_first),fnrt,'ref_file')

		elif inputnode.inputs.do_FNIRT:
			preProc.connect(inputnode,'ref_fun',fnrt,'ref_file')

		# collect vols for flrt
		preProc.connect(splt,('out_files', grab_first_element),flrt,'in_file')

		# collect vols for fnrt and prepare output xforms


		if inputnode.inputs.do_FNIRT:
			preProc.connect(flrt,'out_matrix_file',fnrt,'affine_file')
			preProc.connect(splt,('out_files',grab_first_element),fnrt,'in_file')

			preProc.connect(fnrt,'field_file',concat_fugue_and_fnrt,'warp1')
			preProc.connect(inputnode,'nVols',expand_final_mats,'nVols')

		# pepare transforms for the case that we're not doing FNIRT
		if not inputnode.inputs.do_FNIRT:
			preProc.connect(flrt,'out_matrix_file',expand_flrt_mats,'mat_list')
			preProc.connect(inputnode,'nVols',expand_flrt_mats,'nVols')
			preProc.connect(expand_flrt_mats,'out',convertX,'in_file')
			preProc.connect(moco_vols,('mat_file',flatten),convertX,'in_file2')
			preProc.connect(convertX,'out_file',appX,'in_matrix_file')

		else:
			preProc.connect(moco_vols,('mat_file',flatten),appX,'premat')


	    # remerge the aligned files

		preProc.connect(appX,'out_file',group_aligned_vol_list,'run_list')
		preProc.connect(inputnode,'nVols',group_aligned_vol_list,'nVols')
		preProc.connect(group_aligned_vol_list,'out',remerge,'in_files')
	
	    # create before / after movies
		preProc.connect(bet_vols,'out_file',uncor_mm,'mmInputnode.run_list')
		preProc.connect(remerge,'merged_file',cor_mm,'mmInputnode.run_list')

	    # collect final pipleline products in datasink

		preProc.connect(remerge,'merged_file',rename,'in_file')

	else:
		preProc.connect(bet_vols,('out_file',grab_first),moco_vols,'ref_file') # if moco_only, align to middle vol of first run
		preProc.connect(moco_vols,'out_file',cor_mm,'mmInputnode.run_list')
		preProc.connect(bet_vols,'out_file',uncor_mm,'mmInputnode.run_list')
		preProc.connect(moco_vols,'out_file',rename,'in_file')


	preProc.connect(inputnode,'abs_run_id',rename,'run_id')
	preProc.connect(rename,'out_file',datasink,'final_aligned')
	preProc.connect(uncor_mm,'merge.merged_file',datasink,'uncorrected_movie')
	preProc.connect(cor_mm,'merge.merged_file',datasink,'corrected_movie')
	preProc.connect(bet_vols,('mask_file',grab_first),datasink,'brain_mask')

	if inputnode.inputs.do_fugue:
		preProc.connect(moco_vols, 'out_file', fuguepipe, 'fugueInputnode.in_files')
		preProc.connect(inputnode, 'delta_TE', fuguepipe, 'fugueInputnode.delta_TE')
		preProc.connect(inputnode, 'mag_frac', fuguepipe, 'fugueInputnode.mag_frac')
		preProc.connect(inputnode, 'dwell_time', fuguepipe, 'fugueInputnode.dwell_time')
		preProc.connect(inputnode,'unwarp_direction',fuguepipe,'fugueInputnode.unwarp_direction')

		preProc.connect(inputnode, 'phase', fuguepipe, 'fugueInputnode.phase')
		preProc.connect(inputnode, 'mags', fuguepipe, 'fugueInputnode.mags')

		preProc.connect(fuguepipe, 'fugue.shift_out_file', concat_fugue_and_fnrt, 'shift_in_file')
		preProc.connect(moco_vols, 'out_file', concat_fugue_and_fnrt, 'reference')
		preProc.connect(concat_fugue_and_fnrt, 'out_file', expand_final_mats, 'mat_list')
		preProc.connect(expand_final_mats, 'out', appX, 'field_file')

		preProc.write_graph(	)


	return preProc
