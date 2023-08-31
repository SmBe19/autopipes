import os
import subprocess
import tempfile

from PIL import Image


class UI:
    window_name: str
    wid: str

    def __init__(self, window_name: str):
        self.window_name = window_name

    def focus_window(self) -> None:
        res = subprocess.run(
            ['xdotool', 'search', '--onlyvisible', '--limit', '1', '--sync', '--name', self.window_name],
            stdout=subprocess.PIPE
        )
        self.wid = res.stdout.decode('utf-8').strip()
        subprocess.run(['xdotool', 'windowactivate', '--sync', self.wid])

    def get_screenshot(self) -> Image:
        self.focus_window()
        self.mouse_move(0, 0)
        with tempfile.TemporaryDirectory(prefix='autopipes') as tempdir:
            screenfile = os.path.join(tempdir, 'screen.png')
            subprocess.run(['import', '-silent', '-window', self.wid, screenfile])
            im = Image.open(screenfile)
        return im

    def mouse_move(self, x: int, y: int) -> None:
        subprocess.run(['xdotool', 'mousemove', '--sync', '--window', self.wid, str(x), str(y)])

    def mouse_click(self, x: int, y: int, button: int) -> None:
        subprocess.run(
            ['xdotool',
             'mousemove', '--sync', '--window', self.wid, str(x), str(y),
             'click', '--window', self.wid, str(button)])

    def mouse_drag(self, x1: int, y1: int, x2: int, y2: int, button: int) -> None:
        subprocess.run(
            ['xdotool',
             'mousemove', '--sync', '--window', self.wid, str(x1), str(y1),
             'mousedown', '--window', self.wid, str(button),
             'mousemove', '--sync', '--window', self.wid, str(x2), str(y2),
             'mouseup', '--window', self.wid, str(button)])

    def press_key(self, keycode: str) -> None:
        subprocess.run(['xdotool', 'key', str(keycode)])
