from unittest import TestCase
import os
from CutFileHandler import CutFileHandler
from Segmenter.BreakPointDetector import BreakPointDetector
from Visualizer import Visualizer


class TestProcessedDataHandler(TestCase):
    def setUp(self):
        self.breakpointDetector = BreakPointDetector()
        self.visualizer = Visualizer()
        self.zone_colors = ['#FFE5E5', '#E5FFE5', '#E5E5FF', '#FFFFE5']  # Light red, green, blue, yellow

    # def test_gen1_cutfile_processing(self) -> None:
    #     filepath = r"C:\Data\JorgensData\4TPI ACME Thread_P550_266RL-22SA01F040 1020.cut"
    #     self.cutfile_handler = CutFileHandler(is_gen2=False, debug=True)
    #     self.cutfile_handler.process_file(filepath, resolution_ms=500)
    #     df = self.cutfile_handler.df_sync
    #     fig = self.visualizer.lineplot(df, line_color="white", line_width=.5, use_plotly=False)
    #     fig.show()
    #     fig.show()

    def test_gen2_cutfile_processing(self):
        # self.filepath = r"C:\Data\MissyDataSet\Missy_Disc2\CutFiles\CoroPlus_241008-133957.cut"
        folderpath = r"C:\Data\MissyDataSet\Missy_Disc2\CutFiles"
        figpath = os.path.join(os.getcwd(), "fig")
        files = os.listdir(folderpath)
        files = [os.path.join(folderpath, file) for file in files if file.endswith('.cut')]
        # files = files[0]
        files = files[:3]
        self.cutfile_handler = CutFileHandler(is_gen2=True, debug=False)
        for filepath in files:
            self.cutfile_handler.process_file(filepath, resolution_ms=500)
            # fig = self.visualizer.lineplot(self.cutfile_handler.df_sync, line_color="black", line_width=.5, use_plotly=False)
            fig = self.visualizer.lineplot(self.cutfile_handler.df_sync, line_color="black", text_color="black",
                                           line_width=.5, use_plotly=True)
            fig.write_html(os.path.join(figpath, os.path.basename(filepath) + ".html"))

