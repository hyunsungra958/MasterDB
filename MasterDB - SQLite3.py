from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
from tkinter import simpledialog
from tkinter.ttk import Treeview
from tkinter.ttk import Combobox
from tkinter.ttk import Progressbar
from tkinter.ttk import Scrollbar
from threading import Thread
import sqlite3
import traceback
import os

class DB:
    def __init__(self, file:str):
        if not os.path.exists(file):
            raise FileExistsError
        self.OBJ = sqlite3.connect(file)
    def execute(self, command):
        self.cursor = self.OBJ.cursor()
        self.cursor.execute(command)
        result = self.cursor.fetchall()
        return result
    def getTables(self):
        return self.execute("""SELECT name FROM sqlite_master WHERE type='table';""")
    def getColumns(self, table):
        return self.execute(f"""PRAGMA table_info({table});""")
    def getAll(self, table):
        return self.execute(f"""SELECT * FROM {table}""")

class Convert:
    def __init__(self, file, table):
        self.RESULT = []
        self.FILE = str(file)
        self.TABLE = str(table)
        self.OBJ = DB(self.FILE)
        self.COLUMNS = [str(data[1]) for data in self.OBJ.getColumns(self.TABLE)]
        self.DATA = self.OBJ.getAll(self.TABLE)
        for data in self.DATA:
            DATA = {}
            idx = 0
            for column in self.COLUMNS:
                DATA[column] = data[idx]
                idx += 1
            self.RESULT.append(DATA)
    def result(self):
        return self.RESULT

