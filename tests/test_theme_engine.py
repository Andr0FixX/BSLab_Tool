import unittest
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import tkinter as tk
from tkinter import ttk
from ui.theme import Theme

class TestThemeEngine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.root.destroy()
        except Exception:
            pass

    def test_theme_colors(self):
        self.assertEqual(Theme.BG_CANVAS, "#0D1117")
        self.assertEqual(Theme.BG_HEADER, "#161B26")
        self.assertEqual(Theme.SURFACE_CARD, "#161D2B")
        self.assertEqual(Theme.BORDER_CARD, "#232D42")
        self.assertEqual(Theme.TABLE_ROW_EVEN, "#131722")
        self.assertEqual(Theme.TABLE_ROW_ODD, "#181E2C")

    def test_font_helpers(self):
        f_ui = Theme.font_ui(size=11)
        f_bold = Theme.font_bold(size=12)
        f_mono = Theme.font_mono(size=10)
        self.assertIsNotNone(f_ui)
        self.assertIsNotNone(f_bold)
        self.assertIsNotNone(f_mono)

    def test_apply_ttk_theme(self):
        style = ttk.Style()
        Theme.apply_ttk_theme(style)
        configured_height = style.lookup("Treeview", "rowheight")
        self.assertEqual(int(configured_height), 28)

if __name__ == "__main__":
    unittest.main()
