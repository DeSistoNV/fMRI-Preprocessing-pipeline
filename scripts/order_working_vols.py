#import os
#import sys
#import pprint
#fileList = []
#rootdir = sys.argv[1]
#for root, subFolders, files in os.walk(rootdir):
    #for file in files:
	#fileList.append(os.path.join(root,file))
#fileList.sort(key = lambda run: run[-12:])
#print '\n'.join(fileList)

import os
import sys
import pprint
fileList = []
rootdir = [
'COlotusHill.7T.em9K.1x1/mocoresults/final_aligned',             \
'DMlotusHill.7T.em9K.1.5iso/mocoresults/final_aligned',  	 \
'MYlotusHill.7T.em9K.1.5iso/mocoresults/final_aligned',	 	 \
'PHILlotusHill.7T.em9K.1.5iso/mocoresults/final_aligned',	 \
'KHlotusHill.7T.em6K.hires/mocoresults/final_aligned',	 	 \
'KHlotusHill.7T.em6K.hires_fnirt/mocoresults/final_aligned',	 \
'KHlotusHill.7T.em9K.1x1/mocoresults/final_aligned', 		 \
'MKlotusHill.7T.em9K.1x1/mocoresults/final_aligned',		 \
'MPlotusHill.7T.em9K.1x1/mocoresults/final_aligned',	  	 \
'QClotusHill.7T.em9K.1x1/mocoresults/final_aligned',		 \
'TNlotusHill.7T.em9K.1.5iso/mocoresults/final_aligned',		 \
'TNlotusHill.7T.em9K.1x1/mocoresults/final_aligned',	         \
'TNlotusHill.7T.em9K.1x1_second_round/mocoresults/final_aligned',   \
'PHILlotusHill.7T.em9K.1.5iso_first_try/mocoresults/final_aligned', \
'COlotusHill.7T.em9K.1.5iso/mocoresults/final_aligned'
]
for ii,jj in enumerate(rootdir):
  rootdir[ii] = '/Data/7T.cmrr/workingvols/'+jj

#for experiments in rootdir:
  #for root, subFolders, files in os.walk(experiments):
      #for file in files:
	  #fileList.append(os.path.join(root,file))

###for unzipping if needed
#print "unzipping all the files"
#for flz in fileList:
  #os.system("sudo gunzip "+flz)
  
for experiments in rootdir:
  for root, subFolders, files in os.walk(experiments):
      for file in files:
	  fileList.append(os.path.join(root,file))
fileList.sort(key = lambda run: run[-9:])
print '\n'.join(fileList)