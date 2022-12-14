from tkinter.filedialog import asksaveasfilename
import customtkinter
import tkinter as tk
from tkinter import ttk
from exceptions import ParseError
from ui.sidebar import Sidebar
from ui.output import Output
from input_parser import Parser
from chart_generator import ChartGenerator
from ui.message_handler import MessageHandler
import sys
import webbrowser

class App:
    def __init__(self, root):
        self.parser = Parser()
        self.chart_generator = ChartGenerator()
        self.message_handler = MessageHandler(root)
        self.data = None
        self.chart_properties = {}
        self.figure = None

        root.title("PyCharts++")
        # below line throws an exception in linux 
        # root.state("zoomed")
        root.option_add("*tearOff", tk.FALSE)

        # Menubar
        menu_bar = tk.Menu(root)
        root['menu'] = menu_bar
        menu_file = tk.Menu(menu_bar)
        # File menu
        menu_bar.add_cascade(menu=menu_file, label="File")
        menu_file.add_command(label="Save as", command=self.__save_as, underline=0)
        menu_file.add_command(label="Exit", command=sys.exit, underline=0)
        # Help menu
        menu_help = tk.Menu(menu_bar)
        menu_bar.add_cascade(menu=menu_help, label="Help")
        menu_help.add_command(label="Documentation", command=self.__open_documentation, underline=0)

        main_frame = customtkinter.CTkFrame(master=root)
        main_frame.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S), padx=3, pady=12)

        self.sidebar = Sidebar(main_frame, self)
        self.output = Output(main_frame)

        root.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1, minsize=500)
        main_frame.columnconfigure(0, weight=3, minsize=800)
        main_frame.columnconfigure(1, weight=1, minsize=300)

    def menu_action(self):
        print("Menu itme clicked")

    def generate_chart(self, chart_type, file_obj):
        if file_obj == None:
            self.message_handler.show_message("No file selected.", "Error")
        elif file_obj.closed:
            self.message_handler.show_message("File is closed. Please reselect the file.", "Error")
        else:
            try:
                self.data = { "chart_type": chart_type.get(), "nodes": self.parser.parse(file_obj) }
                self.parser.clear_nodes()
                self.figure = self.chart_generator.generate_chart(self.data["chart_type"], self.data["nodes"], self.chart_properties)
                self.output.show_chart(self.figure)
                file_obj.close()
            except ParseError as e:
                self.parser.clear_nodes()
                self.message_handler.show_message(e.message, "Error")

    def update_chart(self):
        if self.figure == None:
            self.message_handler.show_message("Canvas is empty.", "Error")
            return
        if self.data == None:
            self.message_handler.show_message("No data has been read.", "Error")
            return

        self.figure = self.chart_generator.generate_chart(self.data["chart_type"], self.data["nodes"], self.chart_properties)
        self.output.show_chart(self.figure)

    def __save_as(self):
        if not self.figure:
            self.message_handler.show_message("Canvas is empty.", "Error")
            return
        filename = asksaveasfilename(initialfile="untitled.png", defaultextension=".png", filetypes=[("Portable Graphics Format", "*.png"), ("All files", "*.")])
        if filename:
            self.figure.savefig(filename)
            self.message_handler.show_message("Successfully saved.", "Info")
        else:
            self.message_handler.show_message("Save location not selected.", "Error")
    
    def reset_chart(self):
        self.figure = None
        self.output.reset()

    def __open_documentation(self):
        docs_url = "https://pycharts.github.io/pycharts"
        webbrowser.open(docs_url)

        




if __name__=="__main__":
    root = customtkinter.CTk()
    root.protocol("WM_DELETE_WINDOW", sys.exit)
    root.minsize(1480, 720)
    App(root)
    root.mainloop()
