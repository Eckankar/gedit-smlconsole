# -*- coding: utf-8 -*-

# config.py -- Config dialog
#
# Copyright (C) 2012 Sebastian Paaske Tørholm
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

import os
import gtk

__all__ = ('SMLConsoleConfig', 'SMLConsoleConfigDialog')

GCONF_KEY_BASE = '/apps/gedit-2/plugins/smlconsole'
GCONF_KEY_COMMAND_COLOR = GCONF_KEY_BASE + '/command-color'
GCONF_KEY_ERROR_COLOR = GCONF_KEY_BASE + '/error-color'
GCONF_KEY_SML_INTERPRETER = GCONF_KEY_BASE + '/sml-interpreter'
GCONF_KEY_SML_FLAGS = GCONF_KEY_BASE + '/sml-flags'

DEFAULT_COMMAND_COLOR = '#314e6c' # Blue Shadow
DEFAULT_ERROR_COLOR = '#990000' # Accent Red Dark
DEFAULT_SML_INTERPRETERS = [
    r'C:\Program Files\Moscow ML\bin\mosml.exe',
    r'C:\Program Files\MosMLogEmacs\mosml\bin\mosml.exe',
    r'/usr/bin/mosml',
    r'/usr/bin/sml',
]
DEFAULT_SML_FLAGS = '-P full'

class SMLConsoleConfig(object):
    try:
        import gconf
    except ImportError:
        gconf = None

    def __init__(self):
        pass

    @staticmethod
    def enabled():
        return SMLConsoleConfig.gconf != None

    @staticmethod
    def add_handler(handler):
        if SMLConsoleConfig.gconf:
            SMLConsoleConfig.gconf.client_get_default().notify_add(GCONF_KEY_BASE, handler)

    @staticmethod
    def find_an_interpreter():
        valid_interpreters = filter(lambda f: os.path.exists(f), DEFAULT_SML_INTERPRETERS)
        if valid_interpreters:
            return valid_interpreters[0]
        else:
            return 'mosml'

    color_command = property(
        lambda self: self.gconf_get_str(GCONF_KEY_COMMAND_COLOR, lambda: DEFAULT_COMMAND_COLOR),
        lambda self, value: self.gconf_set_str(GCONF_KEY_COMMAND_COLOR, value))

    color_error = property(
        lambda self: self.gconf_get_str(GCONF_KEY_ERROR_COLOR, lambda: DEFAULT_ERROR_COLOR),
        lambda self, value: self.gconf_set_str(GCONF_KEY_ERROR_COLOR, value))

    sml_interpreter = property(
        lambda self: self.gconf_get_str(GCONF_KEY_SML_INTERPRETER, self.find_an_interpreter),
        lambda self, value: self.gconf_set_str(GCONF_KEY_SML_INTERPRETER, value))

    sml_flags = property(
        lambda self: self.gconf_get_str(GCONF_KEY_SML_FLAGS, lambda: DEFAULT_SML_FLAGS),
        lambda self, value: self.gconf_set_str(GCONF_KEY_SML_FLAGS, value))

    @staticmethod
    def gconf_get_str(key, default=lambda: ''):
        if not SMLConsoleConfig.gconf:
            return default()

        val = SMLConsoleConfig.gconf.client_get_default().get(key)
        if val is not None and val.type == gconf.VALUE_STRING:
            return val.get_string()
        else:
            return default()

    @staticmethod
    def gconf_set_str(key, value):
        if not SMLConsoleConfig.gconf:
            return

        v = SMLConsoleConfig.gconf.Value(gconf.VALUE_STRING)
        v.set_string(value)
        SMLConsoleConfig.gconf.client_get_default().set(key, v)

class SMLConsoleConfigDialog(object):

    def __init__(self, datadir):
        object.__init__(self)
        self._dialog = None
        self._ui_path = os.path.join(datadir, 'ui', 'config.ui')
        self.config = SMLConsoleConfig()

    def dialog(self):
        if self._dialog is None:
            self._ui = gtk.Builder()
            self._ui.add_from_file(self._ui_path)

            self.set_colorbutton_color(self._ui.get_object('colorbutton-command'),
                                        self.config.color_command)
            self.set_colorbutton_color(self._ui.get_object('colorbutton-error'),
                                        self.config.color_error)

            self._ui.get_object('interpreter-select').set_filename(self.config.sml_interpreter)

            self._ui.get_object('flags-input').set_text(self.config.sml_flags)

            self._ui.connect_signals(self)

            self._dialog = self._ui.get_object('dialog-config')
            self._dialog.show_all()
        else:
            self._dialog.present()

        return self._dialog

    @staticmethod
    def set_colorbutton_color(colorbutton, value):
        try:
            color = gtk.gdk.color_parse(value)
        except ValueError:
            pass    # Default color in config.ui used
        else:
            colorbutton.set_color(color)

    def on_dialog_config_response(self, dialog, response_id):
        self._dialog.destroy()

    def on_dialog_config_destroy(self, dialog):
        self._dialog = None
        self._ui = None

    def on_colorbutton_command_color_set(self, colorbutton):
        self.config.color_command = colorbutton.get_color().to_string()

    def on_colorbutton_error_color_set(self, colorbutton):
        self.config.color_error = colorbutton.get_color().to_string()

    def on_interpreter_select_file_set(self, filebutton):
        self.config.sml_interpreter = filebutton.get_filename()

    def on_flags_input_changed(self, input):
        self.config.sml_flags = input.get_text()

# ex:et:ts=4:
