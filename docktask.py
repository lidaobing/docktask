#!/usr/bin/env python

import os
import gtk
import gtkmozembed


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


class PopupWindow(gtk.Window):
    def __init__(self, url):
        super(self.__class__, self).__init__()
        html = gtkmozembed.MozEmbed()
        html.load_url(url)
        self.add(html)
        self.set_default_size(400, 300)
        

class DockTaskWindow(gtk.Window):
    def __init__(self):
        super(self.__class__,self).__init__()

        self.isDock = True
        self.defaultUrl = None

        rootBox = gtk.VBox()
        rootBox.set_border_width(2)
        
        toolbar = gtk.Toolbar()
        html = gtkmozembed.MozEmbed()

        dockAction = gtk.Action("input", "input", "if you found you can not input in the web page, click here",
                                gtk.STOCK_INDENT)
        homeAction = gtk.Action("home", "home", "return the start page", gtk.STOCK_HOME)
        refreshAction = gtk.Action("refresh", "refresh", "refresh", gtk.STOCK_REFRESH)
        exitAction = gtk.Action("exit", "exit", "exit", gtk.STOCK_QUIT)

        toolbar.add(dockAction.create_tool_item())
        toolbar.add(homeAction.create_tool_item())
        toolbar.add(refreshAction.create_tool_item())
        toolbar.add(exitAction.create_tool_item())

        rootBox.pack_start(toolbar, False)
        rootBox.pack_start(html)
        rootBox.set_focus_child(html)

        self.add(rootBox)
        self.set_default_size(200, 750)

        self.html = html

        dockAction.connect("activate", self.onDockButtonClick)
        refreshAction.connect("activate", self.onRefresh)
        exitAction.connect("activate", self.onExit)
        homeAction.connect("activate", self.onHome)

    def onHome(self, *args):
        if self.defaultUrl is not None:
            self.html.load_url(self.defaultUrl)

    def load_url(self, url):
        self.defaultUrl = url
        self.html.load_url(url)

    def onLeaveNotifyEvent(self, *args):
        pass
        #self.entry.grab_focus()

    def onEnterNotifyEvent(self, *args):
        self.entry.grab_focus()

    def onDockButtonClick(self, *args):
        PopupWindow(self.html.get_location()).show_all()

    def onRefresh(self, *args):
        self.html.reload(gtkmozembed.FLAG_RELOADNORMAL)

    def onExit(self, *args):
        gtk.main_quit()

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

class DockTaskApp(object):
    def __init__(self):
        self._initMozilla()
        self.window = DockTaskWindow()
        self.window.connect("destroy", lambda *args: gtk.main_quit())
        self.window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DOCK)

    def _initMozilla(self):
        path = os.path.expanduser('~/.config/docktask/mozilla')
        if not os.path.isdir(path):
            os.makedirs(path)
        gtkmozembed.set_profile_path(path, "default")
    
    def start(self):
        self.window.show_all();
        self.window.onWorkingAreaChange();
        #self.window.onHome()
        self.window.load_url("https://mail.google.com/tasks/ig")
        #self.window.load_url("https://m.rememberthemilk.com/")
        gtk.main();


def main():
    DockTaskApp().start()

if __name__ == '__main__':
    main()
