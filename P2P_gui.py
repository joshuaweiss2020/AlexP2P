from xmlrpc.client import ServerProxy, Fault
from cmd import Cmd
from os import listdir
from threading import Thread

from os.path import join, isfile
import os
import myClient
import sys
from tkinter import *
# from tkinter.ttk import *
import tkinter.filedialog
import tkinter.scrolledtext
import tkinter.messagebox as messagebox
from tkinter import ttk
from myUtils import *
import p2pCmd
import socket
import json
import traceback
from functools import wraps

class Root():
	def __init__(self, shape):  # shape为长*宽元组
		self.wnd = Tk()
		self.shape = shape
		self.wnd.title("Alex P2P 文件传送器")
		screenwidth = self.wnd.winfo_screenwidth()
		screenheight = self.wnd.winfo_screenheight()
		alignstr = '%dx%d+%d+%d' % (
			shape[0], shape[1], (screenwidth - shape[0]) / 2, (screenheight - shape[1]) / 2)  # 屏幕居中
		self.wnd.geometry(alignstr)
		self.wnd.resizable(width=False, height=False)
		self.notebook = ttk.Notebook(self.wnd, width=self.shape[0], height=self.shape[1], style="basic.TNotebook", )
		self.notebook.pack()
		self.notebook.bind("<<NotebookTabChanged>>", self.tabChoosed)


		self.widgets = Widgets(self)
		self.buttonShape = (100, 30)
		# self.buttonPad = ()
		self.tabShape = (self.shape[0], self.shape[1]) #- self.buttonShape[1])
		self.myClient, self.myCmd, self.PTab , self.clientName , self.progressBar= None, None, None, None, None

		self.style = ttk.Style()
		self.initStyles()

	def tabChoosed(self,*args):
		tabId = self.notebook.select()
		index = self.notebook.index(tabId)
		self.widgets.tabs[index].show()


	def initStyles(self):
		self.font_label = 12
		self.font_text = 12
		font_label = ("黑体", 0-self.font_label)
		font_text = ("黑体", 0-self.font_text)

		self.style.configure("basic.TLabel", foreground="black", background="lightgray", font=font_label)
		self.style.configure("basic.TButton", foreground="black", background="lightgray", relief=GROOVE,font=font_label)

		self.style.configure("basic.TEntry", foreground="black", background="lightgray", relief=GROOVE, font=font_text)
		self.style.configure("basic.TCombobox", foreground="black", background="lightgray", relief=GROOVE, font=font_text)



	def connServer(self):
		setupTab = self.widgets.tabs[0]
		downloadTab = self.widgets.tabs[1]
		print(downloadTab.name)
		clientName = setupTab.clientNameVal.get()
		self.clientName = clientName
		if not clientName or clientName == "":
			self.PTab.info("终端名称为空，无法连接远程设备")
			return 0
		else:
			try:
				if not self.myClient or not self.myCmd or clientName != setupTab.clientNameInit :
					self.myClient, self.myCmd = p2pCmd.gui_main(setupTab)
					self.myClient.root = self
					self.myCmd.root = self
				else:
					self.myClient.clientName = clientName
					self.myClient.updateClientInfo()

			except Exception as e:
				self.PTab.info("连接远程设备出错，请检查配置信息 出错信息:" + str(e))
				traceback.print_exc()
				return 0
			self.PTab.info("连接成功，可以传输或同步文件")
			#获取客户端列表
			i = 0
			clientList = self.myCmd.do_getCl()

			downloadTab.show()
			downloadTab.connClient["values"] = tuple(clientList.keys())
			downloadTab.connClient.current(1)

			self.notebook.select(1)

			return 1





class Widgets():  # Widgets= PButton+PTab
	def __init__(self, root):
		self.names = {"设置": 0, "传输": 1, "同步": 2}
		self.buttons = []
		self.tabs = []


