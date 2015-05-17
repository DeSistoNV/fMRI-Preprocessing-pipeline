""" Interface which runs FSL's BET on a database of 4D fMRI Nifti files
	1. take mean of each 4D files
	2. run BET at different fractional intensity thesholds
	3. convert each Nifti to a .gif 
"""
import tempfile, shutil, os, sys, subprocess
import pandas as pd
from PyQt4 import QtGui, QtCore

# fracs with which to run 
list = False
if list:
	fracs = [0.05,0.075,0.1,0.125,0.15,0.175,0.2,0.225,0.25,0.275,0.3,0.325,0.35,0.375,0.4,0.425,0.45,0.475,0.5]
	fracs = [.1,.2,.3]
else:
	fracs = [i / 1000.0 for i in xrange(25,525,10)]

# directory of first file
direct = '/tmp/bet_view_0/'

# creating main window
app = QtGui.QApplication(sys.argv)
main_window = QtGui.QWidget()
main_window.setGeometry(200, 100, 1000,600)
main_window.setWindowTitle('BET FRACTIONAL INTENSITY VIEWER')

# input for file name of CSV file
file_name = QtGui.QLineEdit(main_window)
file_name.setGeometry(0,0,500,20)
file_name.setText('Path to CSV goes here')
file_name.setText('/musc.repo/Data/nickdesisto/3T.v.7T/Databii/res1.csv')

# button that starts the processing
file_button = QtGui.QPushButton('load',main_window)
file_button.setGeometry(600,1,50,20)

# file browse button
diag_button = QtGui.QPushButton('browse',main_window)
diag_button.setGeometry(520,1,60,20)
def selectFile():
    file_name.setText(QtGui.QFileDialog.getOpenFileName())
diag_button.clicked.connect(selectFile)

# slider to change current frac displayed
slider_frac = QtGui.QSlider(QtCore.Qt.Horizontal, main_window)
slider_frac.setGeometry(10, 500, 980, 15)
slider_frac.setFocusPolicy(QtCore.Qt.NoFocus)
slider_frac.setRange(0,len(fracs))

# slider to change current file displayed
slider_run = QtGui.QSlider(QtCore.Qt.Horizontal, main_window)
slider_run.setGeometry(10, 525, 980, 15)
slider_run.setFocusPolicy(QtCore.Qt.NoFocus)
slider_run.setRange(0,6)

# labels displaying current slider position
label_run = QtGui.QLabel('runID : 0',main_window)
label_run.setGeometry(875,500,100,100)
label_frac = QtGui.QLabel('BET FRAC: 0',main_window)
label_frac.setGeometry(875,525,150,100)

# progress bar for when files are being processed
prog_bar = QtGui.QProgressBar(main_window)
prog_bar.setMinimum(0)
prog_bar.setGeometry(275,550,450,25)
prog_bar.setValue(0)
prog_bar.hide()

# display element for the gif images
pic = QtGui.QLabel(main_window)
pic.setGeometry(0, 50, 1000,450)
pic.setPixmap(QtGui.QPixmap('{}0.png'.format(direct)))
pic.setScaledContents(True)

# changes frac
def set_pic_frac(value):
	if value == 0:
		pic.setPixmap(QtGui.QPixmap('{}{}.png'.format(direct,0)))
		label_frac.setText('BET FRAC: {}'.format(0))
	else:
		pic.setPixmap(QtGui.QPixmap('{}{}bet.png'.format(direct,fracs[value-1])))
		label_frac.setText('BET FRAC: {}'.format(fracs[value-1]))
	print direct
main_window.connect(slider_frac, QtCore.SIGNAL('valueChanged(int)'), set_pic_frac)

# changes run
def set_pic_run(value):
	global direct
	direct = '/tmp/bet_view_{}/'.format(value)
	set_pic_frac(slider_frac.value())
	label_run.setText('runID : {}'.format(value))
main_window.connect(slider_run, QtCore.SIGNAL('valueChanged(int)'), set_pic_run)


class process_files(QtCore.QThread):

	def __init__(self):
		QtCore.QThread.__init__(self)
		self.that = QtGui.QWidget()
		self.count = QtGui.QSpinBox(self.that)
		self.count.hide()

	def run(self):

		db = str(file_name.text())
		df = pd.read_csv(db,index_col = False)
		slider_run.setRange(0,len(df.index)-2 )
		iters = len(fracs) * len(fracs) * len(df.index) + len(df.index)
		prog_bar.setMaximum(iters)
		step = 0
		self.count.setMaximum(iters)
		del iters

		files = [(df.run_path[i]  + '/' + df.run_data_file[i],df.runID[i]) for i in xrange(len(df.index) -1)]
		print files
		tmp_files = []
		print 'copying files...'
		for f in files:
			tmp_path = '/tmp/bet_view_{}/'.format(f[1])
			if not os.path.exists(tmp_path):
				os.makedirs(tmp_path)
			ld = [i for i in os.listdir(f[0]) if '.nii' in i].pop()
			nii = f[0] + '/' + ld
			print 'running : cp {} {}'.format(nii,tmp_path)
			if not os.path.isfile(tmp_path + ld):
				shutil.copy2(nii , tmp_path)
			tmp_files.append((tmp_path + ld,f[1]))
			step += 1
			self.count.setValue(step)
		for f in tmp_files:
			this_path = '/tmp/bet_view_{}/'.format(f[1])
			this_mean = this_path + '0.nii.gz'
			cmd_mean = 'fslmaths {} -Tmean {}'.format(f[0],this_mean)
	 		print 'running : {}'.format(cmd_mean)
			subprocess.call(cmd_mean,shell=True)
			step +=1
			self.count.setValue(step)
			os.remove(f[0])
			print 'running : rm {}'.format(f[0])
			for frac in fracs:
	 			cmd_bet = 'bet {} {}{}bet.nii.gz -f {}'.format(this_mean,this_path,str(frac),str(frac))
	 			print 'running : {}'.format(cmd_bet)
	 			subprocess.call(cmd_bet,shell=True)
	 			step +=1
	 			self.count.setValue(step)
	 		print 'running : rm {}'.format(this_mean)

	 		bets = ['{}{}'.format(this_path,i) for i in os.listdir(this_path) if '.nii' in i]
	 		for image in bets:
				cmd_pic = 'slicer -s 4 {} -a {}.png'.format(image,image[:-7])
				print 'running : {}'.format(cmd_pic)
				subprocess.call(cmd_pic,shell=True)
				step += 1
				self.count.setValue(step)
				os.remove(image)
				print 'running : rm {}'.format(image)

main_window.pipe = process_files()

def file_button_action():
	if os.path.isfile(file_name.text()):
		main_window.pipe.start()
	else:
		print 'file not found'

file_button.clicked.connect(file_button_action)
main_window.pipe.finished.connect(prog_bar.hide)
main_window.pipe.started.connect(prog_bar.show)
main_window.pipe.count.valueChanged.connect(prog_bar.setValue)

main_window.show()
sys.exit(app.exec_())

