#/*##########################################################################
# Copyright (C) 2004-2014 V.A. Sole, European Synchrotron Radiation Facility
#
# This file is part of the PyMca X-ray Fluorescence Toolkit developed at
# the ESRF by the Software group.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
#############################################################################*/
__author__ = "V.A. Sole - ESRF Data Analysis"
__contact__ = "sole@esrf.fr"
__license__ = "MIT"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
import sys
import posixpath
import h5py
from PyMca5.PyMcaGui import PyMcaQt as qt
from PyMca5.PyMcaCore import DataObject
from PyMca5.PyMcaGui.io.hdf5 import QNexusWidget
from PyMca5.PyMcaGui.pymca import QStackWidget
from PyMca5.PyMcaIO import HDF5Stack1D
if hasattr(qt, 'QString'):
    QString = qt.QString
else:
    QString = str
DEBUG=0

class PyMcaNexusWidget(QNexusWidget.QNexusWidget):
    def __init__(self, *var, **kw):
        QNexusWidget.QNexusWidget.__init__(self, *var, **kw)

    def itemRightClickedSlot(self, ddict):
        filename = ddict['file']
        name = ddict['name']
        if ddict['dtype'].startswith('|S') or\
           ddict['dtype'].startswith('|O'):
            #handle a right click on a dataset of string type
            return self.showInfoWidget(filename, name, False)
            pass
        elif ddict['dtype'] == '':
            #handle a right click on a group
            return self.showInfoWidget(filename, name, False)
        else:
            #handle a right click on a numeric dataset
            _hdf5WidgetDatasetMenu = qt.QMenu(self)
            _hdf5WidgetDatasetMenu.addAction(QString("Add to selection table"),
                                        self._addToSelectionTable)

            _hdf5WidgetDatasetMenu.addAction(QString("Show Information"),
                                    self._showInfoWidgetSlot)
            fileIndex = self.data.sourceName.index(filename)
            phynxFile  = self.data._sourceObjectList[fileIndex]
            info = self.getInfo(phynxFile, name)
            interpretation = info.get('interpretation', "")
            stack1D = False
            stack2D = False
            nDim = len(ddict['shape'].split('x'))
            if nDim > 1:
                stack1D = True
            if nDim == 3:
                stack2D = True
            if interpretation.lower() in ['image']:
                stack1D = False
            if interpretation.lower() in ['spectrum']:
                stack2D = False

            if stack1D:
                _hdf5WidgetDatasetMenu.addAction(QString("Show as 1D Stack"),
                                    self._stack1DSignal)
                _hdf5WidgetDatasetMenu.addAction(QString("Load and show as 1D Stack"),
                                    self._loadStack1DSignal)
            if stack2D:
                _hdf5WidgetDatasetMenu.addAction(QString("Show as 2D Stack"),
                                    self._stack2DSignal)
                _hdf5WidgetDatasetMenu.addAction(QString("Load and show as 2D Stack"),
                                    self._loadStack2DSignal)
            self._lastDatasetDict = ddict
            _hdf5WidgetDatasetMenu.exec_(qt.QCursor.pos())
            self._lastDatasetDict= None
            return

    def _stack1DSignal(self):
        if DEBUG:
            print("_stack1DSignal")
        self._stackSignal(index=-1, load=False)

    def _loadStack1DSignal(self):
        if DEBUG:
            print("_stack1DSignal")
        self._stackSignal(index=-1, load=True)

    def _loadStack2DSignal(self):
        if DEBUG:
            print("_loadStack2DSignal")
        self._stackSignal(index=0, load=True)

    def _stack2DSignal(self, load=False):
        if DEBUG:
            print("_stack2DSignal")
        self._stackSignal(index=0, load=False)

    def _stackSignal(self, index=-1, load=False):
        ddict = self._lastDatasetDict
        filename = ddict['file']
        name = ddict['name']
        sel = {}
        sel['SourceName'] = self.data.sourceName * 1
        sel['SourceType'] = "HDF5"
        fileIndex = self.data.sourceName.index(filename)
        phynxFile  = self.data._sourceObjectList[fileIndex]
        title     = filename + " " + name
        sel['selection'] = {}
        sel['selection']['sourcename'] = filename
        #single dataset selection
        scanlist = None
        sel['selection']['x'] = []
        sel['selection']['y'] = [name]
        sel['selection']['m'] = []
        sel['selection']['index'] = index
        self._checkWidgetDict()

        widget = QStackWidget.QStackWidget()
        widget.setWindowTitle(title)
        widget.notifyCloseEventToWidget(self)

        #different ways to fill the stack
        if h5py.version.version < '2.0':
            useInstance = True
        else:
            useInstance = False

        groupName = posixpath.dirname(name)
        if useInstance:
            #this crashes with h5py 1.x
            #this way it is not loaded into memory unless requested
            #and cannot crash because same instance is used
            stack = phynxFile[name]
        else:
            #create a new instance
            phynxFile = h5py.File(filename, 'r')
            stack = phynxFile[name]

        # try to find out the "energy" axis
        axesList = []
        xData = None
        try:
            group = phynxFile[groupName]
            if 'axes' in stack.attrs.keys():
                axes = stack.attrs['axes']
                if sys.version > '2.9':
                    try:
                        axes = axes.decode('utf-8')
                    except:
                        print("WARNING: Cannot decode axes")
                axes = axes.split(":")
                for axis in axes:
                    if axis in group.keys():
                        axesList.append(posixpath.join(groupName, axis))
                if len(axesList):
                    xData = phynxFile[axesList[index]].value
        except:
            # I cannot afford this Nexus specific things
            # to break the generic HDF5 functionality
            if DEBUG:
                raise
            axesList = []

        #the only problem is that, if the shape is not of type (a, b, c),
        #it will not be possible to reshape it. In that case I have to
        #actually read the values
        nDim = len(stack.shape)
        if (load) or (nDim != 3):
            stack = stack.value
            shape = stack.shape
            if index == 0:
                #Stack of images
                n = 1
                for dim in shape[:-2]:
                    n = n * dim
                stack.shape = n, shape[-2], shape[-1]
                if len(axesList):
                    if xData.size != n:
                        xData = None
            else:
                #stack of mca
                n = 1
                for dim in shape[:-1]:
                    n = n * dim
                if nDim != 3:
                    stack.shape = 1, n, shape[-1]
                if len(axesList):
                    if xData.size != shape[-1]:
                        xData = None
                #index equal -1 should be able to handle it
                #if not, one would have to uncomment next line
                #index = 2
        actualStack = DataObject.DataObject()
        actualStack.data = stack
        if xData is not None:
            actualStack.x = [xData]
        widget.setStack(actualStack, mcaindex=index)
        wid = id(widget)
        self._lastWidgetId = wid
        self._widgetDict[wid] = widget
        widget.show()

if __name__ == "__main__":
    try:
        #this is to add the 3D buttons ...
        from PyMca5 import Object3D
    except:
        #not a big deal for this tests
        pass
    app = qt.QApplication(sys.argv)
    w = PyMcaNexusWidget()
    if 0:
        w.setFile(sys.argv[1])
    else:
        from PyMca5.PyMcaCore import NexusDataSource
        dataSource = NexusDataSource.NexusDataSource(sys.argv[1:])
        w.setDataSource(dataSource)
    def addSelection(sel):
        print(sel)
    def removeSelection(sel):
        print(sel)
    def replaceSelection(sel):
        print(sel)
    w.show()
    w.sigAddSelection.connect(addSelection)
    w.sigRemoveSelection.connect(removeSelection)
    w.sigReplaceSelection.connect(replaceSelection)
    sys.exit(app.exec_())
