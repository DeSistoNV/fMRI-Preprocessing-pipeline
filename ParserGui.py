__author__ = 'Nick Desisto'
import sys
import os
import sqlite3
from datetime import datetime
from collections import OrderedDict

from PyQt4 import QtGui
from random import randint

## 1.0 - 11.20.2014 - first working copy
## 1.0.1 - added fields for working volume and brain mask

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
        print files
        return files


# noinspection PyUnresolvedReferences
class QtInter(QtGui.QWidget):
    def __init__(self):
        super(QtInter, self).__init__()
        self.usedNames = []  # list for checking if a file has already been added
        self.rows = []  # stack of files to be added to database
        self.autoFiles = []  # Stack of parsed files
        self.yIncrement = 23  # constant for input and label placement
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
                           '}')  # setting opacity of all entry fields

        # self.button = QtGui.QPushButton('Test Values', self)
        # self.button.clicked.connect(self.test_vals)
        # self.button.setToolTip('Test Values for testing')
        # self.button.move(150, 0)

        self.dirButton = QtGui.QPushButton('get files', self)
        self.dirButton.clicked.connect(self.create_auto_list)
        self.dirButton.move(20, 600)
        self.dirButton.setToolTip('Find all .nii files in current directory')

        self.addButton = QtGui.QPushButton('Add File', self)
        self.addButton.clicked.connect(self.file_append)
        self.addButton.move(280, 600)
        self.addButton.setToolTip('Add current file to stack')

        self.pandaButton = QtGui.QPushButton('pandas and CSV', self)
        self.pandaButton.clicked.connect(self.pickle_panda)
        self.pandaButton.move(655, 750)
        self.pandaButton.resize(100, 25)
        self.pandaButton.setToolTip('Output to Pickled Pandas DataFrame and CSV file')

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
                self.Inputs[self.InputLabels[i]].move(100, self.yIncrement + self.yIncrement * i)
                self.Inputs[self.InputLabels[i]].resize(250, 20)
            self.Labels[self.InputLabels[i]] = QtGui.QLabel(self.InputLabels[i], self)
            self.Labels[self.InputLabels[i]].move(5, self.yIncrement + self.yIncrement * i + 4)
            self.Labels[self.InputLabels[i]].lower()
        for i in range(len(self.inputsToolTips)):
            self.Inputs[self.InputLabels[i]].setToolTip(self.inputsToolTips[i])

        self.MatrixLabels = ['matrix_x', 'matrix_y', 'n_slices', 'vox_x', 'vox_y', 'vox_z']
        self.MatrixToolTips = ['number of voxels along rows', 'number of voxels along cols',
                               'number of slices per volume',
                               'voxel dimensions in mm', 'voxel dimensions in mm', 'slice thickness']
        for i in range(3):
            self.Inputs[self.MatrixLabels[i]] = QtGui.QLineEdit(self)
            self.Inputs[self.MatrixLabels[i]].move(100 + 50 * i, self.yIncrement + self.yIncrement * 21)
            self.Inputs[self.MatrixLabels[i]].resize(40, 20)
            self.Inputs[self.MatrixLabels[i]].setToolTip(self.MatrixToolTips[i])
            self.Inputs[self.MatrixLabels[i + 3]] = QtGui.QLineEdit(self)
            self.Inputs[self.MatrixLabels[i + 3]].move(100 + 50 * i, self.yIncrement + self.yIncrement * 22)
            self.Inputs[self.MatrixLabels[i + 3]].resize(40, 20)
            self.Inputs[self.MatrixLabels[i + 3]].setToolTip(self.MatrixToolTips[i + 3])

        # # LABELS AND INPUTS ARE BOTH IN DICTS BY THEIR LABEL NAME HERE
        self.table = QtGui.QListWidget(self)
        self.table.resize(215, 597)
        self.table.move(365, 25)

        self.tableLabel = QtGui.QLabel('<html><b>FILES CURRENTLY ADDED</b></html>', self)
        self.tableLabel.move(395, 10)
        self.table.currentItemChanged.connect(self.view_file)

        self.parse_table = QtGui.QListWidget(self)
        self.parse_table.resize(210, 597)
        self.parse_table.move(585, 25)

        self.parseLabel = QtGui.QLabel('<html><b>PARSED FILES READY TO ENTER</b></html>', self)
        self.parseLabel.move(600, 10)
        self.parse_table.currentItemChanged.connect(self.select_parse_file)

        self.outputInput = QtGui.QLineEdit(self)
        self.outputInput.move(350, 750)
        self.outputInput.resize(300, 23)
        self.outputInput.setToolTip('Enter path to save files to here. DO NOT INCLUDE FILE EXTENSION')

        self.unAddButton = QtGui.QPushButton('un-add', self)
        self.unAddButton.move(495, 575)
        self.unAddButton.clicked.connect(self.un_add)
        self.unAddButton.setToolTip('select an item from the added list and press to un-add')

        self.nextPathButton = QtGui.QPushButton('next path',self)
        self.nextPathButton.move(150,600)
        self.nextPathButton.clicked.connect(self.next_path)
        self.nextPathButton.setToolTip('clear currently unappended filed and allow a new directory to be parsed')


        self.test_vals()
        # ############ MAKIN DA WINDOW ##################

        self.message = QtGui.QTextEdit(self)
        self.message.setReadOnly(True)
        self.message.move(5, 625)
        self.message.resize(790, 120)
        self.message.append(self.open_message)
        self.message.moveCursor(QtGui.QTextCursor.End)

        self.background_image = QtGui.QLabel(self)
        self.background_image.resize(800, 800)
        self.background_image.setStyleSheet("QLabel {background-image: url(/home/nick/Documents/nuerobg.png);}")
        self.background_image.lower()

        self.setGeometry(300, 100, 800, 780)
        self.setFixedSize(800, 780)
        self.setWindowOpacity(0.95)
        self.setWindowTitle('Brain Stuff: PyQT')
        self.show()


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
        self.Inputs['run_code_path'].setText('Run/Code/Path')
        self.Inputs['main path'].setText('/home/nick/MUSC/Naselaris_TN/')
        self.Inputs['experiment'].setText('imagery.rf')
        self.Inputs['sessionID'].setText('55')
        self.Inputs['design matrix'].setText('design_matrix')
        self.Inputs['location'].setText('The Moon')
        self.Inputs['TR'].setText('2')
        self.Inputs['run_code_file'].setText('run_experiment.py')
        self.Inputs['design_matrix_path'].setText('/framefiles')
        self.Inputs['frameFilePath'].setText('/frame/file/path')
        self.Inputs['picPath'].setText('/pic/path/')
        self.Inputs['siemensRef'].setText('0')
        self.Inputs['padVol'].setText('55')
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
                self.parseTableObjects.append(QtGui.QListWidgetItem(f.split('/')[0]))
                self.parse_table.addItem(self.parseTableObjects[len(self.parseTableObjects) - 1])
            self.message.append(str(len(self.autoFiles)) + ' .nii files found')

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
                self.Inputs['matrix_x'].setText(parse['Mosaic rows'])
                self.Inputs['matrix_y'].setText(parse['Mosaic columns'])
                self.Inputs['n_slices'].setText(parse['Number of slices'])
            except KeyError:
                self.Inputs['matrix_x'].setText('')
                self.Inputs['matrix_y'].setText('')
                self.Inputs['n_slices'].setText('')
                self.message.append('<html><font color = "red">Error: Unable to parse matrix dimensions<br></font></html>')
            self.Inputs['vox_x'].setText(parse['Voxel size x (mm)'])
            self.Inputs['vox_y'].setText(parse['Voxel size y (mm)'])
            self.Inputs['vox_z'].setText(parse['Slice thickness (mm)'])
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
            self.message.append(
                '<html><font color = "green"><b>---------- PANDA PICKLED TO ' + str(
                    self.outputInput.text()) + '.p' + '---------</b><br></font></html>')
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

    """ outputs to SQLite3 DB """

    # def do_sql(self):
    #     out = str(self.outputInput.text())
    #     test = out[:out.rfind('/')]
    #     out += '.db'
    #     try:
    #         if not os.path.isdir(test):
    #             raise DirectoryDoesntExistError()
    #
    #         if os.path.isfile(out):
    #             raise FileAlreadyExistsError()
    #
    #         if len(self.rows) < 1:
    #             raise NoFilesAddedError()
    #
    #         connection = sqlite3.connect(str(self.outputInput.text()) + '.db')
    #         cursor = connection.cursor()
    #
    #         # create table
    #         # noinspection PyPep8
    #         cursor.execute('CREATE TABLE mri \
    #                      (runID INTEGER PRIMARY KEY AUTOINCREMENT, \
    #                       date  DATE, 				   \
    #                       subject TEXT,                            \
    #                       expID TEXT,                              \
    #                       working_vol TEXT,                        \
    #                       brain_mask TEXT,                         \
    #                       sessionID INTEGER,                       \
    #                       runType TEXT,                            \
    #                       designMatrixName TEXT,                   \
    #                       frameFileName TEXT,                      \
    #                       runName TEXT,                            \
    #                       nVols INTEGER,                           \
    #                       tesla TEXT,                              \
    #                       magnetSite TEXT,                         \
    #                       runPath TEXT,                            \
    #                       tr REAL,                                 \
    #                       matrixSizeX INTEGER,                     \
    #                       matrixSizeY INTEGER,                     \
    #                       matrixSizeZ INTEGER,                     \
    #                       voxResX REAL,                            \
    #                       voxResY REAL,                            \
    #                       voxResZ REAL,                            \
    #                       runCodePath TEXT,                        \
    #                       runCodeName TEXT,                        \
    #                       designMatrixPath TEXT,                   \
    #                       frameFilePath TEXT,                      \
    #                       picPath TEXT,                            \
    #                       seimensRef INTEGER,                      \
    #                       padVol INTEGER                           \
    #                       )'
    #         )
    #
    #         for row in self.rows:
    #             values = 'INSERT INTO mRI VALUES' + '(null,' + ','.join(
    #                 str(i) if type(i) == int else "\'" + i + "\'" for i in row.values()) + ')'
    #             cursor.execute(values)
    #
    #         connection.commit()
    #
    #         self.message.append(
    #             '<html><b><font color = "green">--------SQL DB saved to ' + str(
    #                 self.outputInput.text()) + '.db' + ' ---------</font><</b>br></html>')
    #     except sqlite3.OperationalError:
    #         self.message.append(
    #             '<html><font color = "red">SQLite3 Operation Error: Possible that you do not have permission'
    #             ' to this directory</font><br></html>')
    #     except NoFilesAddedError:
    #         self.message.append('<html><font color = "red">Error: No files added yet</font><brb></html>')
    #     except FileAlreadyExistsError:
    #         self.message.append('<html><font color = "red">Error: file ' + out + ' Already exists</font><br></html>')
    #     except DirectoryDoesntExistError:
    #         self.message.append(
    #             '<html><font color = "red">Error: File Path -  ' + test + 'does not exist.<br></font></html>')
    #     finally:
    #         self.message.moveCursor(QtGui.QTextCursor.End)

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


def main():
    app = QtGui.QApplication(sys.argv)
    # noinspection PyUnusedLocal
    ex = QtInter()
    sys.exit(app.exec_())


main()