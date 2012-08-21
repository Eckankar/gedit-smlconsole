# -*- coding: utf-8 -*-

# smlconsole.py -- Console widget
#
# Copyright (C) 2012 - Sebastian Paaske Tørholm
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

import string
import sys
import re
import traceback
import gobject
import gtk
import pango
import subprocess
import threading
import os

from config import SMLConsoleConfig

__all__ = ('SMLConsole', 'OutFile')

SML_COMMAND = [r'C:\Program Files\MosMLogEmacs\mosml\bin\mosml.exe', "-P", "full"]

class SMLConsole(gtk.ScrolledWindow):

    __gsignals__ = {
        'grab-focus' : 'override',
    }

    def __init__(self, namespace = {}):
        gtk.ScrolledWindow.__init__(self)
        gtk.gdk.threads_init()

        self.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.set_shadow_type(gtk.SHADOW_IN)
        self.view = gtk.TextView()
        self.view.modify_font(pango.FontDescription('Monospace'))
        self.view.set_editable(True)
        self.view.set_wrap_mode(gtk.WRAP_WORD_CHAR)
        self.add(self.view)
        self.view.show()

        buffer = self.view.get_buffer()
        self.normal = buffer.create_tag("normal")
        self.error  = buffer.create_tag("error")
        self.command = buffer.create_tag("command")

        SMLConsoleConfig.add_handler(self.apply_preferences)
        self.apply_preferences()

        self.__spaces_pattern = re.compile(r'^\s+')
        self.namespace = namespace

        self.block_command = False

        # Init first line
        buffer.create_mark("input-line", buffer.get_end_iter(), True)
        buffer.create_mark("input-end", buffer.get_end_iter(), False)

        # Init history
        self.history = ['']
        self.history_pos = 0
        self.current_command = ''
        self.namespace['__history__'] = self.history

        # Set up hooks for standard output.
        self.stdout = OutFile(self, sys.stdout.fileno(), self.normal)
        self.stderr = OutFile(self, sys.stderr.fileno(), self.error)

        self.sml = None
        self.kill_sml = False
        self.start_sml()

        # Signals
        self.view.connect("key-press-event", self.__key_press_event_cb)
        buffer.connect("mark-set", self.__mark_set_cb)

    def start_sml(self):
        if self.kill_sml:
            return
            
        if self.sml:
            try:
                self.sml.kill()
            except:
                pass
            self.sml = None

        startupInfo = None
        if os.name == 'nt':
            startupInfo = subprocess.STARTUPINFO()
            startupInfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        self.sml = subprocess.Popen(SML_COMMAND,
                                    stdin  = subprocess.PIPE,
                                    stdout = subprocess.PIPE,
                                    stderr = subprocess.PIPE,
                                    shell = False,
                                    startupinfo = startupInfo)

        def transfer_data(from_f, to_f):
            try:
                while True:
                    c = from_f.read(1)
                    if c == '\r': continue
                    if c == '': break
                    to_f.write(c)
            except Exception, e:
                print e
            self.start_sml()
                
        
        stdoutt = threading.Thread(target = transfer_data, args = (self.sml.stdout, self.stdout))
        stdoutt.daemon = True
        stdoutt.start()        
        #stderrt = threading.Thread(target = transfer_data, args = (self.sml.stderr, self.stderr))
        #stderrt.daemon = True
        #stderrt.start()
        
    def do_grab_focus(self):
        self.view.grab_focus()

    def apply_preferences(self, *args):
        config = SMLConsoleConfig()
        self.error.set_property("foreground", config.color_error)
        self.command.set_property("foreground", config.color_command)

    def stop(self):
        self.namespace = None
        self.kill_sml = True
        try:
            self.sml.kill()
        except:
            pass
        self.sml = None

    def __key_press_event_cb(self, view, event):
        modifier_mask = gtk.accelerator_get_default_mod_mask()
        event_state = event.state & modifier_mask

        if (event.keyval == gtk.keysyms.c or \
            event.keyval == gtk.keysyms.d) and \
            event_state == gtk.gdk.CONTROL_MASK:
               self.sml.kill()

        if event.keyval == gtk.keysyms.r and event_state == gtk.gdk.CONTROL_MASK:
            document = self.namespace['window'].get_active_document()
            self.eval( document.get_text( document.get_start_iter(), document.get_end_iter() ) + "\n", display_command = True )

        elif event.keyval == gtk.keysyms.Return and event_state == gtk.gdk.CONTROL_MASK:
            # Get the command
            buffer = view.get_buffer()
            inp_mark = buffer.get_mark("input-line")
            inp = buffer.get_iter_at_mark(inp_mark)
            cur = buffer.get_end_iter()
            line = buffer.get_text(inp, cur)
            self.current_command = self.current_command + line + "\n"
            self.history_add(line)

            # Prepare the new line
            cur = buffer.get_end_iter()
            #buffer.insert(cur, "\n... ")
            cur = buffer.get_end_iter()
            buffer.move_mark(inp_mark, cur)

            # Keep indentation of precendent line
            spaces = re.match(self.__spaces_pattern, line)
            if spaces is not None:
                buffer.insert(cur, line[spaces.start() : spaces.end()])
                cur = buffer.get_end_iter()

            buffer.place_cursor(cur)
            gobject.idle_add(self.scroll_to_end)
            return True

        elif event.keyval == gtk.keysyms.Return:
            # Get the marks
            buffer = view.get_buffer()
            lin_mark = buffer.get_mark("input-line")

            # Get the command line
            lin = buffer.get_iter_at_mark(lin_mark)
            cur = buffer.get_end_iter()
            line = buffer.get_text(lin, cur)
            self.current_command = self.current_command + line + "\n"
            self.history_add(line)

            # Make the line blue
            lin = buffer.get_iter_at_mark(lin_mark)
            buffer.apply_tag(self.command, lin, cur)
            buffer.insert(cur, "\n")

            cur_strip = self.current_command.rstrip()

            # Eval the command
            self.__run(self.current_command)
            self.current_command = ''
            self.block_command = False
            com_mark = ""#">>> "

            # Prepare the new line
            cur = buffer.get_end_iter()
            buffer.move_mark(lin_mark, cur)
            buffer.insert(cur, com_mark)
            cur = buffer.get_end_iter()
            buffer.place_cursor(cur)
            gobject.idle_add(self.scroll_to_end)
            return True

        elif event.keyval == gtk.keysyms.KP_Down or event.keyval == gtk.keysyms.Down:
            # Next entry from history
            view.emit_stop_by_name("key_press_event")
            self.history_down()
            gobject.idle_add(self.scroll_to_end)
            return True

        elif event.keyval == gtk.keysyms.KP_Up or event.keyval == gtk.keysyms.Up:
            # Previous entry from history
            view.emit_stop_by_name("key_press_event")
            self.history_up()
            gobject.idle_add(self.scroll_to_end)
            return True

        elif event.keyval == gtk.keysyms.KP_Left or event.keyval == gtk.keysyms.Left or \
             event.keyval == gtk.keysyms.BackSpace:
            buffer = view.get_buffer()
            inp = buffer.get_iter_at_mark(buffer.get_mark("input-line"))
            cur = buffer.get_iter_at_mark(buffer.get_insert())
            if inp.compare(cur) == 0:
                if not event_state:
                    buffer.place_cursor(inp)
                return True
            return False

        # For the console we enable smart/home end behavior incoditionally
        # since it is useful when editing python

        elif (event.keyval == gtk.keysyms.KP_Home or event.keyval == gtk.keysyms.Home) and \
             event_state == event_state & (gtk.gdk.SHIFT_MASK|gtk.gdk.CONTROL_MASK):
            # Go to the begin of the command instead of the begin of the line
            buffer = view.get_buffer()
            iter = buffer.get_iter_at_mark(buffer.get_mark("input-line"))
            ins = buffer.get_iter_at_mark(buffer.get_insert())

            while iter.get_char().isspace():
                iter.forward_char()

            if iter.equal(ins):
                iter = buffer.get_iter_at_mark(buffer.get_mark("input-line"))

            if event_state & gtk.gdk.SHIFT_MASK:
                buffer.move_mark_by_name("insert", iter)
            else:
                buffer.place_cursor(iter)
            return True

        elif (event.keyval == gtk.keysyms.KP_End or event.keyval == gtk.keysyms.End) and \
             event_state == event_state & (gtk.gdk.SHIFT_MASK|gtk.gdk.CONTROL_MASK):

            buffer = view.get_buffer()
            iter = buffer.get_end_iter()
            ins = buffer.get_iter_at_mark(buffer.get_insert())

            iter.backward_char()

            while iter.get_char().isspace():
                iter.backward_char()

            iter.forward_char()

            if iter.equal(ins):
                iter = buffer.get_end_iter()

            if event_state & gtk.gdk.SHIFT_MASK:
                buffer.move_mark_by_name("insert", iter)
            else:
                buffer.place_cursor(iter)
            return True

    def __mark_set_cb(self, buffer, iter, mark):
        mark_name = mark.get_name()
        if mark_name in ['input', 'input-line', 'tmp-input-line', None]: return
        
        input = buffer.get_iter_at_mark(buffer.get_mark("input-line"))
        pos   = buffer.get_iter_at_mark(buffer.get_insert())
        self.view.set_editable(pos.compare(input) != -1)

    def get_command_line(self):
        buffer = self.view.get_buffer()
        inp = buffer.get_iter_at_mark(buffer.get_mark("input-line"))
        cur = buffer.get_end_iter()
        text = buffer.get_text(inp, cur)
        return text

    def set_command_line(self, command):
        buffer = self.view.get_buffer()
        mark = buffer.get_mark("input-line")
        inp = buffer.get_iter_at_mark(mark)
        cur = buffer.get_end_iter()
        buffer.delete(inp, cur)
        buffer.insert(inp, command)
        self.view.grab_focus()

    def history_add(self, line):
        if line.strip() != '':
            self.history_pos = len(self.history)
            self.history[self.history_pos - 1] = line
            self.history.append('')

    def history_up(self):
        if self.history_pos > 0:
            self.history[self.history_pos] = self.get_command_line()
            self.history_pos = self.history_pos - 1
            self.set_command_line(self.history[self.history_pos])

    def history_down(self):
        if self.history_pos < len(self.history) - 1:
            self.history[self.history_pos] = self.get_command_line()
            self.history_pos = self.history_pos + 1
            self.set_command_line(self.history[self.history_pos])

    def scroll_to_end(self):
        iter = self.view.get_buffer().get_end_iter()
        self.view.scroll_to_iter(iter, 0.0)
        return False

    def write(self, text, tag = None):
        buffer = self.view.get_buffer()
        if tag is None:
            buffer.insert(buffer.get_end_iter(), text)
        else:
            lin = buffer.get_mark("input-line")
            m = buffer.create_mark("tmp-input-line", buffer.get_iter_at_mark(lin), False)
            buffer.insert_with_tags(buffer.get_iter_at_mark(m), text, tag)
            buffer.move_mark(lin, buffer.get_iter_at_mark(m))
            buffer.delete_mark(m)
            self.view.set_editable(True)
        gobject.idle_add(self.scroll_to_end)

    def eval(self, command, display_command = False):
        buffer = self.view.get_buffer()
        lin = buffer.get_mark("input-line")
        buffer.delete(buffer.get_iter_at_mark(lin),
                      buffer.get_end_iter())

        if isinstance(command, list) or isinstance(command, tuple):
            for c in command:
                if display_command:
                    self.write(c + "\n", self.command)
                self.__run(c)
        else:
            if display_command:
                self.write(command + "\n", self.command)
            self.__run(command)

        cur = buffer.get_end_iter()
        buffer.move_mark_by_name("input-line", cur)
        #buffer.insert(cur, ">>> ")
        cur = buffer.get_end_iter()
        buffer.move_mark_by_name("input-line", cur)
        self.view.scroll_to_iter(cur, 0.0)

    def __run(self, command):
        try:
            self.sml.stdin.write(command)
            self.sml.stdin.flush()
        except Exception, e:
            print e
            self.start_sml()
        return

    def destroy(self):
        pass
        #self.sml.terminate()
        #gtk.ScrolledWindow.destroy(self)

class OutFile:
    """A fake output file object. It sends output to a TK test widget,
    and if asked for a file number, returns one set on instance creation"""
    def __init__(self, console, fn, tag):
        self.fn = fn
        self.console = console
        self.tag = tag
    def close(self):         pass
    def flush(self):         pass
    def fileno(self):        return self.fn
    def isatty(self):        return 0
    def read(self, a):       return ''
    def readline(self):      return ''
    def readlines(self):     return []
    def write(self, s):
        gobject.idle_add(self.console.write, s, self.tag)
    def writelines(self, l):
        gobject.idle_add(self.console.write, l, self.tag)
    def seek(self, a):       raise IOError, (29, 'Illegal seek')
    def tell(self):          raise IOError, (29, 'Illegal seek')
    truncate = tell

# ex:et:ts=4:
