import wx
import imageio
import os

from getvid import SakuVid, VidNotFoundError
from booruinfo import BooruInfoPanel
import cmdline
import utils
from renderer import Renderer


class SakutoolApp(wx.App):
    def OnInit(self):
        self.frame = SakutoolFrame()
        self.SetTopWindow(self.frame)
        self.frame.Show()
        return True


class SakutoolFrame(wx.Frame):
    def __init__(self):
        configer = utils.Configer()
        self.path = configer.get_asset_path()

        # --- init GUI ---
        self.size = size = wx.Size(1024, 960)
        self.width, self.height = size.GetWidth(), size.GetHeight()
        self.style = style = wx.NO_BORDER #| wx.CAPTION | wx.CLOSE_BOX | wx.MINIMIZE_BOX
        wx.Frame.__init__(self, parent=None, title='Sakutool v0 -- Niku.KK',
                          pos=wx.DefaultPosition, size=size,
                          style=style)
        self.Centre()
        self.SetCanFocus(False)

        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour(utils.BG_DARK)

        sizer = wx.GridBagSizer(0, 5)

        image_height = self.width*9//16
        self.renderer = Renderer(self.panel, self._pring_play_info, size=(self.width, image_height))

        # TODO timeline panel class
        self.timeline_panel = wx.Panel(self.panel, size=(self.width, 80))
        self.timeline_panel.SetBackgroundColour(utils.BG_LIGHT)
        timeline_title = wx.StaticText(self.timeline_panel, label='Timeline Panel: to be continued...')

        info_height = self.height - image_height - 80 - 20 - 5
        self.cmd_panel = cmdline.CmdPanel(self.panel, self._print_status_bar, size=(200, info_height))
        self.booru_panel = BooruInfoPanel(self.panel, size=(300, info_height))
        self.info_play = wx.StaticText(self.panel, size=(300, info_height), label=' Playing Info \n\n')
        self.info_play.SetForegroundColour(utils.FG_LIGHT)
        self.info_play.SetFont(wx.Font(9, family=wx.FONTFAMILY_MODERN,
                                       style=wx.FONTSTYLE_NORMAL, weight=wx.FONTWEIGHT_NORMAL))

        self.status_bar = wx.StaticText(self.panel, size=(self.width, 20))
        self.status_bar.SetBackgroundColour('black')
        self.status_bar.SetForegroundColour(utils.FG_LIGHT)
        self.status_bar.SetFont(wx.Font(9, family=wx.FONTFAMILY_MODERN,
                                        style=wx.FONTSTYLE_NORMAL, weight=wx.FONTWEIGHT_NORMAL))

        sizer.Add(self.renderer, pos=(0, 0), span=(1, 3), flag=wx.ALL, border=0)
        sizer.Add(self.timeline_panel, pos=(1, 0), span=(1, 3), flag=wx.BOTTOM, border=5)
        sizer.Add(self.cmd_panel, pos=(2, 0), flag=wx.ALL | wx.ALIGN_BOTTOM, border=0)
        sizer.Add(self.booru_panel, pos=(2, 1), flag=wx.LEFT | wx.EXPAND, border=5)
        sizer.Add(self.info_play, pos=(2, 2), flag=wx.LEFT | wx.EXPAND, border=5)
        sizer.Add(self.status_bar, pos=(3, 0), span=(1, 3), flag=wx.ALL, border=0)

        self.renderer.Bind(wx.EVT_KEY_DOWN, self._onkeydown)
        self.timeline_panel.Bind(wx.EVT_KEY_DOWN, self._onkeydown)
        self.cmd_panel.Bind(wx.EVT_KEY_DOWN, self._onkeydown)
        self.booru_panel.Bind(wx.EVT_KEY_DOWN, self._onkeydown)
        self.info_play.Bind(wx.EVT_KEY_DOWN, self._onkeydown)
        self.status_bar.Bind(wx.EVT_KEY_DOWN, self._onkeydown)

        # self.timer = wx.Timer(self)
        # self.Bind(wx.EVT_TIMER, self._ontimer, self.timer)

        # --- data
        # self.path = './asset/'
        self.vid = None

        self.panel.SetSizerAndFit(sizer)
        self.build_cmd_panel()
        self._booru_panel_refresh()

    def _onkeydown(self, event):
        keycode = event.GetKeyCode()
        shiftdown = event.ShiftDown()
        keycode = cmdline.reformat(keycode, shiftdown)
        # print(keycode)
        self.cmd_panel.operate(keycode)

    def _booru_panel_refresh(self):
        if self.vid:
            self.booru_panel.update(info=self.vid.booru_info)

    # handlers
    def _pring_play_info(self, s):
        self.info_play.SetLabel(s)

    def _print_status_bar(self, s):
        # self.SetStatusText(s)
        self.status_bar.SetLabel(s)

    # --- ---
    def _load_vid(self, booru_id):
        self.renderer.stop()
        try:
            self.vid = SakuVid(booru_id, self.path, maxsize=self.renderer.size)
            self.booru_id = booru_id

            self.renderer.load_vid(self.vid)
            self._booru_panel_refresh()

        except VidNotFoundError:
            self.SetStatusText('Booru ID Not Found..')

    # --- save
    def save_image(self):
        if self.vid:
            self.renderer.pause()
            uri = self.path+'{}/'.format(self.vid.booru_id)
            os.makedirs(uri, exist_ok=True)
            index = self.vid.cur_frame_index
            uri += '{}.jpg'.format(index)
            if not os.path.exists(uri):
                im = self.vid.vid_arr[index]
                imageio.imwrite(uri=uri, im=im)
            self.renderer.next_frame()

    # build menu
    def build_cmd_panel(self):
        cmd_menu_root = self.cmd_panel.menu_root
        cmd_menu_booru_input = cmdline.CmdInput(parent=cmd_menu_root, name='booru input',
                                                func=self._load_vid, allow=cmdline.is_num)

        cmd_menu_root.new_menu_item(name='get vid', key='i', ptr=cmd_menu_booru_input, helpdoc='input booru id.')
        cmd_menu_root.new_func_item(name='play/stop', key=' ', ptr=self.renderer.play_pause)
        cmd_menu_root.new_func_item(name='last frame', key='j', ptr=self.renderer.last_frame)
        cmd_menu_root.new_func_item(name='next frame', key='k', ptr=self.renderer.next_frame)
        cmd_menu_root.new_func_item(name='switch fps', key='f', ptr=self.renderer.switch_fps, helpdoc='24/12/6')
        cmd_menu_root.new_func_item(name='save jpg', key='s', ptr=self.save_image, helpdoc='...')
        cmd_menu_root.new_func_item(name='exit', key='q', ptr=self.exit)

        self.cmd_panel.refresh_info()
        return

    def exit(self):
        self.renderer.stop()
        wx.Exit()


if __name__ == '__main__':
    app = SakutoolApp(False)
    app.MainLoop()
