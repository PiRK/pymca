#/*##########################################################################
#
# The PyMca X-Ray Fluorescence Toolkit
#
# Copyright (c) 2004-2015 European Synchrotron Radiation Facility
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
__doc__= "Generate specfiles with EADL97 shell transition probabilities"
import os
import sys
import EADLParser

Elements = ['H', 'He',
            'Li', 'Be', 'B', 'C', 'N', 'O', 'F', 'Ne',
            'Na', 'Mg', 'Al', 'Si', 'P', 'S', 'Cl', 'Ar',
            'K', 'Ca', 'Sc', 'Ti', 'V', 'Cr', 'Mn', 'Fe',
            'Co', 'Ni', 'Cu', 'Zn', 'Ga', 'Ge', 'As', 'Se',
            'Br', 'Kr', 'Rb', 'Sr', 'Y', 'Zr', 'Nb', 'Mo',
            'Tc', 'Ru', 'Rh', 'Pd', 'Ag', 'Cd', 'In', 'Sn',
            'Sb', 'Te', 'I', 'Xe', 'Cs', 'Ba', 'La', 'Ce',
            'Pr', 'Nd', 'Pm', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy',
            'Ho', 'Er', 'Tm', 'Yb', 'Lu', 'Hf', 'Ta', 'W',
            'Re', 'Os', 'Ir', 'Pt', 'Au', 'Hg', 'Tl', 'Pb',
            'Bi', 'Po', 'At', 'Rn', 'Fr', 'Ra', 'Ac', 'Th',
            'Pa', 'U', 'Np', 'Pu', 'Am', 'Cm', 'Bk', 'Cf',
            'Es', 'Fm', 'Md', 'No', 'Lr', 'Rf', 'Db', 'Sg',
            'Bh', 'Hs', 'Mt']

def getHeader(filename):
    text  = '#F %s\n' % filename
    text += '#U00 This file is a conversion to specfile format of \n'
    text += '#U01 directly extracted EADL97 nonradiative transition probabilities.\n'
    text += '#U02 EADL itself can be found at:\n'
    text += '#U03           http://www-nds.iaea.org/epdl97/libsall.htm\n'
    text += '#U04 The code used to generate this file has been:\n'
    text += '#U05 %s\n' % os.path.basename(__file__)
    text += '#U06\n'
    text += '\n'
    return text

if __name__ == "__main__":
    shellList = EADLParser.getBaseShellList()
    workingShells = ['K', 'L1', 'L2', 'L3', 'M1', 'M2', 'M3', 'M4', 'M5']
    for shell in workingShells:
        fname = "EADL97_%sShellNonradiativeRates.dat" % shell[0]
        print("fname = %s" % fname)
        if shell in ['K', 'L1', 'M1']:
            if os.path.exists(fname):
                os.remove(fname)
            nscan = 0
            outfile = open(fname, 'wb')
            tmpText = getHeader(fname)
            if sys.version < '3.0':
                outfile.write(tmpText)
            else:
                outfile.write(tmpText.encode('UTF-8'))
        nscan += 1
        for i in range(1,101):
            print("Z = %d, Element = %s" % (i, Elements[i-1]))
            element = Elements[i-1]
            ddict = {}
            for key0 in shellList:
                tmpKey = key0.split()[0]
                if tmpKey in workingShells:
                    if workingShells.index(tmpKey) <= workingShells.index(shell):
                        continue
                for key1 in shellList:
                    tmpKey = key1.split()[0]
                    if tmpKey in workingShells:
                        if workingShells.index(tmpKey) <= workingShells.index(shell):
                            continue
                    key = "%s-%s%s" % (shell, key0.split()[0], key1.split()[0])
                    if shell in [key0.split()[0], key1.split()[0]]:
                        continue
                    ddict[key] = [0.0, 0.0]
            try:
                ddict = EADLParser.getNonradiativeTransitionProbabilities(\
                                        Elements.index(element)+1,
                                        shell=shell)
                print("%s Shell nonradiative emission probabilities " % shell)
            except IOError:
                #This happens when reading elements not presenting the transitions
                pass
                #continue
            if i == 1:
                #generate the labels
                nTransitions = 0
                tmpText = '#L Z  TOTAL'
                for key0 in workingShells:
                    tmpKey = key0.split()[0]
                    if tmpKey in workingShells:
                        if workingShells.index(tmpKey) <= workingShells.index(shell):
                            continue
                    for key1 in shellList:
                        tmpKey = key1.split()[0]
                        if tmpKey in workingShells:
                            if workingShells.index(tmpKey) <= workingShells.index(shell):
                                continue
                        key = "%s-%s%s" % (shell, key0.split()[0], key1.split()[0])
                        tmpText += '  %s' % (key)
                        nTransitions += 1
                text  = '#S %d %s-Shell nonradiative rates\n' % (nscan, shell)
                text += '#N %d\n' % (2 + nTransitions)
                text += tmpText + '\n'
            else:
                text = ''
            # this loop calculates the totals, because it cannot be deduced from the subset
            # transitions written in the file
            total = 0.0
            for key0 in shellList:
                tmpKey = key0.split()[0]
                if tmpKey in workingShells:
                    if workingShells.index(tmpKey) <= workingShells.index(shell):
                        continue
                for key1 in shellList:
                    tmpKey = key1.split()[0]
                    if tmpKey in workingShells:
                        if workingShells.index(tmpKey) <= workingShells.index(shell):
                            continue
                    key = "%s-%s%s" % (shell, key0.split()[0], key1.split()[0])
                    total += ddict.get(key, [0.0, 0.0])[0]
            text += '%d  %.7E' % (i, total)
            for key0 in workingShells:
                tmpKey = key0.split()[0]
                if tmpKey in workingShells:
                    if workingShells.index(tmpKey) <= workingShells.index(shell):
                        continue
                for key1 in shellList:
                    tmpKey = key1.split()[0]
                    if tmpKey in workingShells:
                        if workingShells.index(tmpKey) <= workingShells.index(shell):
                            continue
                    key = "%s-%s%s" % (shell, key0.split()[0], key1.split()[0])
                    valueToWrite = ddict.get(key, [0.0, 0.0])[0]
                    if valueToWrite == 0.0:
                        text += '  0.0'
                    else:
                        text += '  %.7E' % valueToWrite
            text += '\n'
            if sys.version < '3.0':
                outfile.write(text)
            else:
                outfile.write(text.encode('UTF-8'))
        if sys.version < '3.0':
            outfile.write('\n')
        else:
            outfile.write('\n'.encode('UTF-8'))
    if sys.version < '3.0':
        outfile.write('\n')
    else:
        outfile.write('\n'.encode('UTF-8'))
    outfile.close()
