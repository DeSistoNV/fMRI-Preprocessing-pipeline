# Nick DeSisto
# 11.16.14
# graphical user interface for creating a database of Nifti fMri files.
import sys
import os
from datetime import datetime
from collections import OrderedDict

from PyQt4 import QtGui
from PyQt4 import QtCore
import pandas as pd
import psutil





## 1.0 - 11.20.2014 - first working copy
## 1.0.1 - added fields for working volume and brain mask
## 1.1 - resized main window
##     - removed pickling for simplicity
##     -rounded voxel size
## 1.1.1
## 2.25.2015
##      - added tabbed interface for possible expansion
## 2.0
## 2.25.2015
##      - added pipeline

class NoFileNameError(Exception):
    pass


class SiemensRefValueError(Exception):
    pass


class NoValuesEnteredError(Exception):
    pass


class FileAlreadyExistsError(Exception):
    pass


class DirectoryDoesntExistError(Exception):
    pass


class NoFilesAddedError(Exception):
    pass

class NoTxtError(Exception):
    pass

""" constructs a list of all .nii files in directory"""
def grab_directory(directory):
    if os.path.isdir(directory):
        files = []

        for directory2 in os.listdir(directory):
            sub_files = os.listdir(directory + directory2)
            for ff in sub_files:
                if ff.find('.txt') == -1:
                    files.append(directory2 + '/' + ff)
        return files

class EmittingStream(QtCore.QObject):

    textWritten = QtCore.pyqtSignal(str)

    def write(self, text):
        self.textWritten.emit(str(text))