class PButton():
	def __init__(self, root, name):
		self.name = name
		self.root = root
		self.shape = root.buttonShape
		#		self.button = Button(self.root.wnd,text=name,font=("黑体",14),command=self.run1,width= len(name)*2,height=1)
		self.button = Button(self.root.wnd, bitmap="gray12", text=" " + name, font=("黑体", 14),
		                     command=self.choosed, width=self.shape[0], height=self.shape[1], compound=LEFT, anchor=W,
		                     relief=GROOVE, padx=15, pady=5)

		self.order = root.widgets.names[name]

		self.root.widgets.buttons.append(self)

		self.show()

	def show(self):
		self.button.place(relx=(self.order * (self.shape[0])) / self.root.shape[0], rely=0)

	def choosed(self):
		for btn in self.root.widgets.buttons:
			btn.button.configure(bg="SystemButtonFace", bitmap="gray12")
		self.button.configure(bg='lightgray', bitmap='gray75')
		for tab in self.root.widgets.tabs:
			if tab.name == self.name:
				tab.show()
				break


class PTab():
	def __init__(self, root, name):
		self.name = name
		self.root = root
		self.shape = root.tabShape
		self.order = root.widgets.names[name]
		self.tab = Frame(self.root.notebook, width=root.shape[0], height=root.shape[1]-30, bd=2, relief=FLAT,
		                 bg="lightgray")

		self.root.PTab = self
		self.root.widgets.tabs.append(self)
		self.root.notebook.add(self.tab, text=self.name)

		self.lSpace = 10  # 距左边界的距离
		self.top = 0  # 顶部起始位置

		self.hSpace = 10  # 纵向间隔



	def show(self):

		# for pTab in self.root.widgets.tabs:
		# 	pTab.tab.place_forget()


		#self.tab.place(relx=0, rely=0) # self.root.buttonShape[1] / self.root.shape[1])
		# self.top = int(self.tab.place_info()["y"])

		self.fill()
		self.readInfo()


	def info(self, msg):
		self.root.infoList.insert(1.0, nowStr() + " " + msg + "...\n")

	def showEx(self):  # 用于在GUI中显示异常信息的装饰器
		def decorator(fn):
			@wraps(fn)
			def showFault(*args, **kwargs):
				try:
					return fn(*args, **kwargs)
				except Fault as f:
					self.info("远程调用异常: ["+fn.__name__+"]:"+str(f))
				# traceback.print_exc()
				except Exception as e:
					self.info("本地调用异常：["+fn.__name__+"]:" +str(e))

			return showFault

		return decorator


	def fill(self):
		pass

	def readInfo(self):
		pass

	def updateInfo(self):
		pass

	def connClient(self, clientName):
		pass



class InfoTab():
	def __init__(self, root):
		self.name = "状态信息"
		self.root = root
		self.fill()

	def fill(self):

		rowX = 0
		rowY = self.root.shape[1] - 80
		self.infoFrame = ttk.LabelFrame(self.root.wnd , width=self.root.shape[0] ,text='状态信息', height=40)

		self.infoList = tkinter.scrolledtext.ScrolledText(self.infoFrame,
		                                                  fg='black', bg='lightgray', font=("黑体", -10), relief=GROOVE,
		                                                  width=154, height=3)

		self.root.infoList = self.infoList

		self.root.infoList.insert(1.0, nowStr() + " 欢迎使用Alex P2P 文件传送器\n")

		# h = self.infoList.winfo_reqwidth()
		# print("h",h)
		# h = self.root.infoList.winfo_width()
		# print("h", h)

		# self.infoFrame.configure(height=h)
		self.infoFrame.place(x=0,y=rowY)
		self.infoList.pack()







