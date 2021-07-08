"""
  Graphical User Interface
  ========================

"""

import os

from pymol import cmd
from pymol.Qt import QtWidgets, QtCore
from pymol.Qt.utils import loadUi

from .io import get_docked, load_dock4, load_chimerax, load_pydock, load_xyz, export_docked_data


def run_gui():
    """Main PyViewDock dialog window"""

    docked = get_docked()

    # create a new Window
    dialog = QtWidgets.QDialog()

    # populate the Window from our *.ui file which was created with the Qt Designer
    uifile = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'gui.ui')
    widget = loadUi(uifile, dialog)

    # hide question mark and add minimize button
    widget.setWindowFlags(widget.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint | QtCore.Qt.WindowMinimizeButtonHint)

    ##  ERROR MESSAGE  ------------------------------------------------
    def error_msg(text, informative_text=None):
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setWindowTitle("PyViewDock")
        msg.setText(text)
        if informative_text:
            msg.setInformativeText(informative_text)
        msg.exec_()


    ##  MENUBAR  ------------------------------------------------------

    show_column = widget.menuColumns.addMenu('Show')
    hide_column = widget.menuColumns.addMenu('Hide')
    hide_all = widget.menuColumns.addAction('buttonHideAll')
    hide_all.setText("Hide All")


    ##  I/O FILES  ----------------------------------------------------

    def clear_all():
        """Clear all the docked entries"""
        docked.clear()
        draw_table()

    def browse_open():
        """Callback for the 'Open' button"""
        supported_formats = {'PDB Dock >4 (*.pdb)': load_dock4,
                             'ChimeraX (*.chimerax)': load_chimerax,
                             'pyDock (*.ene; *.eneRST)': load_pydock,
                             'XYZ (*.xyz)': load_xyz,
                             'All Files(*)': None}
        default_suffix_format = {'pdb': 'PDB Dock >4 (*.pdb)',
                                 'chimerax': 'ChimeraX (*.chimerax)',
                                 'ene': 'pyDock (*.ene; *.eneRST)',
                                 'enerst': 'pyDock (*.ene; *.eneRST)',
                                 'xyz': 'XYZ (*.xyz)'}
        # launch open file dialog from system
        filename, format_selected = QtWidgets.QFileDialog.getOpenFileName(parent=dialog,
                                                                          caption='Open file containing docked structures',
                                                                          directory=os.getcwd(),
                                                                          filter=";;".join(supported_formats.keys()))
        if not filename: return
        # guess format from suffix
        if format_selected == 'All Files(*)':
            suffix = os.path.basename(filename).rpartition('.')[-1].lower()
            if suffix in default_suffix_format:
                format_selected = default_suffix_format[suffix]
            else:
                # error message
                error_msg(f"Unsupported format file:  .{suffix}")
                return
        # load file with corresponding format' function
        supported_formats[format_selected](filename)
        draw_table()

    def browse_export_data():
        """Callback for the 'Export Data' button"""
        supported_formats = {'CSV (*.csv)': 'csv',
                             'Text (*.txt)': 'txt',
                             'All Files(*)': None}
        default_suffix_format = {'csv': 'CSV (*.csv)',
                                 'txt': 'Text (*.txt)'}
        # launch open file dialog from system
        filename, format_selected = QtWidgets.QFileDialog.getSaveFileName(parent=dialog,
                                                                          caption='Save file containing docked data',
                                                                          directory=os.getcwd(),
                                                                          filter=";;".join(supported_formats.keys()))
        if not filename: return
        # guess format from suffix
        if format_selected == 'All Files(*)':
            suffix = os.path.basename(filename).rpartition('.')[-1].lower()
            # if not in supported_formats, fallback to csv
            format_selected = default_suffix_format.get(suffix, default_suffix_format['csv'])
        # save file with corresponding format' arguments
        export_docked_data(filename, supported_formats[format_selected])


    ##  TABLE  --------------------------------------------------------

    headers = docked.headers

    def draw_table(headers=headers):
        """Fill the whole table with data from docked entries"""
        widget.tableDocked.clear()
        widget.tableDocked.setSortingEnabled(False)
        n_internal_columns = 3
        # check if requested headers in remarks
        headers = [i for i in headers if i in docked.remarks]
        # number of rows and columns
        widget.tableDocked.setColumnCount(len(headers)+n_internal_columns)
        widget.tableDocked.setRowCount(docked.n_entries)
        # fill table
        widget.tableDocked.setHorizontalHeaderLabels([""]*n_internal_columns+headers)
        for row, entry in enumerate(docked.entries):
            # hidden internal columns [n_entry, 'object', 'state']
            widget.tableDocked.setItem(row, 0, QtWidgets.QTableWidgetItem(str(row)))
            widget.tableDocked.setItem(row, 1, QtWidgets.QTableWidgetItem(str(entry['internal']['object'])))
            widget.tableDocked.setItem(row, 2, QtWidgets.QTableWidgetItem(str(entry['internal']['state'])))
            # assign to table cell
            for column, remark in enumerate(headers):
                value = entry['remarks'][remark]
                item = QtWidgets.QTableWidgetItem()
                item.setData(QtCore.Qt.EditRole, value)
                widget.tableDocked.setItem(row, column+n_internal_columns, item)
                widget.tableDocked.item(row, column+n_internal_columns).setTextAlignment(QtCore.Qt.AlignCenter)
        widget.tableDocked.resizeColumnsToContents()
        widget.tableDocked.resizeRowsToContents()
        for i in range(n_internal_columns):
            widget.tableDocked.hideColumn(i)
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

    def hide_header_all():
        """Remove all column headers"""
        headers.clear()
        draw_table()

    def display_selected():
        """Display entries corresponding to selected rows"""
        #TODO: multiple selection
        selected_row = widget.tableDocked.selectedItems()
        if selected_row:
            row_n = selected_row[0].row()
            object = widget.tableDocked.item(row_n, 1).text()
            state = widget.tableDocked.item(row_n, 2).text()
            cmd.set('state', state)
            cmd.disable(" ".join(docked.objects))
            cmd.enable(object)

    draw_table()


    ##  CALLBACKS  ----------------------------------------------------

    widget.buttonOpen.triggered.connect(browse_open)
    widget.buttonExportData.triggered.connect(browse_export_data)
    widget.buttonClearAll.triggered.connect(clear_all)
    hide_all.triggered.connect(hide_header_all)
    widget.tableDocked.itemSelectionChanged.connect(display_selected)

    dialog.show()