class ParsingTab(QtGui.QWidget):
    def __init__(self,):
        super(ParsingTab, self).__init__()

        self.csvLabel = QtGui.QLabel("Full path to save the CSV file:",self)
        self.csvLabel.move(300,755)
        self.usedNames = []  # list for checking if a file has already been added
        self.rows = []  # stack of files to be added to database
        self.autoFiles = []  # Stack of parsed files
        self.yIncrement = 25  # constant for input and label placement
        self.tableObjects = []  # list of files in table

        self.append_order_list = ['date', 'subject', 'experiment', 'working_vol', 'brain_mask', 'sessionID',
                                  'runType',
                                  'design matrix', 'frame_file', 'run_data_file', 'nvols', 'tesla', 'location',
                                  'run_path', 'TR', 'matrix_x', 'matrix_y', 'n_slices', 'vox_x', 'vox_y', 'vox_z',
                                  'run_code_path', 'run_code_file', 'design_matrix_path', 'frameFilePath', 'picPath',
                                  'siemensRef', 'padVol']

        # message printed upon opening
        self.open_message = datetime.now().strftime(
            "%I:%M:%S %p") + '<html><br>NII Parsing and database creation tool.<br><b>1</b>. Input ' \
                             'path of the directory in "main path" to search for .nii files I.E. "/home/Naselaris_TN/"<br><b>2</b>. Press get files Button' \
                             '<br><b>3</b>. Fill in the blanks and press add file<br>' \
                             '<b>4</b>. When you are done adding files in the current directory, press next path and enter the new path you would like to parse<br>' \
                             '<b>5</b>. Enter output file name with no file extension and press data structure of ' \
                             'choice to save<br><b>NOTE: You can view data in files already added but changes will ' \
                             'not be saved</b><br><br>'
        self.parseTableObjects = []

        self.setStyleSheet('QLineEdit {'
                           'background : rgba(255,255,255,55%); '
                           'color : "black";'
                           '}'
                           'QListWidget {'
                           'background : rgba(255,255,255,55%)'
                           '}'
                           "QTextEdit {"
                           'background : rgba(255,255,255,55%)'
                           '}'
        )  # setting opacity of all entry fields

        self.Inputs = dict()
        self.Labels = dict()
        self.InputLabels = ['main path', 'date', 'subject', 'experiment', 'sessionID', 'runType',
                            'design matrix', 'frame_file', 'run_data_file', 'nvols', 'tesla', 'location',
                            'run_path', 'TR', 'run_code_path', 'run_code_file', 'design_matrix_path', 'picPath',
                            'frameFilePath',
                            'siemensRef', 'padVol', 'matrix', 'voxels']
        self.inputsToolTips = ['I.E. /user/nick/Naselaris_TN', 'date when data was collected', 'initials for subject',
                               'some kind of code for the experiment the run',
                               'a collection of runs done without pulling the subject',
                               'often an experiment has different run types', ' filename for design matrix',
                               'filename for the file that shows how to interpret',
                               'the name of FOLDER where the raw data lives.',
                               'number of volumes in the run (ie. number of TRs', '3T, 7T, etc.',
                               'where did you collect the data?', 'the full pathname pointing to the folder specified',
                               'the experimental TR',
                               'path to script for running exp. (python, psychtoolbox, psychopy, eprime, etc.)',
                               'filename of script for running exp', ' full path to design matrix',
                               'full path to frame_file',
                               'full path to stimulus files (e.g., tiffs for pictures, .wav for auditory, etc.)',
                               'was Siemens ref volume included as first volume in sequence? 0 or 1',
                               ' did scan fail before collecting the # of TRs specified in nvols? enter # missing vols '
                               'here.']
        for i in range(len(self.InputLabels)):
            if i < self.InputLabels.index('matrix'):
                self.Inputs[self.InputLabels[i]] = QtGui.QLineEdit(self)
                self.Inputs[self.InputLabels[i]].move(125, self.yIncrement + self.yIncrement * i)
                self.Inputs[self.InputLabels[i]].resize(250, 23)
            self.Labels[self.InputLabels[i]] = QtGui.QLabel(self.InputLabels[i], self)
            self.Labels[self.InputLabels[i]].setAlignment(QtCore.Qt.AlignRight)
            self.Labels[self.InputLabels[i]].move(4, self.yIncrement + self.yIncrement * i + 4)
            self.Labels[self.InputLabels[i]].resize(118,25)
            self.Labels[self.InputLabels[i]].lower()

        for i in range(len(self.inputsToolTips)):
            self.Inputs[self.InputLabels[i]].setToolTip(self.inputsToolTips[i])

        self.MatrixLabels = ['matrix_x', 'matrix_y', 'n_slices', 'vox_x', 'vox_y', 'vox_z']
        self.MatrixToolTips = ['number of voxels along rows', 'number of voxels along cols',
                               'number of slices per volume',
                               'voxel dimensions in mm', 'voxel dimensions in mm', 'slice thickness']
        for i in range(3):
            self.Inputs[self.MatrixLabels[i]] = QtGui.QLineEdit(self)
            self.Inputs[self.MatrixLabels[i]].move(125 + 90 * i, self.yIncrement + self.yIncrement * 21)
            self.Inputs[self.MatrixLabels[i]].resize(70, 23)
            self.Inputs[self.MatrixLabels[i]].setToolTip(self.MatrixToolTips[i])
            self.Inputs[self.MatrixLabels[i + 3]] = QtGui.QLineEdit(self)
            self.Inputs[self.MatrixLabels[i + 3]].move(125 + 90 * i, self.yIncrement + self.yIncrement * 22)
            self.Inputs[self.MatrixLabels[i + 3]].resize(70, 25)
            self.Inputs[self.MatrixLabels[i + 3]].setToolTip(self.MatrixToolTips[i + 3])

        # # LABELS AND INPUTS ARE BOTH IN DICTS BY THEIR LABEL NAME HERE
        self.table = QtGui.QListWidget(self)
        self.table.resize(270, 575)
        self.table.move(380, 25)

        self.tableLabel = QtGui.QLabel('<html><b>FILES CURRENTLY ADDED</b></html>', self)
        self.tableLabel.move(400, 10)
        self.table.currentItemChanged.connect(self.view_file)

        self.parse_table = QtGui.QListWidget(self)
        self.parse_table.resize(340, 575)
        self.parse_table.move(655, 25)

        self.parseLabel = QtGui.QLabel('<html><b>PARSED FILES READY TO ENTER</b></html>', self)
        self.parseLabel.move(750, 10)
        self.parse_table.currentItemChanged.connect(self.select_parse_file)

        self.csvLabel = QtGui.QLabel("Full path to save the CSV file:",self)
        self.csvLabel.move(300,755)

        self.outputInput = QtGui.QLineEdit(self)
        self.outputInput.move(485, 750)
        self.outputInput.resize(400, 25)
        self.outputInput.setToolTip('Enter path to export here')

        self.unAddButton = QtGui.QPushButton('un-add', self)
        self.unAddButton.move(495, 600)
        self.unAddButton.clicked.connect(self.un_add)
        self.unAddButton.setToolTip('select an item from the added list and press to un-add')

        self.nextPathButton = QtGui.QPushButton('next path',self)
        self.nextPathButton.move(250,600)
        self.nextPathButton.clicked.connect(self.next_path)
        self.nextPathButton.setToolTip('clear currently unappended filed and allow a new directory to be parsed')

        self.dirButton = QtGui.QPushButton('get files', self)
        self.dirButton.clicked.connect(self.create_auto_list)
        self.dirButton.move(20, 600)
        self.dirButton.setToolTip('Find all .nii files in current directory')

        self.addButton = QtGui.QPushButton('Add File', self)
        self.addButton.clicked.connect(self.file_append)
        self.addButton.move(780, 600)
        self.addButton.setToolTip('Add current file to stack')

        self.pandaButton = QtGui.QPushButton('export to CSV', self)
        self.pandaButton.clicked.connect(self.pickle_panda)
        self.pandaButton.move(890, 750)
        self.pandaButton.resize(100, 25)
        self.pandaButton.setToolTip('Output to Pickled Pandas DataFrame and CSV file')

        self.test_vals()

        self.message = QtGui.QTextEdit(self)
        self.message.setReadOnly(True)
        self.message.move(5, 625)
        self.message.resize(990, 120)
        self.message.append(self.open_message)
        self.message.moveCursor(QtGui.QTextCursor.End)


    def next_path(self):
        try:
            self.dirButton.setEnabled(True)
            self.addButton.setEnabled(False)
            self.parse_table.clear()
            self.Inputs['main path'].setEnabled(True)

        except AttributeError:
            self.message.append('ready for next directory')
    # adding functionality of editing files
    def view_file(self):
        # this is now a parse file button and needs to be integrated into table
        try:
            filep = str(self.table.currentItem().text()) # this is the selected top dir
            for row in self.rows:
                if filep[10:] in row['run_data_file']: # check first 10 chars for match
                    for word in self.append_order_list:
                        if word in self.Inputs.keys():
                            self.Inputs[word].setText(row[word])
        except AttributeError:
            self.Inputs['run_data_file'].setText('')


    # Action for the un_add button
    def un_add(self):
        try:
            text = self.table.currentItem().text()
            self.table.takeItem(self.table.currentRow())
            self.rows = [row for row in self.rows if row['run_data_file'].find(text[:10]) == -1]
            self.usedNames = [name for name in self.usedNames if name.find(text[:10]) == -1]

            self.parseTableObjects.append(QtGui.QListWidgetItem(text))
            self.parse_table.addItem(self.parseTableObjects[len(self.parseTableObjects) - 1])

        except AttributeError:
            self.message.append('<html><font color = "red">Error: No Item Selected</font><brb></html>')
            self.message.moveCursor(QtGui.QTextCursor.End)

    """ action for test values button """

    def test_vals(self):
        self.Inputs['run_code_path'].setText('')
        self.Inputs['main path'].setText('/musc.repo/')
        self.Inputs['experiment'].setText('imagery.rf')
        self.Inputs['sessionID'].setText('1')
        self.Inputs['design matrix'].setText('design_matrix.npy')
        self.Inputs['location'].setText('The Moon')
        self.Inputs['TR'].setText('2')
        self.Inputs['run_code_file'].setText('run_experiment.py')
        self.Inputs['design_matrix_path'].setText('/musc.repo/')
        self.Inputs['frameFilePath'].setText('/musc.repo/')
        self.Inputs['picPath'].setText('/musc.repo/')
        self.Inputs['siemensRef'].setText('0')
        self.Inputs['padVol'].setText('0')
#        self.button.deleteLater()

    # Action for all of em button ;processing grab_directory output
    def create_auto_list(self):
        path = str(self.Inputs['main path'].text())
        if path[len(path) - 1:] != '/':
            path += '/'

        if os.path.isdir(path) and path != '/':
            self.autoFiles = grab_directory(path)
            self.Inputs['main path'].setText(path)
            if len(self.autoFiles) != 0:
                self.dirButton.setDisabled(True)

            for f in self.autoFiles:
                if 'SBRef' not in f and 'localizer' not in f and 'FieldMap' not in f and 'phaseencode' not in f:
                    self.parseTableObjects.append(QtGui.QListWidgetItem(f.split('/')[0]))
                    self.parse_table.addItem(self.parseTableObjects[len(self.parseTableObjects) - 1])
            self.message.append(str(len(self.parseTableObjects)) + ' .nii files found')

            self.Inputs['main path'].setDisabled(True)
            self.addButton.setEnabled(True)

        else:
            self.message.append('<html><font color = "red">THIS DIRECTORY DOES NOT EXIST</font><brb></html>')
        self.message.moveCursor(QtGui.QTextCursor.End)

    # action for next file button
    def select_parse_file(self):
        # self.autofiles is list of top/f.nii

        file_p = str(self.parse_table.currentItem().text())
        for auto_file in self.autoFiles:
            if auto_file.find(file_p[:10]) != -1:
                parse_path = str(self.Inputs['main path'].text()) + auto_file[:-4] + '_info.txt'
                break

        try:

            if not os.path.isfile(parse_path):
                raise NoTxtError()
            if not parse_path:
                raise NoFilesAddedError()
            infile = open(parse_path, 'r')  # opening .txt file




            raw_data = [line[:-1] for line in infile if ord('A') <= ord(line[0]) <= ord('Z')]

            # we now have a list of each line in the file
            parameters = []
            values = []

            # splits file and makes a list of keys and values
            for data in raw_data:
                data = data.split(':')
                parameters.append(data[0])
                values.append(data[1])

            # matches the keys and values in a dict
            parse = dict(zip(parameters, values))
            self.Inputs['date'].setText(parse['Study date'][7:] + '/' + parse['Study date'][5:7] + '/' +
                                        parse['Study date'][1:5])
            self.Inputs['subject'].setText(parse['Subject'].split('^')[1])
            rd = parse_path.find('run')
            self.Inputs['runType'].setText(parse_path[rd + 3:rd + 7])
            self.Inputs['frame_file'].setText(self.Inputs['runType'].text()[1:] + '_frame_list.txt')
            step = parse_path[:parse_path.rfind('/')]
            step2 = step[step.rfind('/'):].replace('/', '')
            self.Inputs['run_data_file'].setText(step2)
            self.Inputs['nvols'].setText(parse['Number of volumes'].strip())
            self.Inputs['tesla'].setText(parse['Model name'][-2:])
            self.Inputs['run_path'].setText(self.Inputs['main path'].text())
            try:
                self.Inputs['matrix_x'].setText(parse['Mosaic columns'])
                self.Inputs['matrix_y'].setText(parse['Mosaic rows'])
                self.Inputs['n_slices'].setText(parse['Number of slices'])
            except KeyError:
                self.Inputs['matrix_x'].setText('')
                self.Inputs['matrix_y'].setText('')
                self.Inputs['n_slices'].setText('')
                self.message.append('<html><font color = "red">Error: Unable to parse matrix dimensions<br></font></html>')
            self.Inputs['vox_x'].setText(str(round(float(parse['Voxel size x (mm)']),2)))
            self.Inputs['vox_y'].setText(str(round(float(parse['Voxel size y (mm)']),2)))
            self.Inputs['vox_z'].setText(str(round(float(parse['Slice thickness (mm)']),2)))
        except IOError:
            self.message.append(
                    '<html><font color = "red">ERROR: no suck file or directory - '
                    + file_p + '<br></font></html>')
        except NoFilesAddedError:
            self.message.append("<html><font color = 'red'><b>Error @ parse_path in select_parse_file: "
                                "something happened that really shouldn't've happened...</b></font><br></html>")
        except NoTxtError:
            self.message.append("<html><font color = 'red'><b>Error: No Txt file found. Could not parse any parameters.</b></font><br></html>")
            self.Inputs['date'].setText('')
            self.Inputs['subject'].setText('')
            self.Inputs['runType'].setText('')
            self.Inputs['frame_file'].setText('')
            self.Inputs['nvols'].setText('')
            self.Inputs['tesla'].setText('')
            self.Inputs['run_path'].setText('')
            self.Inputs['matrix_x'].setText('')
            self.Inputs['matrix_y'].setText('')
            self.Inputs['n_slices'].setText('')
            self.Inputs['vox_x'].setText('')
            self.Inputs['vox_y'].setText('')
            self.Inputs['vox_z'].setText('')
        finally:
            self.message.moveCursor(QtGui.QTextCursor.End)

    """ outputs to a pickled panda """

    def pickle_panda(self):

        import pandas as pd

        try:
            out = str(self.outputInput.text())  # input field
            test = out[:out.rfind('/')]  # slice the bottom directories
            out += '.p'  # add pickle extension
            if not os.path.isdir(test):
                raise DirectoryDoesntExistError()
            if os.path.isfile(out):
                raise FileAlreadyExistsError()
            if len(self.rows) < 1:
                raise NoFilesAddedError()
            keys = [key for key in self.rows[0]]
            data = [tuple(row[key] for key in row) for row in self.rows]
            s = pd.DataFrame(data=data, columns=keys)
            s.index.name = 'runID'
            pd.to_pickle(s, str(self.outputInput.text()) + '.p')
            # self.message.append(
            #     '<html><font color = "green"><b>---------- PANDA PICKLED TO ' + str(
            #         self.outputInput.text()) + '.p' + '---------</b><br></font></html>')
            s.to_csv(str(self.outputInput.text()) + '.csv',columns=s[1:])
            self.message.append(
                '<html><font color = "green"><b>--------CSV saved to ' + str(
                    self.outputInput.text()) + '.csv' + ' ---------</b></font><br></html>')
        except IOError:
            self.message.append('<html><font color = "red">Error: permission to directory denied<br></font></html>')
        except NoFilesAddedError:
            self.message.append('<html><font color = "red">Error: No files added yet<br></font></html>')
        except FileAlreadyExistsError:
            self.message.append('<html><font color = "red">Error: file ' + out + ' Already exists<br></font></html>')
        except DirectoryDoesntExistError:
            # noinspection PyUnboundLocalVariable
            self.message.append(
                '<html><font color = "red">Error: File Path -  ' + test + ' Does not exist.<br></font></html>')
        finally:
            self.message.moveCursor(QtGui.QTextCursor.End)


    """ outputs to a comma separated values file """

    """ add file to stack """
    def file_append(self):
        try:
            if str(self.Inputs['siemensRef'].text()) != '1' and str(self.Inputs['siemensRef'].text()) != '0':
                raise SiemensRefValueError('siemensRef must be either 1 or 0')
            if str(self.Inputs['vox_x'].text()) == '' or str(self.Inputs['matrix_x'].text()) == '':
                raise NoValuesEnteredError('missing values')
            if str(self.Inputs['main path'].text()) == '' or str(self.Inputs['run_path'].text()) == '':
                raise NoFileNameError('no file name entered')

            file_p = str(self.parse_table.currentItem().text())
            if file_p in self.usedNames:
                raise FileAlreadyExistsError('file already exists')

            self.tableObjects.append(QtGui.QListWidgetItem(file_p))

            row = OrderedDict()
            # row['runID'] = str(int(file_p[2:5]))
            for key in self.append_order_list:  # for each param in the order list
                if key in self.Inputs.keys():  # if key is in Inputs set to value
                    row[key] = str(self.Inputs[key].text())
                else:       # else empty
                    row[key] = ''
            self.rows.append(row)


            self.table.addItem(self.tableObjects[len(self.tableObjects) - 1])
            self.parse_table.takeItem(self.parse_table.currentRow())

            self.usedNames.append(file_p)
            if len(self.autoFiles) == 1:
                # self.nextFileButton.setDisabled(True)
                self.dirButton.setDisabled(False)
        except NoFileNameError:
            self.message.append('<html><font color = "red">Error: No file Name Entered</font><br></html>')
        except FileAlreadyExistsError:
            self.message.append('<html><font color = "red">Error: This File is already added</font><br></html>')
        except NoValuesEnteredError:
            self.message.append('<html><font color = "red">Error: Missing Values</font><br></html>')
        except SiemensRefValueError:
            self.message.append(
                '<html><font color = "red">Error: File not Added: siemensRef must be either 1 or 0</font><brb></html>')
        finally:
            self.message.moveCursor(QtGui.QTextCursor.End)


class PipeTab(QtGui.QWidget):
    def __init__(self,parent):
        super(PipeTab, self).__init__()
        self.setStyleSheet('QLineEdit {'
                           'background : rgba(255,255,255,55%); '
                           'color : "black";'
                           '}'
                           'QListWidget {'
                           'background : rgba(255,255,255,55%)'
                           '}'
                           "QTextEdit {"
                           'background : rgba(255,255,255,55%)'
                           '}')

        self.Inputs = dict()
        self.Labels = dict()

        options_x = 900



        # top left label "options
        self.optionsLabel = QtGui.QLabel('<html><b>Options</b></html>',self)
        self.optionsLabel.move(options_x,12)



        self.dbInput = QtGui.QLineEdit(self)
        self.dbInput.setText('/home/nick/Desktop/MUSC/2sessions.csv')
        self.dbInput.resize(250,23)
        self.dbInput.move(80,8)

        self.dbLabel = QtGui.QLabel('Database',self)
        self.dbLabel.resize(120,25)
        self.dbLabel.move(15,12)


        self.subjectDrop = QtGui.QComboBox(self)
        self.subjectDrop.resize(250,25)
        self.subjectDrop.move(180,50)

        self.subjectLabel = QtGui.QLabel('Subject',self)
        self.subjectLabel.resize(60,25)
        self.subjectLabel.move(120,52)


        self.expDrop = QtGui.QComboBox(self)
        self.expDrop.resize(250,25)
        self.expDrop.move(180,80)


        self.dicomBool = QtGui.QComboBox(self)
        self.dicomBool.resize(95,20)
        self.dicomBool.move(options_x,35)
        self.dicomBool.addItem("No")

        self.dicomBool.addItem("Yes")
        self.dicomLabel = QtGui.QLabel('convert dicoms',self)
        self.dicomLabel.move(800,35)
        self.dicomLabel.resize(100,20)


        self.fnirt_box = QtGui.QComboBox(self)
        self.fnirt_box.resize(95,20)
        self.fnirt_box.move(options_x,60)
        self.fnirt_box.addItem('spline')
        self.fnirt_box.addItem('nearestneighbour')
        self.fnirt_box.addItem('trilinear')
        self.fnirt_box.addItem('sinc')

        fnirt_option = QtGui.QLabel('FNIRT interpolation method',self)
        fnirt_option.move(730,60)
        fnirt_option.resize(170,20)


        self.flirt_box = QtGui.QComboBox(self)
        self.flirt_box.resize(95,20)
        self.flirt_box.move(options_x,135)
        self.flirt_box.addItem('sinc')
        self.flirt_box.addItem('nearestneighbour')
        self.flirt_box.addItem('trilinear')
        self.flirt_box.addItem('spline')

        flirt_option = QtGui.QLabel('FLIRT interpolation method',self)
        flirt_option.move(730,137)
        flirt_option.resize(170,20)


        cfnirt_option = QtGui.QLabel('flirt COST function',self)
        cfnirt_option.move(782,162)
        cfnirt_option.resize(130,20)

        self.cflirt_box = QtGui.QComboBox(self)
        self.cflirt_box.resize(95,20)
        self.cflirt_box.move(options_x,158)
        self.cflirt_box.addItem('normcorr')

        self.cflirt_box.addItem('mutualinfo')
        self.cflirt_box.addItem('corratio')
        self.cflirt_box.addItem('normii')
        self.cflirt_box.addItem('leastsq')
        self.cflirt_box.addItem('labeldiff')
        self.cflirt_box.addItem('bbr')


        self.dfnirt_box = QtGui.QComboBox(self)
        self.dfnirt_box.resize(95,20)
        self.dfnirt_box.move(options_x,85)
        self.dfnirt_box.addItem('Yes')
        self.dfnirt_box.addItem('No')

        dfnirt_option = QtGui.QLabel('Do FNIRT?',self)
        dfnirt_option.move(830,85)
        dfnirt_option.resize(70,20)






        self.rigid2dflirt = QtGui.QComboBox(self)
        self.rigid2dflirt.resize(95,20)
        self.rigid2dflirt.move(options_x,180)
        self.rigid2dflirt.addItem('No')

        self.rigid2dflirt.addItem('Yes')

        rigid2dflirt_label = QtGui.QLabel('Rigid 2D Flirt?',self)
        rigid2dflirt_label.move(810,182)
        rigid2dflirt_label.resize(100,20)


        self.moco_only = QtGui.QComboBox(self)
        self.moco_only.resize(95,20)
        self.moco_only.move(options_x,210)
        self.moco_only.addItem('No')
        self.moco_only.addItem('Yes')

        moco_label = QtGui.QLabel('Motion Correction Only?',self)
        moco_label.move(750,212)
        moco_label.resize(150,20)


        self.dof_flirt = QtGui.QComboBox(self)
        self.dof_flirt.resize(95,20)
        self.dof_flirt.move(options_x,240)
        for i in range(1,13):
            self.dof_flirt.addItem(str(i))

        dof_flirt_label = QtGui.QLabel('Degrees of Freedom(Flirt)',self)
        dof_flirt_label.move(740,242)
        dof_flirt_label.resize(155,20)


        self.cpucount = QtGui.QComboBox(self)
        for i in range(1,psutil.cpu_count()+1):
            self.cpucount.addItem(str(i))
        self.cpucount.move(options_x,110)
        self.cpucount.resize(95,20)

        self.cpucount_label = QtGui.QLabel("# of cpus to use",self)
        self.cpucount_label.move(800,112)


        self.bet_input = QtGui.QLineEdit(self)
        self.bet_input.move(options_x,265)
        self.bet_input.resize(93,20)
        self.bet_input.setText('.5')

        self.bet_label = QtGui.QLabel("BET fractional intensity threshold",self)
        self.bet_label.move(698,268)

        self.t_size_input = QtGui.QLineEdit(self)
        self.t_size_input.move(options_x,295)
        self.t_size_input.resize(93,20)
        self.t_size_input.setText('10000')

        self.t_size_label = QtGui.QLabel("Max Possible Size")
        self.t_size_label.move(698,300)


        self.base_dir = QtGui.QFileDialog(self)
        self.base_dir.setFileMode(QtGui.QFileDialog.DirectoryOnly)

        self.results_con_input = QtGui.QLineEdit(self)
        self.results_con_input.move(185,172)
        self.results_con_input.resize(230,22)
        self.results_con_input.setText('Results')


        self.base_dir_label = QtGui.QLabel('results container',self)
        self.base_dir_label.move(80,178)




        self.base_dir_input = QtGui.QLineEdit(self)
        self.base_dir_input.move(185,112)
        self.base_dir_input.resize(230,22)

        self.base_dir_button = QtGui.QPushButton('browse',self)
        self.base_dir_button.move(420,112)
        self.base_dir_button.resize(60,20)
        self.base_dir_button.clicked.connect(self.base_dir_act)

        self.base_dir_label = QtGui.QLabel('intermediate dump directory',self)
        self.base_dir_label.move(5,118)

        self.results_dir_input = QtGui.QLineEdit(self)
        self.results_dir_input.move(185,140)
        self.results_dir_input.resize(230,22)


        self.results_dir_button = QtGui.QPushButton('browse',self)
        self.results_dir_button.move(420,142)
        self.results_dir_button.resize(60,20)
        self.results_dir_button.clicked.connect(self.results_dir_act)

        self.results_dir_label = QtGui.QLabel('results dump directory',self)
        self.results_dir_label.move(40,144)



        self.InputLabels = ['experiment','Run List(Leave Blank for all)','Session List(Leave Blank for all)','crop this',


                                    'FNIRT subsampling scheme (4 ints)','FNIRT warp resolution',  'ref_run', 'search_X','search_y','search_z',]

        yIncrement = 30
        for i in range(len(self.InputLabels)):
            self.Inputs[self.InputLabels[i]] = QtGui.QLineEdit(self)
            self.Inputs[self.InputLabels[i]].move(220,190 + yIncrement * i )
            self.Inputs[self.InputLabels[i]].resize(250, 23)
            self.Labels[self.InputLabels[i]] = QtGui.QLabel(self.InputLabels[i], self)
            self.Labels[self.InputLabels[i]].setAlignment(QtCore.Qt.AlignRight)
            self.Labels[self.InputLabels[i]].move(0, 190+ yIncrement * i + 5)
            self.Labels[self.InputLabels[i]].resize(220,25)
            self.Labels[self.InputLabels[i]].lower()



        self.Inputs['experiment'].hide()
        self.Labels['experiment'].move(60,85)

        self.Inputs['crop this'].setText('med, med, min')
        self.Inputs['FNIRT subsampling scheme (4 ints)'].setText('4, 2, 1, 1')
        self.Inputs['FNIRT warp resolution'].setText('5, 5, 5')
        self.Inputs['crop this'].setDisabled(True)
        self.Inputs['FNIRT subsampling scheme (4 ints)'].setDisabled(True)
        self.Inputs['FNIRT warp resolution'].setDisabled(True)



        self.dbButton = QtGui.QPushButton('get files', self)
        self.dbButton.clicked.connect(self.db_get)
        self.dbButton.move(340,8)
        self.dbButton.setToolTip('Find all .nii files in current directory')


        self.message = QtGui.QTextEdit(self,)
        self.message.setReadOnly(True)
        self.message.move(5, 625)
        self.message.resize(990, 150)
        self.message.moveCursor(QtGui.QTextCursor.End)

        self.pipeline_run_button = QtGui.QPushButton('Run Random Exception Generator', self)
        self.pipeline_run_button.move(780,600)

        self.pipeline_run_button.clicked.connect(self.start_download)

        self.downloader = pipe_thread()



        # this is for console streams going into gui
        sys.stdout = EmittingStream(textWritten=self.normalOutputWritten)
        sys.stderr = EmittingStream(textWritten=self.normalOutputWritten)
    # method to print console streams to gui
    def normalOutputWritten(self, text):
            """Append text to the QTextEdit."""
            # Maybe QTextEdit.append() works as well, but this is how I do it:
            cursor = self.message.textCursor()
            cursor.movePosition(QtGui.QTextCursor.End)
            cursor.insertText(text)
            self.message.setTextCursor(cursor)
            self.message.ensureCursorVisible()

    # globalizes all args and starts the pipeline
    def start_download(self):
        global stuff
        stuff = dict()
        stuff['cpus'] = int(self.cpucount.currentText())
        stuff['base_dir'] = str(self.base_dir_input.text())
        stuff['results_dir'] = str(self.results_dir_input.text())
        stuff['convert_dicoms'] = True if str(self.dicomBool.currentText()) == 'Yes' else False
        stuff['t_size'] = int(self.t_size_input.text())
        stuff['bet_frac'] = float(self.bet_input.text())
        stuff['subject'] = str(self.subjectDrop.currentText())
        stuff['experiment'] = str(self.expDrop.currentText())
        stuff['db'] = str(self.dbInput.text())
        stuff['moco only'] = True if str(self.moco_only.currentText()) == 'Yes' else False
        stuff['Flirt_cost_func'] = [str(self.cflirt_box.currentText())]
        stuff['interp_flirt'] = str(self.flirt_box.currentText())
        stuff['dof_flirt'] = int(self.dof_flirt.currentText())
        stuff['rigid2D'] = True if str(self.rigid2dflirt.currentText()) == 'Yes' else False
        stuff['do_fnirt'] = True if str(self.dfnirt_box.currentText()) == 'Yes' else False
        stuff['interp_fnirt'] = str(self.fnirt_box.currentText())
        stuff['results_container'] = str(self.results_con_input.text())

        try:
            if not os.path.isdir(stuff['base_dir']):
                raise NoFileNameError('Error: ' + stuff['base_dir']  + ' Does Not exist.')
            if not os.path.isdir(stuff['results_dir']):
                raise NoFileNameError('Error: ' + stuff['results_dir']  + ' Does Not exist.')



            self.downloader.start()
        except Exception as e:
            print e.message



    def db_get(self):
        df = pd.read_csv(str(self.dbInput.text()),index_col=False)
        print self.dbInput.text()

        for sub in set(df.subject):
             self.subjectDrop.addItem(sub)
        for id in set(df.experiment):
            self.expDrop.addItem(id)

    def __del__(self):
            # Restore sys.stdout
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__


    # action for file browser button
    def base_dir_act(self):
        direct = self.base_dir.getExistingDirectory()
        self.base_dir_input.setText(direct)

    # action for file browser button
    def results_dir_act(self):
        direct = self.base_dir.getExistingDirectory()
        self.results_dir_input.setText(direct)