class SetupTab(PTab):
	def __init__(self, root):
		self.name = list(root.widgets.names.keys())[0]
		PTab.__init__(self, root, self.name)

	def fill(self):

		# 设定终端名称
		self.clientNameVal = StringVar()
		hostname = socket.getfqdn(socket.gethostname())
		hostname = hostname.replace(".", "_")
		hostname = hostname.replace("-", "_")
		hostname = hostname.replace(" ", "_")
		if not self.clientNameVal.get():
			self.clientNameVal.set(hostname[:10])
			self.clientNameInit = hostname[:10]
		helpX = self.lSpace + 58 * self.lSpace

		rowY = self.top + self.hSpace

		self.clientName_l = ttk.Label(self.tab, text='终端名称:', style="basic.TLabel")
		self.clientName_l.place(x=self.lSpace, y=rowY)

		self.clientName = ttk.Entry(self.tab, style='basic.TEntry',
		                        textvariable=self.clientNameVal)
		self.clientName.place(x=self.lSpace + 10 * self.lSpace, y=rowY)

		self.clientName_help = ttk.Label(self.tab, text='【作为远程访问的标识】', style="basic.TLabel")
		self.clientName_help.place(x=helpX, y=rowY)

		# 设定下载文件夹
		self.downloadFolderVal = StringVar()
		if not self.downloadFolderVal.get():
			self.downloadFolderVal.set(sys.path[0] + os.sep + self.clientNameVal.get())

		rowY = rowY + self.hSpace * 3
		self.downloadFolder_l = ttk.Label(self.tab, text='下载文件夹:', style="basic.TLabel")
		self.downloadFolder_l.place(x=self.lSpace, y=rowY)

		self.downloadFolder = ttk.Entry(self.tab, style='basic.TEntry',
		                            textvariable=self.downloadFolderVal, width=50)
		self.downloadFolder.place(x=self.lSpace + 10 * self.lSpace, y=rowY)

		self.downloadFolder_btn = ttk.Button(self.tab, text="选择...", style="basic.TButton",
		                                 command=lambda: self.chooseFolder(self.downloadFolderVal))
		x = int(self.downloadFolder.place_info()["x"]) + self.downloadFolder.winfo_reqwidth() + 5
		self.downloadFolder_btn.place(x=x, y=rowY)

		self.downloadFolder_help = ttk.Label(self.tab, text='【设定下载文件所存放的位置】', style="basic.TLabel")
		self.downloadFolder_help.place(x=helpX, y=rowY)

		# 设定同步文件夹
		self.syncFolderVal = StringVar()
		if not self.syncFolderVal.get():
			self.syncFolderVal.set(sys.path[0] + os.sep + "sync_" + self.clientNameVal.get())

		rowY = rowY + self.hSpace * 3

		self.syncFolder_l = ttk.Label(self.tab, text='同步文件夹:', style="basic.TLabel")
		self.syncFolder_l.place(x=self.lSpace, y=rowY)

		self.syncFolder = ttk.Entry(self.tab, style='basic.TEntry',
		                        textvariable=self.syncFolderVal, width=50)
		self.syncFolder.place(x=self.lSpace + 10 * self.lSpace, y=rowY)

		self.syncFolder_btn = ttk.Button(self.tab, text="选择...", style="basic.TButton",
		                             command=lambda: self.chooseFolder(self.syncFolderVal))
		x = int(self.syncFolder.place_info()["x"]) + self.syncFolder.winfo_reqwidth() + 5

		self.syncFolder_btn.place(x=x, y=rowY)

		self.syncFolder_help = ttk.Label(self.tab, text='【设定用于同步的文件夹】', style="basic.TLabel")
		self.syncFolder_help.place(x=helpX, y=rowY)

		# 设定访问密码
		rowY = rowY + self.hSpace * 3
		self.passwordVal = StringVar()
		if not self.passwordVal.get(): self.passwordVal.set("000000")

		self.password_l = ttk.Label(self.tab, text='访问密码:', style="basic.TLabel")
		self.password_l.place(x=self.lSpace, y=rowY)

		self.password = ttk.Entry(self.tab, style='basic.TEntry',
		                      textvariable=self.passwordVal, width=20, show="*")
		self.password.place(x=self.lSpace + 10 * self.lSpace, y=rowY)

		self.password_help = ttk.Label(self.tab, text='【远程访问本机的密码】', style="basic.TLabel")
		self.password_help.place(x=helpX, y=rowY)

		# 设定代理服务器
		rowY = rowY + self.hSpace * 6
		self.proxy_cbVal = IntVar()
		self.proxy_cbVal.set(0)

		self.proxy_cb = Checkbutton(self.tab, text='是否使用代理服务器', onvalue=1, offvalue=0, variable=self.proxy_cbVal,
		                            fg='black', bg='lightgray', font=("黑体", 12), command=self.proxyCheck)
		self.proxy_cb.place(x=self.lSpace, y=rowY)

		# 设定代理服务器地址
		rowY = rowY + self.hSpace * 3
		self.proxyIPVal = StringVar()
		self.proxyIPVal.set("10.191.113.100")

		self.proxyIP_l = ttk.Label(self.tab, text='IP:', style="basic.TLabel")
		self.proxyIP_l.place(x=self.lSpace, y=rowY)

		self.proxyIP = ttk.Entry(self.tab, style='basic.TEntry',
		                     textvariable=self.proxyIPVal, width=16)
		self.proxyIP.place(x=self.lSpace + 10 * self.lSpace, y=rowY)

		self.proxyIP_help = ttk.Label(self.tab, text='【格式：XX.XX.XX.XX】', style="basic.TLabel")
		self.proxyIP_help.place(x=helpX, y=rowY)

		# 设定端口
		rowY = rowY + self.hSpace * 3
		self.proxyPortVal = StringVar()
		self.proxyPortVal.set("8002")

		self.proxyPort_l = ttk.Label(self.tab, text='端口:', style="basic.TLabel")
		self.proxyPort_l.place(x=self.lSpace, y=rowY)

		self.proxyPort = ttk.Entry(self.tab, style='basic.TEntry',
		                       textvariable=self.proxyPortVal, width=6)
		self.proxyPort.place(x=self.lSpace + 10 * self.lSpace, y=rowY)

		self.proxyPort_help = ttk.Label(self.tab, text='【格式：XXXX】', style="basic.TLabel")
		self.proxyPort_help.place(x=helpX, y=rowY)

		# 设定用户名
		rowY = rowY + self.hSpace * 3
		self.proxyUserVal = StringVar()
		self.proxyUserVal.set("weijiaohua-004")

		self.proxyUser_l = ttk.Label(self.tab, text='用户名:', style="basic.TLabel")
		self.proxyUser_l.place(x=self.lSpace, y=rowY)

		self.proxyUser = ttk.Entry(self.tab, style='basic.TEntry',
		                       textvariable=self.proxyUserVal, width=20)
		self.proxyUser.place(x=self.lSpace + 10 * self.lSpace, y=rowY)

		self.proxyUser_help = ttk.Label(self.tab, text='【可以为空】', style="basic.TLabel")
		self.proxyUser_help.place(x=helpX, y=rowY)

		# 设定用户密码
		rowY = rowY + self.hSpace * 3
		self.proxyPasswordVal = StringVar()
		self.proxyPasswordVal.set("Cpic2190#")

		self.proxyPassword_l = ttk.Label(self.tab, text='用户密码:', style="basic.TLabel")
		self.proxyPassword_l.place(x=self.lSpace, y=rowY)

		self.proxyPassword = ttk.Entry(self.tab, style='basic.TEntry',
		                           textvariable=self.proxyPasswordVal, width=20, show="*")
		self.proxyPassword.place(x=self.lSpace + 10 * self.lSpace, y=rowY)

		self.proxyPassword_help = ttk.Label(self.tab, text='【可以为空】', style="basic.TLabel")
		self.proxyPassword_help.place(x=helpX, y=rowY)

		self.proxyCheck()
		# 恢复默认&确认修改
		rowY = rowY + self.hSpace * 6
		self.reset_btn = ttk.Button( self.tab, text="恢复默认", style="basic.TButton",
		                        command=lambda: self.updateInfo("reset"))
		x = self.root.shape[0] / 2 + 20
		self.reset_btn.place(x=x, y=rowY)

		self.update_btn = ttk.Button( self.tab, text="确认修改", style="basic.TButton",
		                         command=lambda: self.updateInfo("update"))
		x = self.root.shape[0] / 2 - 20 - 80
		self.update_btn.place(x=x, y=rowY)

	def chooseFolder(self, val):
		val.set(tkinter.filedialog.askdirectory())

	def proxyCheck(self):
		if self.proxy_cbVal.get() == 0:
			self.proxyIP.configure(state=DISABLED)
			self.proxyPort.configure(state=DISABLED)
			self.proxyUser.configure(state=DISABLED)
			self.proxyPassword.configure(state=DISABLED)
		else:
			self.proxyIP.configure(state=NORMAL)
			self.proxyPort.configure(state=NORMAL)
			self.proxyUser.configure(state=NORMAL)
			self.proxyPassword.configure(state=NORMAL)

	def updateInfo(self, type="update"):
		if type == 'reset':
			self.fill()
			self.info("设置信息重置成功，若需保存，请点击'确认修改'")
		else:
			data = {}
			for attr in dir(self):
				if isinstance(getattr(self, attr), StringVar) or isinstance(getattr(self, attr), IntVar):
					data[attr] = getattr(self, attr).get()
			with open(getMacAdr() + ".info", "w") as f:
				json.dump(json.dumps(data, indent=4), f)
			self.info("设置信息更新成功")
			self.root.connServer()

	def readInfo(self):  # 读入设置信息
		if isfile(getMacAdr() + ".info"):
			print("read")
			with open(getMacAdr() + ".info") as f:
				data = json.loads(json.load(f))
			for attr in dir(self):
				if isinstance(getattr(self, attr), StringVar) or isinstance(getattr(self, attr), IntVar):
					getattr(self, attr).set(data[attr])

			self.clientNameInit = data["clientNameVal"]

			self.proxyCheck()

		else:
			self.info("初次使用，需要设定相关参数")


