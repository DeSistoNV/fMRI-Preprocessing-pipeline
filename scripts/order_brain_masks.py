import os
import glob
import sys
import pprint
fileList = []
rootdir = [
'COlotusHill.7T.em9K.1x1/mocoresults/',             \
'DMlotusHill.7T.em9K.1.5iso/mocoresults/',  	 \
'MYlotusHill.7T.em9K.1.5iso/mocoresults/',	 	 \
'PHILlotusHill.7T.em9K.1.5iso/mocoresults/',	 \
'KHlotusHill.7T.em6K.hires/mocoresults/',	 	 \
'KHlotusHill.7T.em9K.1x1/mocoresults/', 		 \
'MKlotusHill.7T.em9K.1x1/mocoresults/',		 \
'MPlotusHill.7T.em9K.1x1/mocoresults/',	  	 \
'QClotusHill.7T.em9K.1x1/mocoresults/',		 \
'TNlotusHill.7T.em9K.1.5iso/mocoresults/',		 \
'TNlotusHill.7T.em9K.1x1/mocoresults/',	         \
'TNlotusHill.7T.em9K.1x1_second_round/mocoresults/', \
'PHILlotusHill.7T.em9K.1.5iso_first_try/mocoresults/', \
'COlotusHill.7T.em9K.1.5iso/mocoresults/' \
]

for ii,jj in enumerate(rootdir):
  rootdir[ii] = '/Data/7T.cmrr/workingvols/'+jj

print "unzipping all the files"
for experiments in rootdir:
  fl = glob.glob(experiments+'brain_mask/_bet_vols0/*')
  #print fl
  os.system("sudo gunzip "+fl[0])

for experiments in rootdir:
  for root, subFolders, files in os.walk(experiments+'final_aligned'):
      for file in files:
	  fileList.append((os.path.join(root,file), glob.glob(experiments+'brain_mask/_bet_vols0/*.nii')))
fileList.sort(key = lambda run: run[0][-9:])

for fl in fileList:
  print ''.join(fl[1])

