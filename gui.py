"""
  Graphical User Interface
  ========================

"""

import os

from pymol import cmd
from pymol.Qt import QtWidgets, QtCore
from pymol.Qt.utils import loadUi

from .io import docked, load_cluster

# initial headers
headers = ['Cluster', 'ClusterRank', 'deltaG']

def run_gui():
    """Main PyViewDock dialog window"""

    global docked, headers

    # create a new Window
    dialog = QtWidgets.QDialog()

    # populate the Window from our *.ui file which was created with the Qt Designer
    uifile = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'gui.ui')
    widget = loadUi(uifile, dialog)


    ##  MENUBAR  ------------------------------------------------------

    show_column = widget.menuColumns.addMenu('Show')
    hide_column = widget.menuColumns.addMenu('Hide')


    ##  I/O FILES  ----------------------------------------------------

    def browse_open():
        """Callback for the 'Open' button"""
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(parent=dialog,
                                                            caption='Open file containing docked structures',
                                                            directory=os.getcwd(),
                                                            filter='PDB File (*.pdb);; All Files(*)')
        if filename:
            load_cluster(filename)
        draw_table()


    ##  TABLE  --------------------------------------------------------

    def draw_table(headers=headers):
        """Fill the whole table with data from docked entries"""
        widget.tableDocked.clear()
        widget.tableDocked.setSortingEnabled(False)
        # check if requested headers in remarks
        headers = [i for i in headers if i in docked.remarks]
        # number of rows and columns
        widget.tableDocked.setColumnCount(len(headers)+2)
        widget.tableDocked.setRowCount(docked.n_entries)
        # fill table
        widget.tableDocked.setHorizontalHeaderLabels([""]*2+headers)
        for row in range(docked.n_entries):
            # hidden internal columns ('object', 'state')
            widget.tableDocked.setItem(row, 0,
                QtWidgets.QTableWidgetItem(str(docked.entries[row]['internal']['object'])))
            widget.tableDocked.setItem(row, 1,
                QtWidgets.QTableWidgetItem(str(docked.entries[row]['internal']['state'])))
            for column, remark in enumerate(headers):
                # convert to string
                value = docked.entries[row]['remarks'][remark]
                if isinstance(value, int):
                    # surrounded by spaces for proper sorting
                    value_fmt = f"{value:>4}"+" "*2
                elif isinstance(value, float):
                    value_fmt = f"{value}"
                else:
                    value_fmt = value
                # assign to table cell
                widget.tableDocked.setItem(
                    row, column+2, QtWidgets.QTableWidgetItem(value_fmt))
                widget.tableDocked.item(
                    row, column+2).setTextAlignment(QtCore.Qt.AlignCenter)
        widget.tableDocked.resizeColumnsToContents()
        widget.tableDocked.resizeRowsToContents()
        widget.tableDocked.hideColumn(0)
        widget.tableDocked.hideColumn(1)
        # update columns menubar
        show_column.clear()
        hide_column.clear()
        for i in sorted(docked.remarks - set(headers)):
            action = show_column.addAction(i)
            action.triggered.connect(lambda chk, i=i: show_header(i))
        for i in headers:
            action = hide_column.addAction(i)
            action.triggered.connect(lambda chk, i=i: hide_header(i))
        # show table
        widget.tableDocked.setSortingEnabled(True)
        widget.tableDocked.show()

    def show_header(header):
        """Add a column to headers"""
        headers.append(header)
        draw_table()

    def hide_header(header):
        """Remove a column from headers"""
        headers.remove(header)
        draw_table()

    def display_selected():
        """Display entries corresponding to selected rows"""
        #TODO: multiple selection
        selected_row = widget.tableDocked.selectedItems()
        if selected_row:
            row_n = selected_row[0].row()
            object = widget.tableDocked.item(row_n, 0).text()
            state = widget.tableDocked.item(row_n, 1).text()
            cmd.set('state', state)
            cmd.disable(" ".join(docked.objects))
            cmd.enable(object)

    draw_table()


    ##  CALLBACKS  ----------------------------------------------------

    widget.buttonOpen.triggered.connect(browse_open)
    widget.tableDocked.itemSelectionChanged.connect(display_selected)

    dialog.show()