class DownloadTab(PTab):
	def __init__(self, root):
		self.name = list(root.widgets.names.keys())[1]
		PTab.__init__(self, root, self.name)

	def fill(self):
		helpX = self.lSpace + 60 * self.lSpace

		# 设置连接对象
		self.connClientVal = StringVar()

		rowY = self.top + self.hSpace
		rowX = self.lSpace


		self.connClient_l = ttk.Label(self.tab, text='在线终端:' + ' '*10, style="basic.TLabel")
		self.connClient_l.place(x=rowX, y=rowY)

		rowX += self.connClient_l.winfo_reqwidth() + 5
		self.connClient = ttk.Combobox(self.tab, style="basic.TCombobox",
		                               textvariable=self.connClientVal, width=18)
		self.connClient.place(x=rowX, y=rowY)
		#self.connClient["values"] = ("server", "dadmac", "officemac")

		rowX += self.connClient.winfo_reqwidth() + 5
		self.connClientPWD_l = ttk.Label(self.tab, text='连接密码:', style="basic.TLabel")
		self.connClientPWD_l.place(x=rowX, y=rowY)

		rowX += self.connClientPWD_l.winfo_reqwidth() + 5
		self.connClientPWDVal = StringVar()
		self.connClientPWD = ttk.Entry(self.tab, style='basic.TEntry',
		                           textvariable=self.connClientPWDVal, width=10)
		self.connClientPWD.place(x=rowX, y=rowY)

		rowX += self.connClientPWD.winfo_reqwidth() + 5
		self.connClientBtn = ttk.Button( self.tab, style="basic.TButton",
		                            text="连接",
		                            command=self.connectClient)
		self.connClientBtn.place(x=rowX, y=rowY)

		rowX += self.connClientBtn.winfo_reqwidth() + 5
		self.connClient_help = ttk.Label(self.tab, text='【连接远程终端】',style="basic.TLabel")
		self.connClient_help.place(x=rowX, y=rowY)

		# 设定当前目录#######
		rowY = self.top + self.hSpace * 6
		rowX = self.lSpace

		self.remoteDir_l = ttk.Label(self.tab, text='远程终端当前目录为:', style="basic.TLabel")
		self.remoteDir_l.place(x=rowX, y=rowY)

		rowX += self.remoteDir_l.winfo_reqwidth() + 5
		self.remoteDirVal = StringVar()
		self.remoteDir = ttk.Entry(self.tab, style='basic.TEntry',
		                       textvariable=self.remoteDirVal, width=60)
		self.remoteDir.place(x=rowX, y=rowY)

		rowX += self.remoteDir.winfo_reqwidth() + 5
		self.remoteDirEnterBtn = ttk.Button( self.tab,style="basic.TButton",
		                                text="进入目录",
		                                command=lambda:self.enterRemoteFolder(self.remoteDirVal.get()))
		self.remoteDirEnterBtn.place(x=rowX, y=rowY)

		rowX += self.remoteDirEnterBtn.winfo_reqwidth() + 5
		self.remoteDirReturnBtn = ttk.Button( self.tab, style="basic.TButton",
		                                 text="返回上层",
		                                 command=lambda: self.enterRemoteFolder(".."))
		self.remoteDirReturnBtn.place(x=rowX, y=rowY)

		# 显示文件列表###########
		rowY += self.hSpace * 6
		rowX = self.lSpace

		self.titleList = Listbox(self.tab,fg='black', bg='lightgray', font=("黑体", -10), relief=GROOVE,
		                         width=150, height=20, activestyle='dotbox')

		self.titleList.place(x=rowX, y=rowY)

		yscrollbar = Scrollbar(self.titleList, command=self.titleList .yview)
		yscrollbar.place(x=self.root.shape[0] - 50 , y=rowY)
		self.titleList.config(yscrollcommand=yscrollbar.set)

		self.titleList.bind("<Double-Button-1>", self.fileChoosed)




		# 显示标题###########
		col_num = 1

		self.titleDef = [("名称", 22, "name"), ("类型", 5, "ext"), ("大小", 5, "size"), ("修改时间", 8, "mtime"),
		("创建时间", 8, "ctime"), ("本地状态", 5, "state")]

		self.title, self.col_len_l = rowTitle(self.titleDef)

		self.titleList.insert(col_num, self.title)

		col_num += 1
		self.titleList.insert(col_num, lenUtf(self.title) * "-" + "\n")


		# 显示进度条
		rowX = self.lSpace
		rowY += self.hSpace * 30

		self.progressBarVal = DoubleVar()



		self.progressBar_l  = ttk.Label(self.tab, text='执行进度:' + ' '*10, style='basic.TLabel')
		self.progressBar_l.place(x=rowX, y=rowY)

		rowX += self.progressBar_l.winfo_reqwidth() + 5
		self.progressBar = ttk.Progressbar(self.tab, variable=self.progressBarVal, length='400', mode='determinate')
		self.progressBar.place(x=rowX, y=rowY)
		self.root.progressBar = self.progressBar


		self.progressBarVal.set(0)

		clientList = self.root.myCmd.do_getCl()

		self.connClient["values"] = tuple(clientList.keys())
		self.connClient.current(1)






	def showFilelist(self, fileList):
		col_num = 1
		nowPath = ".."
		self.fileList = []
		self.titleList.delete(3, END)
		for info in fileList:
			filename = info["name"]
			if filename.startswith("."): continue
			col_num += 1
			col_data = rowShow(self.titleDef, self.col_len_l, info ,
							   self.root.myClient.clientInfo["downloadFolderVal"])
			self.titleList.insert(col_num, col_data)
			self.fileList.append(info)

	def fileChoosed(self,event):
		w = event.widget
		line = w.curselection()
		if line[0]<2:
			self.info("选择错误")
			return
		info = self.fileList[line[0]-2]
		print(w.bbox(line))

		if info["isdir"]: 		# 处理目录
			self.remoteDirVal.set(info["path"])
			self.enterRemoteFolder(info["path"])
		else:	 # 处理文件下载
			yesno = messagebox.askyesno('提示', '要下载文件{}吗'.format(info["name"]))
			if yesno:
				self.root.myCmd.do_fetch(self.root.myClient, self.connClientVal.get(), info["dirName"], info["name"])






	#@self.showEx()
	def connectClient(self):

		clientName = self.connClientVal.get()
		client = self.root.myCmd.do_getClient(clientName, self.connClientPWDVal.get())

		self.showFilelist(client["fileList"])
		self.remoteDirVal.set(client["downloadFolderVal"])

	def enterRemoteFolder(self, dirName):
		sep = os.sep
		if self.remoteDirVal.get().find("\\") > 0: sep = "\\"
		if dirName == ".." :
			#dirName = self.remoteDirVal.get() + ".." + os.sep

			if self.remoteDirVal.get().count(sep) <2:
				self.info("当前已是根目录")
				return
			dirName = upFolderPath(self.remoteDirVal.get(), sep)
			self.remoteDirVal.set(dirName)
		elif not dirName.endswith(sep):
			dirName += sep

		self.remoteDirVal.set(dirName)

		client = self.root.myCmd.do_cd(dirName, self.root.myClient.clientName,self.connClientVal.get(),
		                               self.connClientPWDVal.get())
		self.showFilelist(client["fileList"])


