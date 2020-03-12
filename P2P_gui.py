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
from tkinter import ttk
from myUtils import *
import p2pCmd
import socket
import json
import traceback


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

		# self.wnd.geometry(str(shape[0]) + "x" + str(shape[1]) + "+100+30")
		self.wnd.resizable(width=False, height=False)
		self.widgets = Widgets(self)
		self.buttonShape = (100, 30)
		# self.buttonPad = ()
		self.tabShape = (self.shape[0], self.shape[1] - self.buttonShape[1])
		self.myClient, self.myCmd, self.PTab = None, None, None



	def connServer(self):
		setupTab = self.widgets.tabs[2]
		downloadTab = self.widgets.tabs[0]
		clientName = setupTab.clientNameVal.get()
		if not clientName or clientName == "":
			self.PTab.info("终端名称为空，无法连接远程设备")
			return 0
		else:
			try:
				self.myClient, self.myCmd = p2pCmd.gui_main(setupTab)
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
			downloadTab.connClient.current(0)
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
		self.tab = Frame(self.root.wnd, width=root.tabShape[0], height=root.tabShape[1] - 30, bd=2, relief=GROOVE,
		                 bg="lightgray")
		self.root.PTab = self
		self.root.widgets.tabs.append(self)

		self.lSpace = 10  # 距左边界的距离
		self.top = 0  # 顶部起始位置

		self.hSpace = 10  # 纵向间隔



	def show(self):
		for pTab in self.root.widgets.tabs:
			pTab.tab.place_forget()


		self.tab.place(relx=0, rely=self.root.buttonShape[1] / self.root.shape[1])
		# self.top = int(self.tab.place_info()["y"])

		self.fill()
		self.readInfo()

	def info(self, msg):
		self.root.infoList.insert(1.0, nowStr() + " " + msg + "...\n")

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
		rowY = self.root.shape[1] - 30
		rowX = 0

		self.infoVar = StringVar()
		self.info_l = Label(self.root.wnd, text='状态信息:', fg='black', bg='lightgray', font=("黑体", 12),
		                    width=100, height=30, relief=GROOVE, bitmap="info", compound=LEFT, anchor=W, padx=10)
		self.info_l.place(x=rowX, y=rowY)
		# self.info_l.grid(row=3,column=0,sticky=W)
		rowX += int(self.info_l.cget("width"))

		self.infoList = tkinter.scrolledtext.ScrolledText(self.root.wnd,
		                                                  fg='black', bg='lightgray', font=("黑体", 11), relief=GROOVE,
		                                                  width=108)

		self.infoList.place(x=rowX, y=rowY - 2)
		# self.infoList.grid(row=3,column=1,columnspan=3,sticky=W+E)
		self.root.infoList = self.infoList

		self.root.infoList.insert(1.0, nowStr() + " 欢迎使用Alex P2P 文件传送器\n")





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

		self.clientNameVal.set(hostname[:10])
		helpX = self.lSpace + 58 * self.lSpace

		rowY = self.top + self.hSpace

		self.clientName_l = Label(self.tab, text='终端名称:', fg='black', bg='lightgray', font=("黑体", 12))
		self.clientName_l.place(x=self.lSpace, y=rowY)

		self.clientName = Entry(self.tab, fg='black', bg='white', font=("黑体", 11), relief=GROOVE, bd=2,
		                        textvariable=self.clientNameVal)
		self.clientName.place(x=self.lSpace + 10 * self.lSpace, y=rowY)

		self.clientName_help = Label(self.tab, text='【作为远程访问的标识】', fg='black', bg='lightgray', font=("黑体", 10))
		self.clientName_help.place(x=helpX, y=rowY)

		# 设定下载文件夹
		self.downloadFolderVal = StringVar()
		self.downloadFolderVal.set(sys.path[0] + os.sep + self.clientNameVal.get())

		rowY = rowY + self.hSpace * 3
		self.downloadFolder_l = Label(self.tab, text='下载文件夹:', fg='black', bg='lightgray', font=("黑体", 12))
		self.downloadFolder_l.place(x=self.lSpace, y=rowY)

		self.downloadFolder = Entry(self.tab, fg='black', bg='white', font=("黑体", 11), relief=GROOVE, bd=2,
		                            textvariable=self.downloadFolderVal, width=50)
		self.downloadFolder.place(x=self.lSpace + 10 * self.lSpace, y=rowY)

		self.downloadFolder_btn = Button(self.tab, text="选择...", font=("黑体", 9),
		                                 command=lambda: self.chooseFolder(self.downloadFolderVal), relief=GROOVE)
		x = int(self.downloadFolder.place_info()["x"]) + int(self.downloadFolder.cget("width")) * 8 + 5
		self.downloadFolder_btn.place(x=x, y=rowY)

		self.downloadFolder_help = Label(self.tab, text='【设定下载文件所存放的位置】', fg='black', bg='lightgray', font=("黑体", 10))
		self.downloadFolder_help.place(x=helpX, y=rowY)

		# 设定同步文件夹
		self.syncFolderVal = StringVar()
		self.syncFolderVal.set(sys.path[0] + os.sep + "sync_" + self.clientNameVal.get())

		rowY = rowY + self.hSpace * 3

		self.syncFolder_l = Label(self.tab, text='同步文件夹:', fg='black', bg='lightgray', font=("黑体", 12))
		self.syncFolder_l.place(x=self.lSpace, y=rowY)

		self.syncFolder = Entry(self.tab, fg='black', bg='white', font=("黑体", 11), relief=GROOVE, bd=2,
		                        textvariable=self.syncFolderVal, width=50)
		self.syncFolder.place(x=self.lSpace + 10 * self.lSpace, y=rowY)

		self.syncFolder_btn = Button(self.tab, text="选择...", font=("黑体", 9),
		                             command=lambda: self.chooseFolder(self.syncFolderVal), relief=GROOVE)
		x = int(self.syncFolder.place_info()["x"]) + int(self.syncFolder.cget("width")) * 8 + 5
		self.syncFolder_btn.place(x=x, y=rowY)

		self.syncFolder_help = Label(self.tab, text='【设定用于同步的文件夹】', fg='black', bg='lightgray', font=("黑体", 10))
		self.syncFolder_help.place(x=helpX, y=rowY)

		# 设定访问密码
		rowY = rowY + self.hSpace * 3
		self.passwordVal = IntVar()
		self.passwordVal.set("20130628")

		self.password_l = Label(self.tab, text='访问密码:', fg='black', bg='lightgray', font=("黑体", 12))
		self.password_l.place(x=self.lSpace, y=rowY)

		self.password = Entry(self.tab, fg='black', bg='white', font=("黑体", 11), relief=GROOVE, bd=2,
		                      textvariable=self.passwordVal, width=20, show="*")
		self.password.place(x=self.lSpace + 10 * self.lSpace, y=rowY)

		self.password_help = Label(self.tab, text='【远程访问本机的密码】', fg='black', bg='lightgray', font=("黑体", 10))
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

		self.proxyIP_l = Label(self.tab, text='IP:', fg='black', bg='lightgray', font=("黑体", 12))
		self.proxyIP_l.place(x=self.lSpace, y=rowY)

		self.proxyIP = Entry(self.tab, fg='black', bg='white', font=("黑体", 11), relief=GROOVE, bd=2,
		                     textvariable=self.proxyIPVal, width=16)
		self.proxyIP.place(x=self.lSpace + 10 * self.lSpace, y=rowY)

		self.proxyIP_help = Label(self.tab, text='【格式：XX.XX.XX.XX】', fg='black', bg='lightgray', font=("黑体", 10))
		self.proxyIP_help.place(x=helpX, y=rowY)

		# 设定端口
		rowY = rowY + self.hSpace * 3
		self.proxyPortVal = StringVar()
		self.proxyPortVal.set("8002")

		self.proxyPort_l = Label(self.tab, text='端口:', fg='black', bg='lightgray', font=("黑体", 12))
		self.proxyPort_l.place(x=self.lSpace, y=rowY)

		self.proxyPort = Entry(self.tab, fg='black', bg='white', font=("黑体", 11), relief=GROOVE, bd=2,
		                       textvariable=self.proxyPortVal, width=6)
		self.proxyPort.place(x=self.lSpace + 10 * self.lSpace, y=rowY)

		self.proxyPort_help = Label(self.tab, text='【格式：XXXX】', fg='black', bg='lightgray', font=("黑体", 10))
		self.proxyPort_help.place(x=helpX, y=rowY)

		# 设定用户名
		rowY = rowY + self.hSpace * 3
		self.proxyUserVal = StringVar()
		self.proxyUserVal.set("weijiaohua-004")

		self.proxyUser_l = Label(self.tab, text='用户名:', fg='black', bg='lightgray', font=("黑体", 12))
		self.proxyUser_l.place(x=self.lSpace, y=rowY)

		self.proxyUser = Entry(self.tab, fg='black', bg='white', font=("黑体", 11), relief=GROOVE, bd=2,
		                       textvariable=self.proxyUserVal, width=20)
		self.proxyUser.place(x=self.lSpace + 10 * self.lSpace, y=rowY)

		self.proxyUser_help = Label(self.tab, text='【可以为空】', fg='black', bg='lightgray', font=("黑体", 10))
		self.proxyUser_help.place(x=helpX, y=rowY)

		# 设定用户密码
		rowY = rowY + self.hSpace * 3
		self.proxyPasswordVal = StringVar()
		self.proxyPasswordVal.set("Cpic2190#")

		self.proxyPassword_l = Label(self.tab, text='用户密码:', fg='black', bg='lightgray', font=("黑体", 12))
		self.proxyPassword_l.place(x=self.lSpace, y=rowY)

		self.proxyPassword = Entry(self.tab, fg='black', bg='white', font=("黑体", 11), relief=GROOVE, bd=2,
		                           textvariable=self.proxyPasswordVal, width=20, show="*")
		self.proxyPassword.place(x=self.lSpace + 10 * self.lSpace, y=rowY)

		self.proxyPassword_help = Label(self.tab, text='【可以为空】', fg='black', bg='lightgray', font=("黑体", 10))
		self.proxyPassword_help.place(x=helpX, y=rowY)

		self.proxyCheck()
		# 恢复默认&确认修改
		rowY = rowY + self.hSpace * 6
		self.reset_btn = Button(self.tab, text="恢复默认", font=("黑体", 12), bitmap="gray12", width=100, height=30,
		                        compound=LEFT, anchor=W,
		                        command=lambda: self.updateInfo("reset"), relief=GROOVE)
		x = self.root.shape[0] / 2 + 20
		self.reset_btn.place(x=x, y=rowY)

		self.update_btn = Button(self.tab, text="确认修改", font=("黑体", 12), bitmap="gray12", width=100, height=30,
		                         compound=LEFT, anchor=W,
		                         command=lambda: self.updateInfo("update"), relief=GROOVE)
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

		self.connClient_l = Label(self.tab, text='在线终端:', fg='black', bg='lightgray', font=("黑体", 12))
		self.connClient_l.place(x=rowX, y=rowY)

		rowX += 140
		self.connClient = ttk.Combobox(self.tab, font=("黑体", 12),
		                               textvariable=self.connClientVal, width=20)
		self.connClient.place(x=rowX, y=rowY)
		#self.connClient["values"] = ("server", "dadmac", "officemac")

		rowX += 160
		self.connClientPWD_l = Label(self.tab, text='连接密码:', fg='black', bg='lightgray', font=("黑体", 12))
		self.connClientPWD_l.place(x=rowX, y=rowY)

		rowX += 80
		self.connClientPWDVal = StringVar()
		self.connClientPWD = Entry(self.tab, fg='black', bg='white', font=("黑体", 11), relief=GROOVE, bd=2,
		                           textvariable=self.connClientPWDVal, width=10)
		self.connClientPWD.place(x=rowX, y=rowY)

		rowX += 90
		self.connClientBtn = Button(self.tab, fg='black', bg='lightgray', font=("黑体", 12), relief=GROOVE, bd=2,
		                            text="连接", bitmap='gray12', width=40, compound=LEFT, anchor=W, padx=5)
		self.connClientBtn.place(x=rowX, y=rowY)

		rowX += 120
		self.connClient_help = Label(self.tab, text='【连接远程终端】', fg='black', bg='lightgray', font=("黑体", 12))
		self.connClient_help.place(x=rowX, y=rowY)

		# 设定当前目录#######
		rowY = self.top + self.hSpace * 6
		rowX = self.lSpace

		self.remoteDir_l = Label(self.tab, text='远程终端的当前目录为:', fg='black', bg='lightgray', font=("黑体", 12))
		self.remoteDir_l.place(x=rowX, y=rowY)

		rowX += 140
		self.remoteDirVal = StringVar()
		self.remoteDir = Entry(self.tab, fg='black', bg='white', font=("黑体", 11), relief=GROOVE, bd=1,
		                       textvariable=self.remoteDirVal, width=70)
		self.remoteDir.place(x=rowX, y=rowY)

		rowX += 450
		self.remoteDirEnterBtn = Button(self.tab, fg='black', bg='lightgray', font=("黑体", 12), relief=GROOVE, bd=2,
		                                text="进入目录", bitmap='gray12', width=40, compound=LEFT, anchor=W, padx=5)
		self.remoteDirEnterBtn.place(x=rowX, y=rowY)

		rowX += 100
		self.remoteDirReturnBtn = Button(self.tab, fg='black', bg='lightgray', font=("黑体", 12), relief=GROOVE, bd=2,
		                                 text="返回上层", bitmap='gray12', width=40, compound=LEFT, anchor=W, padx=5)
		self.remoteDirReturnBtn.place(x=rowX, y=rowY)

		# 显示文件列表###########
		rowY += self.hSpace * 6
		rowX = self.lSpace

		self.titleList = Listbox(self.tab,fg='black', bg='lightgray', font=("黑体", 11), relief=GROOVE,
		                         width=128, height=20)

		self.titleList.place(x=rowX, y=rowY)

		yscrollbar = Scrollbar(self.titleList, command=self.titleList .yview)
		yscrollbar.place(x=self.root.shape[0] - 50 , y=rowY)
		self.titleList.config(yscrollcommand=yscrollbar.set)

		self.titleList.bind("<Double-Button-1>", self.fileChoosed)




		# 显示标题###########
		col_num = 1

		self.titleDef = [("名称", 18, "name"), ("类型", 5, "ext"), ("大小", 5, "size"), ("修改时间", 8, "mtime"),
		("创建时间", 8, "ctime"), ("本地状态", 5, "state")]

		self.title, self.col_len_l = rowTitle(self.titleDef)

		self.titleList.insert(col_num, self.title)

		col_num += 1
		self.titleList.insert(col_num, lenUtf(self.title) * "-" + "\n")

		self.showFilelist(os.listdir("../AlexP2P"))


		#connClient("server")



	def showFilelist(self, filelist):
		col_num = 3
		nowPath = ".."

		for filename in filelist:
			if filename.startswith("."): continue
			col_num += 1
			col_data = rowShow(self.titleDef, self.col_len_l, fileInfo(filename, nowPath))
			self.titleList.insert(col_num, col_data)

	def fileChoosed(self,event):
		w = event.widget
		#print(dir(w))
		print(w.get(w.curselection()))

	def connClient(self, clientName):
		filelist = self.root.myCmd.do_getClient(clientName)
		self.showFilelist(filelist)




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
		self.clientName_l = Label(self.tab, text='同步名称:', fg='black', bg='lightgray', font=("黑体", 12))
		self.clientName_l.place(x=self.lSpace, y=rowY)

		self.clientName = Entry(self.tab, fg='black', bg='white', font=("黑体", 11), relief=GROOVE, bd=2,
		                        textvariable=self.clientNameVal)
		self.clientName.place(x=self.lSpace + 10 * self.lSpace, y=rowY)

		self.clientName_help = Label(self.tab, text='【作为远程访问的标识】', fg='black', bg='lightgray', font=("黑体", 10))
		self.clientName_help.place(x=helpX, y=rowY)


r = Root((800, 600))
for name in r.widgets.names:
	PButton(r, name)

InfoTab(r)
DownloadTab(r)
SyncTab(r)
SetupTab(r)

r.widgets.buttons[0].choosed()

# tab = PTab(r,"传输")
# tab = PTab(r,"同步")
# print(objInfo(btn1.button))
# print(btn1.button.place_info()["x"])
# print(r.wnd.winfo_screenwidth())
r.wnd.mainloop()
# print(help(Button))