class MainWindow(QtGui.QTabWidget):



    def __init__(self):
        super(MainWindow, self).__init__()

        pipe = True
        if pipe:
            self.pipe_tab = PipeTab(self)
            self.addTab(self.pipe_tab,"Nipype FSL Preprocessing PipeLine")

        parse = True
        if parse:
            self.parse_tab = ParsingTab()
            self.addTab(self.parse_tab, "Parsing and DB Creation")





        # # ############ MAKIN DA WINDOW ##################
        self.setFixedSize(1001,800)
        self.background_image = QtGui.QLabel(self)
        self.background_image.resize(1000, 780)
        self.background_image.move(0,22)
        self.background_image.setStyleSheet("QLabel {background-image: url(nbg.png);}")
        self.background_image.lower()
        self.setWindowOpacity(0.95)
        self.setWindowTitle('Brain Stuff: PyQT')
        self.show()






## Qthread that runs the pipeline
class pipe_thread(QtCore.QThread):
    def __init__(self):
        QtCore.QThread.__init__(self)

    def run(self,):
        from fsl_preproc import create_fsl_preproc_workflow
        from mriDbObjDefs_pandas import fsl_preproc_inode
        from mriDbObjDefs_pandas import append_param_csv
        from mriDbObjDefs_pandas import collect_results
        from mriDbObjDefs_pandas import append_pandas
        from mriDbObjDefs_pandas import check_params_used

        main_inputnode = fsl_preproc_inode() ## in MriDbObjs ; nipype superclass

        pipeline_data_params = dict() # Select only...
        pipeline_data_params['subject'] = stuff['subject']
        pipeline_data_params['experiment'] = stuff['experiment']
        pipeline_data_params['run_list'] = []
        pipeline_data_params['sess_list'] = []
        pipeline_data_params['crop_this'] = ['med', 'med', 'min']  ##note that this will almost never be needed, and isn't need in this example
        pipeline_data_params['db'] = stuff['db']

        ## putting above selections into input node
        main_inputnode.panda_fields(
                           subj=pipeline_data_params['subject'],
                           expID=pipeline_data_params['experiment'],                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        			       runList = pipeline_data_params['run_list'],
                           sessList = pipeline_data_params['sess_list'],
                           cropRule = pipeline_data_params['crop_this'],
                           db = pipeline_data_params['db'])	  	##we want all runs here.

        fsl_preproc_params = dict() # THESE ARE THE RUN PARAMS THAT CHANGE WHAT PIPELINE DOES
        fsl_preproc_params['nProc'] = stuff['cpus']

        fsl_preproc_params['basedir'] = stuff['base_dir'] # intermediate pipeline dump

        # save the results with current time in file name
        # fsl_preproc_params['results_base_dir'] = '/home/nick/datDump/results-{}'.format(datetime.now().strftime('%b-%d-%Y-%H:%M'))

        fsl_preproc_params['results_base_dir'] = stuff['results_dir']
        fsl_preproc_params['results_container'] = stuff['results_container'] #output dump specific
        fsl_preproc_params['convert_dicoms'] = stuff['convert_dicoms']
        #default_params['ref_vol_runList'] = [0]		#grab only the first run for aligning all the other runs to
        fsl_preproc_params['t_size'] = stuff['t_size'] # just go with it (max possible size).
        fsl_preproc_params['bet_frac'] = stuff['bet_frac'] # BRAIN EXTRACTION TOOL THRESHOLD

        ##motion correction
        fsl_preproc_params['ref_run'] = [] # reference volume all others will be referenced
        fsl_preproc_params['moco_only'] = stuff['moco only'] # if true, all FLIRT AND FNIRT is ignored

        ##linear registration#
        fsl_preproc_params['FLIRT_cost_func'] = stuff['Flirt_cost_func']
        fsl_preproc_params['interp_FLIRT'] = stuff['interp_flirt'] # linear registration stage (sinc,trilinear,nearestneighbour or spline)
        fsl_preproc_params['dof_FLIRT'] = stuff['dof_flirt'] # degrees of freedom (MAX : 12)
        fsl_preproc_params['rigid2D_FLIRT'] = stuff['rigid2D']  # if true, restrict linear reg to rigid body transformations and ignore dof

        ##nonlinear registration
        fsl_preproc_params['do_FNIRT'] = stuff['do_fnirt']
        fsl_preproc_params['searchr_x'] = [] # params for linear reg exposed (select the angular range over which the initial optimisation search stage is performed.)
        fsl_preproc_params['searchr_y'] = [] # find out what these guys do
        fsl_preproc_params['searchr_z'] = []
        fsl_preproc_params['interp_FNIRT'] = stuff['interp_fnirt'] # what kind of interpolation (sinc,trilinear,nearestneighbour or spline)
        fsl_preproc_params['FNIRT_subsamp'] = [[4,2,1,1]] #FNIRT runs a coarse-to-fine algorithm. This is a list specifying the downsampling factor on each iteration.
        fsl_preproc_params['FNIRT_warpres'] = [(5,5,5)] # Resolution of the warping function. Like, how fine is the warping. Can specify different level for each iteration. *Question*: Why is this list shorter than the one above?


        check_params = False

        if check_params:
            # check to see if parameters have been used yet. If theres a problem code will exit.
            check_params_used(fsl_preproc_params,'/home/nick/datDump/result_params.csv')



        # dump params in input node
        for key in fsl_preproc_params.keys():
            setattr(main_inputnode.inputs, key, fsl_preproc_params[key])

        ##====construct the workflow
        pp = create_fsl_preproc_workflow(main_inputnode)

        ##and, for reasons I can't remember, establish the base directory as an attribute of the workflow
        pp.base_dir = fsl_preproc_params['basedir']

        print main_inputnode.inputs
        if fsl_preproc_params['nProc'] > 1:
           pp.run(plugin='MultiProc', plugin_args={'n_procs' : fsl_preproc_params['nProc']})
        else:
           pp.run()


        append = False
        param_csv = False
        collect_movies = False


        if append:
            #Appending Working Volume and Brain Mask file paths to the pandas DataFrame (repickles and saves it to the same location)
            append_pandas(pp.get_node('inputnode'),fsl_preproc_params,pipeline_data_params['db'])

        if param_csv:
            # Appending the parameters used in this run to a csv to track them
            append_param_csv(fsl_preproc_params,'/home/nick/datDump/result_params.csv')

        if collect_movies:
            # collects all corrected movie files and copies them into one folder.
            collect_results()


def main():
    app = QtGui.QApplication(sys.argv)
    # noinspection PyUnusedLocal
    ex = MainWindow()
    sys.exit(app.exec_())
    del ex
    del app



main()