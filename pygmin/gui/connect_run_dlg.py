import sys
import numpy as np

from PyQt4 import QtGui, QtCore, Qt
from PyQt4.QtGui import QDialog, QApplication, QListWidgetItem


from pygmin.gui.ui.connect_run_ui import Ui_MainWindow as UI
from pygmin.utils.events import Signal
from pygmin.gui.double_ended_connect_runner import DECRunner
from pygmin.gui.ui.mplwidget import MPLWidget
from pygmin.gui.graph_viewer import GraphViewWidget



class OutLog(object):
    """recieve text through self.write and write it to a QtextEdit object
    
    (edit, out=None, color=None) -> can write stdout, stderr to a
    QTextEdit.
    
    Parameters
    ----------
    edit : QTextEdit
    out : something like a filestream (has out.write(mystring))
        alternate stream ( can be the original sys.stdout )
    color : 
        alternate color (i.e. color stderr a different color)
    
    from http://www.riverbankcomputing.com/pipermail/pyqt/2009-February/022025.html
    """
    def __init__(self, edit, out=None, color=None):
        self.edit = edit
        self.out = out
        self.color = color

    def write(self, m):
        if self.color:
            tc = self.edit.textColor()
            self.edit.setTextColor(self.color)

        self.edit.moveCursor(QtGui.QTextCursor.End)
        self.edit.insertPlainText( m )

        if self.color:
            self.edit.setTextColor(tc)

        if self.out:
            self.out.write(m)
    
    def flush(self):
        pass

class ConnectEnergyWidget(MPLWidget):
    def __init__(self, parent=None):
        #QtGui.QWidget
        MPLWidget.__init__(self, parent=parent)
        #self.canvas = MPLWidget(self)

    def update_gui(self, S, E):
        self.axes.clear()
        self.axes.set_xlabel("distance along the path")
        self.axes.set_ylabel("energy")
#        self.axes.set_title("")
        self.axes.plot(S, E, '-o')
        self.draw()


class ConnectViewer(QtGui.QMainWindow):
    """
    external viewer for connect runs
    
    This viewer will use DECRunner to run a connect job in parallel.
    The log messages from that run will be redirected into a GUI text viewer.
    When the run is finished, the completed path will be shown in an OGL viewer
    
    Parameters
    ----------
    system : 
    database :
    min1, min2 : Minimum objects
        the minima to try to connect
    parent : 
        the parent window
    app : 
        the application
    
    See Also
    --------
    DECRunner
    
    """
    def __init__(self, system, database, min1=None, min2=None, parent=None, app=None):
        QtGui.QMainWindow.__init__(self, parent=parent)    
        self.ui = UI()
        self.ui.setupUi(self)
        self.ui.centralwidget.hide()
        
        self.app = app
        self.system = system
        self.database = database
        
        self.ogl = self.ui.ogl
        self.ogl.setSystem(system)

        
        self.textEdit = self.ui.textEdit      
        self.textEdit.setReadOnly(True)
        self.textEdit_writer = OutLog(self.textEdit)
        
        if min1 is not None and min2 is not None:
            self.decrunner = DECRunner(system, database, min1, min2, outstream=self.textEdit_writer)
            self.decrunner.on_finished.connect(self.on_finished)

        self.view_3D = self.ui.dockWidget_3
        self.ui.action3D.setChecked(True)
        
        self.wgt_energies = ConnectEnergyWidget(parent=self)
        self.view_energies = self.new_view("Energies", self.wgt_energies, QtCore.Qt.TopDockWidgetArea)
        self.ui.actionEnergy.setChecked(True)

        self.wgt_graphview = GraphViewWidget(database=self.database, parent=self, app=app)
        self.view_graphview = self.new_view("Graph View", self.wgt_graphview, QtCore.Qt.TopDockWidgetArea)
        self.view_graphview.hide()
        self.ui.actionGraph.setChecked(False)
        
        self.ui.actionStop.setVisible(False)
        self.ui.actionD_Graph.setVisible(False)
        self.ui.actionSummary.setVisible(False)
        self.ui.actionSummary.setChecked(False)


    def start(self):
        self.decrunner.start()

    def on_finished(self):
        print "success", self.decrunner.success
#        print "success", self.decrunner.smoothed_path
        if self.decrunner.success:
            # get the path data
            self.smoothed_path = np.array(self.decrunner.smoothed_path)
            self.S = np.array(self.decrunner.S)
            self.energies = np.array(self.decrunner.energies)
#            print self.smoothed_path.shape

            # show the smoothed path in the ogl viewer
            self.ogl.setCoordsPath(self.smoothed_path)
            
            # plot the energies
            self.wgt_energies.update_gui(self.S, self.energies)
            
            # plot the graph of minima
            self.wgt_graphview.make_graph(database=self.decrunner.database, minima=self.decrunner.newminima)
            self.wgt_graphview.show_graph()

    def new_view(self, title, widget, pos=QtCore.Qt.RightDockWidgetArea):
        child = QtGui.QDockWidget(title, self)
        child.setWidget(widget)
        self.addDockWidget(pos, child)
        return child

    def toggle_view(self, view, show):
        if show:
            view.show()
        else:
            view.hide()

    def on_actionEnergy_toggled(self, checked):
        self.toggle_view(self.view_energies, checked)
    def on_actionGraph_toggled(self, checked):
        self.toggle_view(self.view_graphview, checked)
    def on_action3D_toggled(self, checked):
        self.toggle_view(self.view_3D, checked)


#
# only testing stuff below here
#


def start():
    wnd.start()
    print >> sys.stderr, "started decrunner"
#    wnd.finish()


if __name__ == "__main__":
    from OpenGL.GLUT import glutInit
    import sys
    import pylab as pl

    app = QtGui.QApplication(sys.argv)
    from pygmin.systems import LJCluster
    pl.ion()
    natoms = 13
    system = LJCluster(natoms)
    system.params.double_ended_connect.local_connect_params.NEBparams.iter_density = 5.
    x1, e1 = system.get_random_minimized_configuration()[:2]
    x2, e2 = system.get_random_minimized_configuration()[:2]
    db = system.create_database()
    min1 = db.addMinimum(e1, x1)
    min2 = db.addMinimum(e2, x2)
    
    
    wnd = ConnectViewer(system, db, min1=min1, min2=min2, app=app)
#    decrunner = DECRunner(system, db, min1, min2, outstream=wnd.textEdit_writer)
    glutInit()
    wnd.show()
    from PyQt4.QtCore import QTimer
    QTimer.singleShot(10, start)
    sys.exit(app.exec_()) 