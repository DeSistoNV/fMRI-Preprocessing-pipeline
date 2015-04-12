


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
  from mean_merge import preProc as mm		 	# to create volume movies before and after moco
  from kill_ref import preProc as kr			# to remove the siemens reference scan for runs that need it
  from pad_vol import preProc as pv			# to truncate or pad runs that went too long / short during the experiment
  import nipype.interfaces.utility as util              # for defining input node
  import nipype.interfaces.fsl.utils as fslutils
  

#from list_helpers import flatten                      # needed to flatten lists of lists

  ##==============function definitions
  
  ##needed for the pad_vol workflow
  splooge = 'def func(vol, mean, padNum): return [vol]+[mean]*padNum'
  pv.inputs.padList.function_str = splooge  ##this is a interfaces.utility.Function node that concatenates volumes for padding. 

  
  ##needed to prepare for the concatenation node: see expand_by_n in list_helpers
  expand_by_n = 'def func(mat_list, nVols): return [mat_list[kk] for kk,num in enumerate(nVols) for jj in range(num)]'
  
  ##needed to prepare lists for the final merge
  reduce_by_n = 'def func(run_list, nVols): return [[run_list.pop(0) for ii in range(num)] for num in nVols]'
  
  ##for flattening lists of lists
  def flatten(l):
    import itertools
    return list(itertools.chain.from_iterable(l))
  
  ##for flattening lists of lists and then taking the first element
  def flatten_first(l):
    import itertools
    return list(itertools.chain.from_iterable(l))[0]
    
  ##for grabbing the first element of each list in a list of lists.
  def grab_first_element(l):
    return [ii[0] for ii in l]

  ##for grabbing just the first element in a list
  def grab_first(l):
    return l[0]

  ##=====function def
  def get_key(mydict, key):
    return mydict[key]

 


 ##================================================create workflows

  ##clone the mean/merge workflow
  cor_mm = mm.clone('corrected_meanmerge')
  uncor_mm = mm.clone('uncorrected_meanmerge')

  ##define the pre-processing workflow
  preProc = pe.Workflow(name='fsl_preproc')

  ##================================================define workflow nodes
  ##input node to distribute inputs 
  inputnode = pe.Node(interface = fsl_preproc_inputnode,
		      name = 'inputnode')
							
  ##skull stripping 
  bet_vols = pe.MapNode(interface = fsl.BET(functional=True, frac = inputnode.inputs.bet_frac, mask=True),
			name = 'bet_vols',
			iterfield = 'in_file'
			)
					    
				  
  ##motion correction 
  if inputnode.inputs.moco_only:
    moco_vols = pe.MapNode(interface = fsl.MCFLIRT(save_mats=True),
			  name = 'moco_vols',
			  iterfield = 'in_file'
			  )

  else:
    moco_vols = pe.MapNode(interface = fsl.MCFLIRT(ref_vol=0, save_mats=True),
			  name = 'moco_vols',
			  iterfield = 'in_file'
			  )
    from nipype.interfaces import afni as afni

    moco_vols = pe.MapNode(interface=afni.Volreg(outputtype = 'NIFTI_GZ') ,
                name='moco_vols',
                iterfield = 'in_file'
                       )



				    
 
  ##CONCAT_XFM
  combX = pe.MapNode(interface = fslutils.ConvertXFM(concat_xfm = True),
		     iterfield = ['in_file', 'in_file2'],
		     name = 'combX'
		     )
  
  
  ##FLIRT
  if inputnode.inputs.rigid2D_FLIRT:
    flrt = pe.MapNode(interface = fsl.FLIRT(rigid2D = inputnode.inputs.rigid2D_FLIRT),
			name = 'flrt',
			iterfield = ['in_file'])
  else:
    flrt = pe.MapNode(interface = fsl.FLIRT(dof=inputnode.inputs.dof_FLIRT),
		       name = 'flrt',
		       iterfield = ['in_file'])
    

  flrt.iterables = [('cost_func', inputnode.inputs.FLIRT_cost_func)] ##<<this means user is forced to specify cost function.

  if inputnode.inputs.searchr_x:
    flrt.iterables.append(('searchr_x', inputnode.inputs.searchr_x))
  if inputnode.inputs.searchr_y:
    flrt.iterables.append(('searchr_y', inputnode.inputs.searchr_y))
  if inputnode.inputs.searchr_z:
    flrt.iterables.append(('searchr_z', inputnode.inputs.searchr_z))
		       
  ##split the 4D volumes up into individual 3D files
  splt = pe.MapNode(interface = fslutils.Split(dimension = 't'),
		    name = 'splt',
		    iterfield = ['in_file']
		    )
		       
 
  ##apply the concatenated flirt/mcflrit or mcflirt/flirt/fnirt transform to each volume of each run
  if not inputnode.inputs.do_FNIRT:
    appX = pe.MapNode(interface = fsl.ApplyXfm(apply_xfm=True, interp = inputnode.inputs.interp_FLIRT),
		      name = 'appX',
		      iterfield = ['in_file', 'in_matrix_file']
		      )
    appX_ref = 'reference'

  else:
    appX = pe.MapNode(interface = fsl.ApplyWarp(interp = inputnode.inputs.interp_FNIRT),
		      name = 'appX',
		      iterfield = ['in_file', 'field_file', 'premat']
		      )
    appX_ref = 'ref_file'
    fnrt = pe.MapNode(interface = fsl.FNIRT(field_file = True),
		      name = 'fnrt',
		      iterfield = ['in_file', 'affine_file']
		      )
    if inputnode.inputs.FNIRT_subsamp and inputnode.inputs.FNIRT_warpres:
      fnrt.iterables = [('subsampling_scheme', inputnode.inputs.FNIRT_subsamp), ('warp_resolution', inputnode.inputs.FNIRT_warpres)]
    elif inputnode.inputs.FNIRT_subsamp:
      fnrt.iterables = ('subsampling_scheme', inputnode.inputs.FNIRT_subsamp)
    elif inputnode.inputs.FNIRT_warpres:
      fnrt.iterables = ('warp_resolution', inputnode.inputs.FNIRT_warpres)
    else:
      print "=================using default FNIRT parameters"

  ##merge the volumes that have been split up back into single 4D run files
  remerge = pe.MapNode(interface = fslutils.Merge(dimension = 't'),
		       name = 'remerge',
		       iterfield = ['in_files']
		       )
  
 
  ##pepare the flrt xfm matrices for concatenation with the mcflrt xfm matrices
  expand_flrt_mats = pe.Node(interface = util.Function(input_names =  ['mat_list', 'nVols'],
						       output_names = ['out']),
						       #function_str = expand_by_n),
			     name = 'expand_flrt_mats')
  expand_flrt_mats.inputs.function_str = expand_by_n  ##<<that this is necessary must be a bug.

  ##prepare the fnrt xfm fields for applywarp
  if inputnode.inputs.do_FNIRT:
    expand_fnrt_mats = pe.Node(interface = util.Function(input_names = ['mat_list', 'nVols'], 
							 output_names = ['out']), 
			       name = 'expand_fnrt_mats')
    expand_fnrt_mats.inputs.function_str = expand_by_n

  ##re-group the list of volumes into a list of lists, with each list collecting all volumes for a single run.
  group_aligned_vol_list = pe.Node(interface = util.Function(input_names =  ['run_list', 'nVols'],
						       output_names = ['out']),
			                 name = 'group_aligned_vol_list')
  group_aligned_vol_list.inputs.function_str = reduce_by_n
  
  ##datasink
  datasink = pe.Node(interface = nio.DataSink(parameterization = True),
		          name = 'datasink')

  ##file naming
  rename = pe.MapNode(interface = util.Rename(format_string='%(run_id).05d',
                               keep_ext=True),
                    iterfield= ['in_file','run_id'],
                    name='working_vol')
  
  
  ##====================================================================================connect nodes
 
  ##prepare the datasink for receiving sweet, sweet data										
  preProc.connect([(inputnode, datasink, [('results_base_dir', 'base_directory'),
					  ('results_container', 'container')])
		  ])


  ##convert dicoms (optional)
  if inputnode.inputs.convert_dicoms:
    preProc.connect([	  (inputnode, c2n,       [('run_list', 'c2nInputnode.run_list')])
		  ])
  
    
  ##correct dimensions (applied if needed. otherwise, just passes data through).
  for dims in inputnode.inputs.spatial_crop.keys():
    preProc.connect([	  (inputnode, kr,       [(('spatial_crop', get_key, dims), 'krInputnode.'+dims)])
		   ])
  if inputnode.inputs.convert_dicoms:
    preProc.connect([	  (inputnode, kr,        [('t_min', 'krInputnode.t_min'),				##remove the siemens reference scan
						    ('t_size', 'krInputnode.t_size')]),				##
			    (c2n, kr,              [('nii_vols.converted_files', 'krInputnode.run_list')]),	##
			    (kr, pv,               [('dropref.roi_file', 'pvInputNode.run_list')]),			##pad / truncate runs with too few / many volumes.
			    (inputnode, pv,        [('padNum', 'pvInputNode.padNum')]),
			    (inputnode, pv,        [('nVols', 'pvInputNode.nVols')])
		    ])
  else:
    preProc.connect([	  (inputnode, kr,        [('t_min', 'krInputnode.t_min'),				##remove the siemens reference scan
						    ('t_size', 'krInputnode.t_size')]),				##
			    (inputnode, kr,              [('run_list', 'krInputnode.run_list')]),	##
			    (kr, pv,               [('dropref.roi_file', 'pvInputNode.run_list')]),			##pad / truncate runs with too few / many volumes.
			    (inputnode, pv,        [('padNum', 'pvInputNode.padNum')]),
			    (inputnode, pv,        [('nVols', 'pvInputNode.nVols')])
		    ])
    
		    
  ##skull stripping
  preProc.connect([	  (pv, bet_vols,         [('extract.roi_file', 'in_file')])
		  ])


  ##motion correction branch
  preProc.connect([	  (bet_vols, moco_vols,  [('out_file', 'in_file')])			  
		  ])
			    
  if not inputnode.inputs.moco_only:
    ##split vols and send to applyXform (or applyWarp if we're doing fnrt)
    preProc.connect([	  (bet_vols, splt,       [('out_file', 'in_file')]), ##this gives us a list of lists
			    (splt, appX,           [(('out_files', flatten), 'in_file')])
		  ])
		  

    ##determine the reference run file and distribute to flrt and appX
    ##if no ref_run specified, then we grab the first run of the first vol
    if not inputnode.inputs.ref_run:		 					
      preProc.connect([      (splt, flrt,          [(('out_files', flatten_first), 'reference')]),
			    (splt, appX,          [(('out_files', flatten_first), appX_ref)])
		    ])
    else:		      
      preProc.connect([      (inputnode, flrt,     [('ref_run', 'reference')]),
			    (inputnode, appX,     [('ref_run', appX_ref)])
		    ])
		    
    ##prepare the reference file for the case that we're doing fnirt
    if (not inputnode.inputs.ref_run) and inputnode.inputs.do_FNIRT:
      preProc.connect([	   (splt, fnrt, 	[(('out_files', flatten_first), 'ref_file')])
		    ])
    elif inputnode.inputs.do_FNIRT:
      preProc.connect([	   (inputnode, fnrt,    [('ref_run', 'ref_file')])
		    ])

    ##collect vols for flrt
    preProc.connect([	   (splt, flrt,          [(('out_files', grab_first_element), 'in_file')])
		  ])
    
    
    ##collect vols for fnrt and prepare output xforms
    if inputnode.inputs.do_FNIRT:
      preProc.connect([	   (flrt, fnrt,          [('out_matrix_file', 'affine_file')]),
			    (splt, fnrt,          [(('out_files', grab_first_element), 'in_file')]),
			    (fnrt, expand_fnrt_mats, [('field_file', 'mat_list')]),
			    (inputnode, expand_fnrt_mats, [('nVols', 'nVols')])
		    ])
    
    
    ##pepare transforms for the case that we're not doing FNIRT
    if not inputnode.inputs.do_FNIRT:
      preProc.connect([	    
			    (flrt, expand_flrt_mats,            [('out_matrix_file', 'mat_list')]),
			    (inputnode, expand_flrt_mats,       [('nVols', 'nVols')]),
			    (expand_flrt_mats, combX,           [('out', 'in_file')]),
            ## NEED TO SOMEHOW CONVERT AFNI XFORMS
			    (moco_vols, combX,     	       [(('oned_matrix_save', flatten), 'in_file2')]),
			    (combX, appX,                       [('out_file', 'in_matrix_file')])
		    ])
    else:
      preProc.connect([	   (moco_vols, appX,		       [(('oned_matrix_save', flatten), 'premat')]),
			    (expand_fnrt_mats, appX,            [('out', 'field_file')])
		    ])

    ##remerge the aligned files
    preProc.connect([	   (appX, group_aligned_vol_list,      [('out_file', 'run_list')]),
			    (inputnode, group_aligned_vol_list, [('nVols', 'nVols')]),
			    (group_aligned_vol_list, remerge,   [('out', 'in_files')])
		    ])
		    
    ##create before / after movies
    preProc.connect([	   
			    (bet_vols, uncor_mm,   [('out_file', 'mmInputnode.run_list')]),
			    (remerge, cor_mm,      [('merged_file', 'mmInputnode.run_list')])
		  ])


    ##collect final pipleline products in datasink
    preProc.connect([
			    (remerge, rename,      [('merged_file', 'in_file')]),
   		  ])
  else:
    preProc.connect([	  (bet_vols, moco_vols,    [(('out_file', grab_first), 'ref_file')]),	##if moco_only, align to middle vol of first run
			  (moco_vols, cor_mm,    [('out_file', 'mmInputnode.run_list')]),
			  (bet_vols, uncor_mm,   [('out_file', 'mmInputnode.run_list')]),
		   ])
    preProc.connect([	  (moco_vols, rename,    [('out_file', 'in_file')]),
		   ])

  preProc.connect([	    (inputnode, rename,    [('abs_run_id', 'run_id')]),
			    (rename, datasink,     [('out_file', 'final_aligned')]),
			    (uncor_mm, datasink,   [('merge.merged_file', 'uncorrected_movie')]),			##send everything to data sink
			    (cor_mm, datasink,     [('merge.merged_file', 'corrected_movie')]),
			    (bet_vols, datasink,   [(('mask_file', grab_first), 'brain_mask')])

		 ])

  return preProc