class UI:
    def __init__(self):
        self.root = Tk()
        self.root.title("MasterDB")
        self.root.state("zoomed")

        self.File = "None"
        self.Table = "None"
        self.Page = 0
        self.DataPerPage = 25
        self.MenuPadx = 5

        self.HeadFrame = Frame(self.root)
        self.HeadFrame.pack(fill=BOTH)

        self.MainFrame = Frame(self.root)
        self.MainFrame.pack(fill=BOTH, expand=True)

        self.FileFrame = LabelFrame(self.HeadFrame, relief="solid", borderwidth=1, text="File")
        self.FileFrame.pack(side="left", fill=BOTH, padx=self.MenuPadx)

        self.FileLabel = Label(self.FileFrame, text=self.File)
        self.FileLabel.pack(fill=BOTH, side="left")

        self.FileLoadButton = Button(self.FileFrame, text="...", command=self.FileLoader)
        self.FileLoadButton.pack(side="left")

        self.PageFrame = LabelFrame(self.HeadFrame, relief="solid", borderwidth=1, text="Pages")
        self.PageFrame.pack(side="left", fill=BOTH, padx=self.MenuPadx)

        self.PageLabel = Label(self.PageFrame, text=f"{self.Page*self.DataPerPage}~{self.Page*self.DataPerPage+self.DataPerPage}")
        self.PageLabel.pack(side="left")

        self.Pages = Combobox(self.PageFrame, values=["0"], state="readonly")
        self.Pages.bind("<<ComboboxSelected>>", self.page_update)
        self.Pages.current(0)
        self.Pages.pack(side="left", fill=BOTH)

        self.DataPerPageButton = Button(self.PageFrame, text="...", command=self.dataperpage_update)
        self.DataPerPageButton.pack(side="left")

        self.ExecutorFrame = LabelFrame(self.HeadFrame, text="SQL Script", relief="solid", borderwidth=1)
        self.ExecutorFrame.pack(fill=BOTH, side="right")

        self.Executor = Entry(self.ExecutorFrame, width=60, font=("", 10))
        self.Executor.insert(END, f"""SELECT * FROM {self.Table}""")
        self.Executor.bind("<Return>", self.update)
        self.Executor.pack(side="right")
        
        self.BodyFrame = Frame(self.MainFrame)
        self.BodyFrame.pack(fill=BOTH, expand=True)

        self.TablesFrame = LabelFrame(self.BodyFrame, relief="solid", borderwidth=1, text="Tables")
        self.TablesFrame.pack(side="right", fill=BOTH, padx=self.MenuPadx)

        self.Tables = Listbox(self.TablesFrame, height=1)
        self.Tables.bind("<Double-1>", self.LoadOneTable)
        self.Tables.pack(side="right", fill=BOTH)

        self.DataBaseFrame = Frame(self.BodyFrame)
        self.DataBaseFrame.pack(fill=BOTH, expand=True, side="left")

        self.DataBase = Treeview(self.DataBaseFrame)
        self.DataBase.column("#0", anchor="w", width=0, stretch=NO)
        self.DataBase.heading("#0", anchor="w", text="Marker")
        self.DataBase.pack(fill=BOTH, expand=True, side="left")

        self.Scroller = Scrollbar(self.DataBaseFrame, command=self.DataBase.yview)
        self.Scroller.pack(side="right", fill="y")

        self.DataBase.config(yscrollcommand=self.Scroller.set)

        self.root.mainloop()
    def LoadAll(self):
        try:
            self.DataBase.destroy()
            self.DataBase = Treeview(self.DataBaseFrame)
            self.DataBase.column("#0", anchor="w", width=0, stretch=NO)
            self.DataBase.heading("#0", anchor="w", text="Marker")
            self.DataBase.pack(fill=BOTH, expand=True, side="left")
            self.DataBase.config(yscrollcommand=self.Scroller.set)
            self.DataBase.bind("<Double-1>", self.detailed_info)
            self.Scroller.config(command=self.DataBase.yview)
            OBJ = DB(self.File)
            result = OBJ.execute(self.Executor.get())
            columns = [desc[0] for desc in OBJ.cursor.description]
            self.DataBase["columns"] = columns
            self.DataBase["displaycolumns"] = columns
            self.TotalDataCount = len(result)
            total_pages = (self.TotalDataCount + self.DataPerPage - 1) // self.DataPerPage
            self.Pages["values"] = [str(i) for i in range(total_pages)]
            for column in columns:
                self.DataBase.column(column, anchor="w", stretch=YES)
                self.DataBase.heading(column, text=column, anchor="w")
            idx = 0
            self.PageLabel.config(text=f"{self.Page*self.DataPerPage}~{self.Page*self.DataPerPage+self.DataPerPage}")
            for row in result[self.Page*self.DataPerPage:self.Page*self.DataPerPage+self.DataPerPage]:
                if idx > self.DataPerPage:
                    break
                idx += 1
                self.DataBase.insert("", END, text=str(len(self.DataBase.get_children())+1), values=[str(data) for data in row])
        except:
            messagebox.showerror("Error", traceback.format_exc())
    def LoadTables(self):
        self.Tables.delete(0, END)
        for item in [str(table[0]) for table in DB(self.File).getTables()]:
            self.Tables.insert(END, item)
    def LoadOneTable(self, evt):
        self.Table = str(self.Tables.get(ANCHOR))
        self.Executor.delete(0, END)
        self.Executor.insert(END, f"""SELECT * FROM {self.Table}""")
        self.update("tableload")
    def FileLoader(self):
        try:
            self.File = filedialog.askopenfilename(title="DB File", filetypes=[("Database File", "*.db"),])
            self.FileLabel.config(text=self.File)
            self.LoadTables()
            self.Table = [str(table[0]) for table in DB(self.File).getTables()][0]
            self.Executor.delete(0, END)
            self.Executor.insert(END, f"""SELECT * FROM {self.Table}""")
            self.update("fileload")
        except:
            messagebox.showerror("Error", traceback.format_exc())
    def page_update(self, evt):
        self.Page = int(self.Pages.get())
        self.update("pageload")
    def dataperpage_update(self):
        try:
            self.DataPerPage = int(simpledialog.askstring("AMOUNT", "Enter the max data amount per pages"))
            self.update("pageload")
        except:
            messagebox.showerror("Error", traceback.format_exc())
    def update(self, evt):
        t = Thread(target=self.update_handler)
        t.daemon = True
        t.start()
    def update_handler(self):
        t = Thread(target=self.LoadAll())
        t.daemon = True
        t.start()
    def detailed_info(self, evt):
        try:
            Item = self.DataBase.item(self.DataBase.selection())
            InfoFrame = Toplevel(self.root)
            InfoFrame.title(f"Data for {Item['text']}")
            idx = 0
            idx2 = 0
            MainFrame = Frame(InfoFrame)
            MainFrame.pack(side="left", fill=BOTH, expand=True)
            for column in [str(data) for data in self.DataBase["columns"]]:
                if idx2 > 30:
                    MainFrame = Frame(InfoFrame)
                    MainFrame.pack(side="left", fill=BOTH, expand=True)
                    idx2 = 0
                DataFrame = Frame(MainFrame)
                DataFrame.pack(fill=BOTH)
                DataLabel = Label(DataFrame, text=f"{column}: ", anchor="w")
                DataLabel.pack(side="left", fill=BOTH)
                Data = Entry(DataFrame, width=60)
                Data.pack(fill=BOTH, side="right")
                Data.insert(END, Item["values"][idx])
                idx += 1
                idx2 += 1
        except:
            messagebox.showerror("Error", traceback.format_exc())

UI()