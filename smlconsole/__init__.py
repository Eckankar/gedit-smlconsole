# -*- coding: utf-8 -*-

# __init__.py -- plugin object
#
# Copyright (C) 2012
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

# Based on pythonconsole included with gedit.

import gtk
import gedit

from console import SMLConsole
from config import SMLConsoleConfigDialog
from config import SMLConsoleConfig

SML_ICON = 'gnome-mime-text-x-python'

class SMLConsolePlugin(gedit.Plugin):
    def __init__(self):
        gedit.Plugin.__init__(self)
        self.dlg = None

    def activate(self, window):
        console = SMLConsole(namespace = {'__builtins__' : __builtins__,
                                             'gedit' : gedit,
                                             'window' : window})
        #console.eval('print "You can access the main window through ' \
        #             '\'window\' :\\n%s" % window', False)
        bottom = window.get_bottom_panel()
        image = gtk.Image()
        image.set_from_icon_name(SML_ICON, gtk.ICON_SIZE_MENU)
        bottom.add_item(console, 'SML Console', image)
        window.set_data('SMLConsolePluginInfo', console)

    def deactivate(self, window):
        console = window.get_data("SMLConsolePluginInfo")
        console.stop()
        window.set_data("SMLConsolePluginInfo", None)
        bottom = window.get_bottom_panel()
        bottom.remove_item(console)

    def is_configurable(self):
        return True

    def create_configure_dialog(self):
        if not self.dlg:
            self.dlg = SMLConsoleConfigDialog(self.get_data_dir())

        dialog = self.dlg.dialog()
        window = gedit.app_get_default().get_active_window()
        if window:
            dialog.set_transient_for(window)

        return dialog

# ex:et:ts=4:
