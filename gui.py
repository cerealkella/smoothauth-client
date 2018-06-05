import time
import wx
from threading import Thread
from cardreader import CardReader
from auth_broker import badgeRead


class MyThread(Thread):
    """Worker Thread Class."""
    def __init__(self, panel):
        """Init Worker Thread Class."""
        Thread.__init__(self)
        self.panel = panel
        self.sentinel = True
        self.start()    # start the thread

    def run(self):
        """Run Worker Thread."""
        while self.sentinel:
            time.sleep(1)
            wx.CallAfter(self.panel.update)
        print('Thread finished!')


class PanelOne(wx.Panel):
    """"""
    def __init__(self, parent):
        """Constructor"""
        wx.Panel.__init__(self, parent=parent)
        '''
        grid = gridlib.Grid(self)
        grid.CreateGrid(20, 10)
        '''
        # user info
        user_sizer = wx.BoxSizer(wx.HORIZONTAL)

        user_lbl = wx.StaticText(self, label="Username:")
        user_sizer.Add(user_lbl, 0, wx.ALL | wx.CENTER, 5)
        self.user = wx.TextCtrl(self)
        user_sizer.Add(self.user, 0, wx.ALL, 5)

        # pass info
        p_sizer = wx.BoxSizer(wx.HORIZONTAL)

        p_lbl = wx.StaticText(self, label="Password:")
        p_sizer.Add(p_lbl, 0, wx.ALL | wx.CENTER, 5)
        self.password = wx.TextCtrl(self,
                                    style=wx.TE_PASSWORD | wx.TE_PROCESS_ENTER)
        p_sizer.Add(self.password, 0, wx.ALL, 5)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(user_sizer, 0, wx.ALL, 5)
        main_sizer.Add(p_sizer, 0, wx.ALL, 5)

        btn = wx.Button(self, label="Login")
        btn.Bind(wx.EVT_BUTTON, self.onLogin)
        main_sizer.Add(btn, 0, wx.ALL | wx.CENTER, 5)

        self.SetSizer(main_sizer)

    def onLogin(self, event):
        """
        Check credentials and login
        """
        stupid_password = "pa$$w0rd!"
        user_password = self.password.GetValue()
        if user_password == stupid_password:
            print("You are now logged in!")
            pub.sendMessage("frameListener", message="show")
            self.Destroy()
        else:
            print("Username or password is incorrect!")


class PanelTwo(wx.Panel):
    """"""
    def __init__(self, parent):
        """Constructor"""
        wx.Panel.__init__(self, parent=parent)
        self.lbl = wx.StaticText(self, label='')
        self.thread = None

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.c = CardReader()
        if self.c.connected:
            png = wx.Image("resources/tap-badge.png", wx.BITMAP_TYPE_ANY)\
                    .ConvertToBitmap()
        else:
            png = wx.Image("resources/plug-in-usb.png", wx.BITMAP_TYPE_ANY)\
                    .ConvertToBitmap()

        self.image = wx.StaticBitmap(self, -1, png,
                                     (png.GetWidth(), png.GetHeight()))
        main_sizer.AddStretchSpacer()
        main_sizer.Add(self.image, 0, wx.CENTER)
        # main_sizer.Add(btn, 0, wx.CENTER)
        main_sizer.AddStretchSpacer()

        self.SetSizer(main_sizer)

    def start_timer(self):
        self.thread = MyThread(self)

    def stop_timer(self):
        self.thread.sentinel = False

    def update(self):
        '''
        self.count += 1
        self.lbl.SetLabel('Counter: {}'.format(self.count))
        '''
        self.c.read_card_loop(True)
        self.lbl.SetLabel('Badge Read: {}'.format(self.c.badge_num))


class MyForm(wx.Frame):

    def __init__(self):
        wx.Frame.__init__(self, None, wx.ID_ANY,
                          "SmoothAuth")

        self.CreateStatusBar()
        self.SetStatusText("Please Scan Your Badge!")

        self.panel_one = PanelOne(self)
        self.panel_two = PanelTwo(self)
        self.panel_one.Hide()

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.panel_one, 1, wx.EXPAND)
        self.sizer.Add(self.panel_two, 1, wx.EXPAND)
        self.SetSizer(self.sizer)

        menubar = wx.MenuBar()
        fileMenu = wx.Menu()
        switch_panels_menu_item = fileMenu.Append(wx.ID_ANY,
                                                  "Switch Panels",
                                                  "Some text")

        self.Bind(wx.EVT_MENU, self.onSwitchPanels,
                  switch_panels_menu_item)
        self.Bind(wx.EVT_CLOSE, self.on_close)

        menubar.Append(fileMenu, '&File')

        self.panel_two.start_timer()
        self.SetMenuBar(menubar)
        self.Maximize(True)

    def onSwitchPanels(self, event):
        """"""
        if self.panel_one.IsShown():
            self.SetTitle("Panel Two Showing")
            self.panel_one.Hide()
            self.panel_two.Show()
            self.panel_two.start_timer()
        else:
            self.SetTitle("Panel One Showing")
            self.panel_one.Show()
            self.panel_two.stop_timer()
            self.panel_two.Hide()
        self.Layout()

    def on_close(self, event):
        self.panel_two.stop_timer()
        self.panel_two.thread.join()
        self.Destroy()


# Run the program
if __name__ == "__main__":
    app = wx.App(False)
    frame = MyForm()
    frame.Show()
    app.MainLoop()