class SyncTab(PTab):
	def __init__(self, root):
		self.name = list(root.widgets.names.keys())[2]
		PTab.__init__(self, root, self.name)

	def fill(self):
		self.clientNameVal = StringVar()
		hostname = socket.getfqdn(socket.gethostname())
		hostname = hostname.replace(".", "_")
		hostname = hostname.replace("-", "_")

		self.clientNameVal.set(hostname[:10])
		self.downloadFolderVal = StringVar()
		self.downloadFolderVal.set(sys.path[0] + os.sep + self.clientNameVal.get())
		self.syncFolderVal = StringVar()
		self.syncFolderVal.set(sys.path[0] + os.sep + "sync_" + self.clientNameVal.get())

		helpX = self.lSpace + 58 * self.lSpace
		# 设定终端名称
		rowY = self.top + self.hSpace
		self.clientName_l = ttk.Label(self.tab, text='同步名称:', style="basic.TLabel")
		self.clientName_l.place(x=self.lSpace, y=rowY)

		self.clientName = ttk.Entry(self.tab, style='basic.TEntry',
		                        textvariable=self.clientNameVal)
		self.clientName.place(x=self.lSpace + 10 * self.lSpace, y=rowY)

		self.clientName_help = ttk.Label(self.tab, text='【作为远程访问的标识】', style="basic.TLabel")
		self.clientName_help.place(x=helpX, y=rowY)


r = Root((800, 600))
# for name in r.widgets.names:
# 	PButton(r, name)

InfoTab(r)
SetupTab(r)
DownloadTab(r)
SyncTab(r)

# x = Tk()
#
#
# w = ttk.Notebook(x, width=700,height=450)
# r.wnd = w
# w.place(x=0,y=0)
# s2 = Frame(w)
# s3 = Frame(w)
# w.add(s2, text="设置")
# w.add(s3, text="下载")
# w.add(s1,text="同步")
#a=r.notebook.tabs()[0]
#r.notebook.select(a)
print()
#r.widgets.tabs[0].show()

#r.widgets.buttons[0].choosed()

# tab = PTab(r,"传输")
# tab = PTab(r,"同步")
# print(objInfo(btn1.button))
# print(btn1.button.place_info()["x"])
# print(r.wnd.winfo_screenwidth())
r.wnd.mainloop()
# x.mainloop()
# print(help(Button))
