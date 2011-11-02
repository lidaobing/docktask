#!/usr/bin/env python
#
#    doctask
#
#    Copyright (C) 2010 LI Daobing <lidaobing@gmail.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''
Track you online tasks with a GTK+ dock application

such as rememberthemilk, google tasks, etc.
'''

import os
import logging
import webbrowser

try:
    import json
except ImportError:
    import simplejson as json

import gtk
import webkit



def getCurrentDesktopOfScreen(screen):
    desktop = 0
    if screen is None:
        screen = gtk.gdk.screen_get_default()

    root = screen.get_root_window()
    if root is None:
        root = gtk.gdk.get_root_window()

    if root is not None:
        res = root.property_get(gtk.gdk.atom_intern("_NET_CURRENT_DESKTOP"))
        if res[0] == 'CARDINAL' and res[1] == 32:
            return res[2][0]
    return desktop
    

def getWorkAreaGeometry(gtkWindow):
    screen = None
    if gtkWindow is not None:
        screen = gtkWindow.get_screen()
    root = None
    screenWidth = 0
    screenHeight = 0
    if screen is None:
        screen = gtk.gdk.screen_get_default()
    if screen is not None:
        screenWidth = screen.get_width()
        screenHeight = screen.get_height()
        root = screen.get_root_window()
    if root is None:
        root = gtk.gdk.screen_get_root_window()

    res = {'x': 0, 'y': 0, 'width': screenWidth, 'height': screenHeight}

    if root is not None:
        desktop = getCurrentDesktopOfScreen(screen)
        data = root.property_get(gtk.gdk.atom_intern("_NET_WORKAREA"))
        if data[0] == 'CARDINAL' and data[1] == 32:
            res['x'] = data[2][desktop*4]
            res['y'] = data[2][desktop*4+1]
            res['width'] = data[2][desktop*4+2]
            res['height'] = data[2][desktop*4+3]
    return res


class StatusIcon(gtk.StatusIcon):
    def __init__(self, dockTaskWindow):
        super(self.__class__, self).__init__()
        self.set_from_stock(gtk.STOCK_INDENT)
        self.dockTaskWindow = dockTaskWindow
        self.connect("activate", self.onActivate)
        self.set_visible(False)

    def onActivate(self, *args):
        self.dockTaskWindow.show_all()
        self.set_visible(False)

class PopupWindow(gtk.Window):
    def __init__(self, url):
        super(self.__class__, self).__init__()
        html = Html()
        html.load_uri(url)
        self.add(html)
        self.set_default_size(400, 300)

class Html(webkit.WebView):
    def __init__(self):
        super(self.__class__, self).__init__()
        #self.connect("open-uri", self.onOpenUri)
        #self.connect("new-window", self.onNewWindow)
        #self.connect("net-state", self.onNetState)
        #self.connect("net-start", self.onNetStart)

    def onOpenUri(self, _html, uri, *args):
        logging.info(uri)
        if uri == 'about:blank':
            return True
        return False

    def onNewWindow(self, _html, retval, *args):
        url = self.get_link_message()
        logging.info(url)
        webbrowser.open(url)

    def onNetState(self, _html, *args):
        logging.info("netstate: %s, %s", hex(args[0]), args[1:])

    def onNetStart(self, _html, *args):
        logging.info("net-start: %s", self.get_location())

    def onEvent(self, _html, *args):
        logging.info(args)

class DockTaskWindow(gtk.Window):
    def __init__(self, config):
        super(self.__class__,self).__init__()
        self.config = config

        self.isDock = True
        self.defaultUrl = None

        rootBox = gtk.VBox()
        rootBox.set_border_width(2)
        
        toolbar = gtk.Toolbar()
        toolbar.set_style(gtk.TOOLBAR_ICONS)
        gtk.icon_size_register('doctasktoolbar', 16, 16)
        toolbar.set_icon_size(gtk.icon_size_from_name('doctasktoolbar'))

        html = Html()

        dockAction = gtk.Action("input", "input", "if you found you can not input in the web page, click here",
                                gtk.STOCK_INDENT)
        homeAction = gtk.Action("home", "home", "return the start page", gtk.STOCK_HOME)
        refreshAction = gtk.Action("refresh", "refresh", "refresh", gtk.STOCK_REFRESH)
        exitAction = gtk.Action("exit", "exit", "exit", gtk.STOCK_QUIT)
        trayAction = gtk.Action("tray", "tray", "minimize to tray", gtk.STOCK_GO_DOWN)
        newUrlAction = gtk.Action("newUrl", "newUrl", "open a new url", gtk.STOCK_JUMP_TO)
        

        toolbar.add(dockAction.create_tool_item())
        toolbar.add(homeAction.create_tool_item())
        urlListToolButton = gtk.MenuToolButton(gtk.STOCK_SELECT_ALL)
        urlListToolButton.set_menu(self._buildUrlMenu())
        toolbar.add(urlListToolButton)
        # toolbar.add(newUrlAction.create_tool_item())
        toolbar.add(refreshAction.create_tool_item())
        toolbar.add(trayAction.create_tool_item())
        toolbar.add(exitAction.create_tool_item())

        rootBox.pack_start(toolbar, False)
        rootBox.pack_start(html)
        rootBox.set_focus_child(html)

        self.add(rootBox)
        self.set_default_size(200, 750)

        self.html = html
        self.statusIcon = StatusIcon(self)

        dockAction.connect("activate", self.onDockButtonClick)
        refreshAction.connect("activate", self.onRefresh)
        exitAction.connect("activate", self.onExit)
        homeAction.connect("activate", self.onHome)
        trayAction.connect("activate", self.onTray)
        newUrlAction.connect("activate", self.onNewUrl)
        self.connect("enter-notify-event", self.onEnterNotifyEvent)
        self.connect("show", self.onShow)

    def _buildUrlMenu(self):
        '''return gtk.Menu'''
        res = gtk.Menu()
        print self.config.urls
        for x in self.config.urls:
            name, url = x
            menuItem = gtk.MenuItem(name)
            menuItem.set_tooltip_text(url)
            menuItem.connect("activate", self._onUrlMenuActivate, url)
            menuItem.show()
            res.append(menuItem)
        print res.get_children()
        return res

    def _onUrlMenuActivate(self, _widget, url):
        self.load_url(url)

    def onHome(self, *args):
        if self.defaultUrl is not None:
            self.html.load_url(self.defaultUrl)

    def load_url(self, url):
        logging.info("load_url: %s", url)
        self.defaultUrl = url
        self.html.load_uri(url)

    def onLeaveNotifyEvent(self, *args):
        pass
        #self.entry.grab_focus()

    def onEnterNotifyEvent(self, *args):
        self.activate_default()

    def onDockButtonClick(self, *args):
        PopupWindow(self.defaultUrl).show_all()

    def onRefresh(self, *args):
        self.html.reload()

    def onExit(self, *args):
        gtk.main_quit()

    def onNewUrl(self, *args):
        pass

    def onWorkingAreaChange(self):
        geo = getWorkAreaGeometry(self)
        self.move(geo['x'], geo['y'])
        self.resize(min(200, geo['width']),
                              geo['height'])
        self.setStrut(geo)

    def setStrut(self, geo):
        strut = [min(200, geo['width']), 0, 0, 0]
        strut_partial = [min(200, geo['width']), 0, 0, 0, geo['y'], geo['y']+geo['height'],0,0,0,0,0,0]
        
        self.window.property_change(
            gtk.gdk.atom_intern("_NET_WM_STRUT"),
            gtk.gdk.atom_intern("CARDINAL"),
            32,
            gtk.gdk.PROP_MODE_REPLACE,
            strut)
        self.window.property_change(
            gtk.gdk.atom_intern("_NET_WM_STRUT_PARTIAL"),
            gtk.gdk.atom_intern("CARDINAL"),
            32,
            gtk.gdk.PROP_MODE_REPLACE,
            strut_partial)

    def onTray(self, *args):
        self.statusIcon.set_visible(True)
        self.hide()

    def onShow(self, *args):
        self.onWorkingAreaChange()

class DockTaskCfg(object):
    def __init__(self):
        self.width = 200
        self.urls = [('google task', 'https://mail.google.com/tasks/ig'),
                     ('remember the milk', 'http://m.rememberthemilk.com/'),
                     ]

    def load(self, ifile):
        if ifile is None:
            return
        data = json.load(ifile)
        self.__dict__.update(data)

    def dump(self, ofile):
        if ofile is None:
            return
        json.dump(self.__dict__, ofile)
        
class DockTaskApp(object):
    def __init__(self):
        self.config = self._loadConfig()
        self.window = DockTaskWindow(self.config)
        self.window.connect("destroy", lambda *args: gtk.main_quit())
        self.window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DOCK)
        #self.window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_NORMAL)

    def start(self):
        self.window.load_url("https://mail.google.com/tasks/ig")
        self.window.show_all()
        gtk.main()

    def _loadConfig(self):
        config = DockTaskCfg()
        path = os.path.expanduser('~/.config/docktask/config')
        if os.path.isfile(path):
            config.load(file(path))
        return config

    def _saveConfig(self):
        path = os.path.expanduser('~/.config/docktask/config')
        self.config.dump(file(path, 'w'))

    def __del__(self):
        self._saveConfig()

def main():
    logging.basicConfig(level=logging.INFO)
    DockTaskCfg().dump(None)
    DockTaskApp().start()

if __name__ == '__main__':
    main()
