#!/usr/bin/env python

# Copyright 2009 Lee Harr
#
# This file is part of pybotwar.
#
# Pybotwar is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Pybotwar is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pybotwar.  If not, see <http://www.gnu.org/licenses/>.


import os
import sys

from PyQt4 import QtCore, QtGui, uic
from PyQt4.Qt import QFrame, QWidget, QHBoxLayout, QPainter

import conf

import highlightedtextedit
import numberedtextedit

uidir = 'data/ui'

class TextEditor(QtGui.QMainWindow):
    def __init__(self, parent):
        self.parent = parent
        QtGui.QMainWindow.__init__(self)
        uifile = 'editor.ui'
        uipath = os.path.join(uidir, uifile)
        TEClass, _ = uic.loadUiType(uipath)
        self.ui = TEClass()
        self.ui.setupUi(self)

        self.editor = LineTextWidget(self.ui.centralwidget)
        self.ui.verticalLayout.addWidget(self.editor)
        self.setCentralWidget(self.ui.centralwidget)

        self._filepath = None
        self._fdir = None

    def closeEvent(self, ev):
        if self.maybeSave():
            ev.accept()
        else:
            ev.ignore()

    def openfile(self, filepath=None):
        if filepath is None:
            filepath = conf.template
        else:
            self._filepath = filepath

        filestring = file(filepath).read()
        self.editor.edit.code = filestring

        if filepath is None or filepath==conf.template:
            title = 'Untitled'
        else:
            fdir, title = os.path.split(str(filepath))
            self._fdir = fdir
        self.setWindowTitle(title)

    def undo(self):
        self.editor.edit.undo()

    def redo(self):
        self.editor.edit.redo()

    def cut(self):
        self.editor.edit.cut()

    def copy(self):
        self.editor.edit.copy()

    def paste(self):
        self.editor.edit.paste()

    def selectAll(self):
        self.editor.edit.selectAll()

    def new(self):
        self.parent.newRobot()

    def open(self):
        self.parent.loadRobot(self._fdir)

    def save(self):
        if self._filepath is None:
            return self.saveAs()
        else:
            return self.savefile()

    def savecheck(self):
        filepath = self._filepath
        fdir, fname = os.path.split(str(filepath))
        if fname.endswith('.py'):
            fmodname = fname[:-3]
        else:
            title = QtCore.QString('File Name Error')
            msg = QtCore.QString('Unable to import module. File name must end in .py')
            print 'ERR', title, msg
            msgbox = QtGui.QMessageBox.information(self, title, msg)
            return

        if fdir not in sys.path:
            sys.path.append(fdir)

        try:
            sys.dont_write_bytecode = True
            if fmodname not in sys.modules:
                __import__(fmodname)
            else:
                mod = sys.modules[fmodname]
                reload(mod)

        except SyntaxError, e:
            title = QtCore.QString('Syntax Error')
            msg = QtCore.QString(str(e))
            msgbox = QtGui.QMessageBox.information(self, title, msg)
            self.selectline(e.lineno)

        except Exception, e:
            import traceback
            tb = traceback.format_exc()
            title = QtCore.QString('Error')
            msg = QtCore.QString('Other non-syntax exception: ' + tb)
            msgbox = QtGui.QMessageBox.information(self, title, msg)

    def saveAs(self):
        fdir = QtCore.QString(os.path.abspath(conf.robot_dirs[0]))
        filepath = QtGui.QFileDialog.getSaveFileName(self, 'Save Robot As', fdir)
        if filepath:
            self._filepath = filepath
            return self.savefile()
        else:
            return False

    def savefile(self):
        try:
            f = file(self._filepath, 'w')
            f.write(self.editor.edit.code)
            self.savecheck()
        except:
            QtGui.QMessageBox.warning(self, 'Cannot Save', 'Cannot save file')
            self._filepath = None
            return False
        else:
            self.editor.edit._doc.setModified(False)
            _, title = os.path.split(str(self._filepath))
            self.setWindowTitle(title)
            return True

    def maybeSave(self):
        if self.editor.edit._doc.isModified():
            ret = QtGui.QMessageBox.warning(self, self.tr("Application"),
                        self.tr("The document has been modified.\n"
                                "Do you want to save your changes?"),
                        QtGui.QMessageBox.Yes | QtGui.QMessageBox.Default,
                        QtGui.QMessageBox.No,
                        QtGui.QMessageBox.Cancel | QtGui.QMessageBox.Escape)
            if ret == QtGui.QMessageBox.Yes:
                return self.save()
            elif ret == QtGui.QMessageBox.Cancel:
                return False
        return True

    def selectline(self, n):
        docline = 1
        doccharstart = 0
        blk = self.editor.edit._doc.begin()
        while docline < n:
            txt = blk.text()
            lentxt = len(txt)+1
            doccharstart += lentxt
            blk = blk.next()
            docline += 1
        txt = blk.text()
        lentxt = len(txt)
        doccharend = doccharstart + lentxt

        curs = QtGui.QTextCursor(self.editor.edit._doc)
        curs.setPosition(doccharstart, 0)
        curs.setPosition(doccharend, 1)
        self.editor.edit.setTextCursor(curs)


class HighlightedTextEdit(highlightedtextedit.HighlightedTextEdit):
    def __init__(self, parent=None):
        QtGui.QTextEdit.__init__(self, parent)
        self.setFrameShape(QtGui.QFrame.Box)
        self.setFrameShadow(QtGui.QFrame.Plain)

        self.setWordWrapMode(QtGui.QTextOption.NoWrap)
        char_format = QtGui.QTextCharFormat()
        char_format.setFont(self.font())
        char_format.setFontPointSize(16)
        self.setFontPointSize(16)
        self.highlighter = PythonHighlighter(self.document(), char_format)
        self._doc = self.document()

        pal = QtGui.QPalette()
        bgc = QtGui.QColor(0, 0, 0)
        pal.setColor(QtGui.QPalette.Base, bgc)
        textc = QtGui.QColor(255, 255, 255)
        pal.setColor(QtGui.QPalette.Text, textc)
        self.setPalette(pal)

    def keyPressEvent(self, ev):
        k = ev.key()

        Tab = QtCore.Qt.Key_Tab
        Backtab = QtCore.Qt.Key_Backtab
        Backspace = QtCore.Qt.Key_Backspace

        if k not in (Tab, Backtab, Backspace):
            QtGui.QTextEdit.keyPressEvent(self, ev)
            return

        curs = self.textCursor()
        col = curs.columnNumber()
        blkn = curs.blockNumber()
        blk = self._doc.findBlockByNumber(blkn)
        txt = blk.text()
        firstnonspace = 0
        hasselection = curs.hasSelection()
        for c in txt:
            if c != ' ':
                break
            firstnonspace += 1

        #print k, col, firstnonspace

        if col == 0:
            if k in (Tab, Backtab):
                if hasselection:
                    selstart = curs.selectionStart()
                    selend = curs.selectionEnd()
                    curs.setPosition(selstart, 0)
                    startblk = curs.block()
                    curs.setPosition(selend, 0)
                    endblk = curs.block()
                    if selend == endblk.position():
                        endblk = endblk.previous()
                    curs.clearSelection()
                    spaces = QtCore.QString('    ')

                    blk = startblk
                    startpos = blk.position()
                    while True:
                        pos = blk.position()
                        curs.setPosition(pos, 0)
                        self.setTextCursor(curs)
                        if k == Tab:
                            self.insertPlainText(spaces)
                        else:
                            txt = blk.text()
                            if txt[:4] == '    ':
                                for char in range(4):
                                    curs.deleteChar()
                        if blk == endblk:
                            break
                        blk = blk.next()
                    endpos = blk.position() + blk.length()
                    curs.setPosition(startpos, 0)
                    curs.setPosition(endpos, 1)
                    self.setTextCursor(curs)

                elif k == Tab:
                    spaces = QtCore.QString('    ')
                    self.insertPlainText(spaces)

                elif k == Backtab:
                    if txt[:4] == '    ':
                        for char in range(4):
                            curs.deleteChar()

            elif k == Backspace:
                QtGui.QTextEdit.keyPressEvent(self, ev)

        elif col == firstnonspace:
            if k == Tab:
                nexttabstop = 4-(col%4)
                spaces = QtCore.QString(' '*nexttabstop)
                self.insertPlainText(spaces)

            elif k in (Backtab, Backspace):
                prevtabstop = col%4
                if not prevtabstop:
                    prevtabstop = 4
                for char in range(prevtabstop):
                    curs.deletePreviousChar()

        elif 0 < col < firstnonspace:
            blk0 = blk.position()
            if k == Tab:
                curs.setPosition(blk0+firstnonspace, 0)
                self.setTextCursor(curs)
            elif k == Backtab:
                curs.setPosition(blk0, 0)
                self.setTextCursor(curs)

        else:
            QtGui.QTextEdit.keyPressEvent(self, ev)


class PythonHighlighter(highlightedtextedit.PythonHighlighter):
    def updateFonts(self, font):
        self.base_format.setFont(font)
        self.empty_format = QtGui.QTextCharFormat(self.base_format)

        self.keywordFormat = QtGui.QTextCharFormat(self.base_format)
        self.keywordFormat.setForeground(QtGui.QBrush(QtGui.QColor(116,167,255)))
        self.keywordFormat.setFontWeight(QtGui.QFont.Bold)
        self.callableFormat = QtGui.QTextCharFormat(self.base_format)
        self.callableFormat.setForeground(QtGui.QBrush(QtGui.QColor(116,255,87)))
        self.magicFormat = QtGui.QTextCharFormat(self.base_format)
        self.magicFormat.setForeground(QtGui.QColor(224,128,0))
        self.qtFormat = QtGui.QTextCharFormat(self.base_format)
        self.qtFormat.setForeground(QtCore.Qt.blue)
        self.qtFormat.setFontWeight(QtGui.QFont.Bold)
        self.selfFormat = QtGui.QTextCharFormat(self.base_format)
        self.selfFormat.setForeground(QtGui.QBrush(QtGui.QColor(255,127,127)))
        #self.selfFormat.setFontItalic(True)
        self.singleLineCommentFormat = QtGui.QTextCharFormat(self.base_format)
        self.singleLineCommentFormat.setForeground(QtGui.QBrush(QtGui.QColor(187,87,255)))
        self.multiLineStringFormat = QtGui.QTextCharFormat(self.base_format)
        self.multiLineStringFormat.setBackground(
            QtGui.QBrush(QtGui.QColor(127,127,255)))
        self.quotationFormat1 = QtGui.QTextCharFormat(self.base_format)
        self.quotationFormat1.setForeground(QtCore.Qt.yellow)
        self.quotationFormat2 = QtGui.QTextCharFormat(self.base_format)
        self.quotationFormat2.setForeground(QtCore.Qt.yellow)

    def updateRules(self):

        self.rules = []
        self.rules += map(lambda s: (QtCore.QRegExp(r"\b"+s+r"\b"),
                          self.keywordFormat), self.keywords)

        self.rules.append((QtCore.QRegExp(r"\b[A-Za-z_]+\(.*\)"), self.callableFormat))
        self.rules.append((QtCore.QRegExp(r"\b__[a-z]+__\b"), self.magicFormat))
        self.rules.append((QtCore.QRegExp(r"\bself\b"), self.selfFormat))
        self.rules.append((QtCore.QRegExp(r"\bQ([A-Z][a-z]*)+\b"), self.qtFormat))

        self.multiLineStringBegin = QtCore.QRegExp(r'\"\"\"')
        self.multiLineStringEnd = QtCore.QRegExp(r'\"\"\"')

        self.rules.append((QtCore.QRegExp(r"#[^\n]*"), self.singleLineCommentFormat))

        self.rules.append((QtCore.QRegExp(r'r?\"[^\n]*\"'), self.quotationFormat1))
        self.rules.append((QtCore.QRegExp(r"r?'[^\n]*'"), self.quotationFormat2))


class NumberBar(numberedtextedit.NumberBar):
    def __init__(self, *args):
        numberedtextedit.NumberBar.__init__(self, *args)
        self.setFont(QtGui.QFont('Serif', 14))

    def update(self, *args):
        width = self.fontMetrics().width(str(self.highest_line)) + 25
        if self.width() != width:
            self.setFixedWidth(width)
        QWidget.update(self, *args)

    def paintEvent(self, event):
        h = self.size().height()
        w = self.size().width()

        contents_y = self.edit.verticalScrollBar().value()
        page_bottom = contents_y + self.edit.viewport().height()
        font_metrics = self.fontMetrics()

        painter = QPainter(self)
        painter.setBackgroundMode(QtCore.Qt.OpaqueMode)
        bgc = QtGui.QColor(0, 0, 0)
        painter.fillRect(0, 0, w, h, bgc)

        numbersborderc = QtGui.QColor(55, 75, 75)
        painter.setPen(numbersborderc)
        painter.drawLine(w-1, 0, w-1, h)

        bg = QtGui.QBrush(bgc)
        painter.setBackground(bg)
        textc = QtGui.QColor(55, 255, 255)
        painter.setPen(textc)
        fg = QtGui.QBrush(bgc)
        painter.setBrush(fg)

        line_count = 0
        # Iterate over all text blocks in the document.
        block = self.edit.document().begin()
        while block.isValid():
            line_count += 1

            # The top left position of the block in the document
            position = self.edit.document().documentLayout().blockBoundingRect(block).topLeft()

            # Draw the line number right justified at the y position of the
            # line. 3 is a magic padding number. drawText(x, y, text).
            painter.drawText(self.width() - font_metrics.width(str(line_count)) - 8, round(position.y()) - contents_y + font_metrics.ascent(), str(line_count))

            block = block.next()

        self.highest_line = line_count
        painter.end()

        QWidget.paintEvent(self, event)

    def mousePressEvent(self, ev):
        py = ev.y()
        contents_y = self.edit.verticalScrollBar().value()
        realy = contents_y + py

        doc = self.edit.document()
        layout = doc.documentLayout()
        block = doc.begin()
        line_count = 0
        while block.isValid():
            line_count += 1
            rect = layout.blockBoundingRect(block)
            top = rect.topLeft().y()
            bottom = rect.bottomLeft().y()
            if top <= realy <= bottom:
                break
            block = block.next()

        textpos = block.position()
        curs = QtGui.QTextCursor(doc)
        curs.setPosition(textpos, 0)
        self.edit.setTextCursor(curs)

    def wheelEvent(self, ev):
        self.edit.wheelEvent(ev)


class LineTextWidget(numberedtextedit.LineTextWidget):
    def __init__(self, *args):
        from PyQt4.Qt import QFrame

        QFrame.__init__(self, *args)

        self.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)

        self.edit = HighlightedTextEdit()
        self.edit.setFrameStyle(QFrame.NoFrame)
        self.edit.setAcceptRichText(False)

        self.number_bar = NumberBar()
        self.number_bar.setTextEdit(self.edit)

        hbox = QHBoxLayout(self)
        hbox.setSpacing(0)
        hbox.setMargin(0)
        hbox.addWidget(self.number_bar)
        hbox.addWidget(self.edit)

        self.edit.installEventFilter(self)
        self.edit.viewport().installEventFilter(self)


if __name__ == "__main__":

    import sys

    app = QtGui.QApplication(sys.argv)
    widget = HighlightedTextEdit()
    if len(sys.argv) == 2:
        fname = sys.argv[1]
        code = file(fname).read()
        widget.code = code
        g = QtCore.QRect(0, 0, 800, 600)
        widget.setGeometry(g)
    widget.show()
    sys.exit(app.exec_())
