from os.path import isfile

from tkinter import *
import tkinter.filedialog
import tkinter.scrolledtext
import tkinter.messagebox as messagebox
from tkinter import ttk

import p2pCmd
import socket
import json
import webbrowser
from p2pClient import VERSION
from myUtils import *
from p2pClient import MyClient


class Root:
    def __init__(self, shape):  # shape为长*宽元组
        self.logger = logInit("alexP2PClient.log")
        self.wnd = Tk()
        self.shape = shape
        self.wnd.title("Alex P2P 文件传送器")
        screenwidth = self.wnd.winfo_screenwidth()
        screenheight = self.wnd.winfo_screenheight()
        alignstr = '%dx%d+%d+%d' % (
            shape[0], shape[1], (screenwidth - shape[0]) / 2, (screenheight - shape[1]) / 2)  # 屏幕居中
        self.wnd.geometry(alignstr)
        self.wnd.resizable(width=False, height=False)

        self.tabIndexes = {"帮助": 3, "设置": 2, "传输": 1, "同步": 0}

        self.notebook = ttk.Notebook(self.wnd, width=self.shape[0], height=self.shape[1], style="basic.TNotebook", )
        self.notebook.pack()
        self.notebook.bind("<<NotebookTabChanged>>", self.tabChoosed)

        self.widgets = Widgets(self)
        self.buttonShape = (100, 30)
        # self.buttonPad = ()
        self.tabShape = (self.shape[0], self.shape[1])  # - self.buttonShape[1])
        self.myClient, self.myCmd, self.PTab, self.clientName = None, None, None, None
        self.progressBar, self.syncProgressBar = None, None
        self.syncFolderVal, self.progressBarVal, self.syncProgressBarVal = None, None, None
        self.syncProgressInfo_l, self.progressInfo_l = None, None
        self.upload_files, self.download_files, self.same_files = None, None, None
        self.syncListSelected = None
        self.connected = False
        self.isCheckLogin = False

        self.style = ttk.Style()
        self.initStyles()

    def tabChoosed(self, *args):
        tabId = self.notebook.select()
        index = self.notebook.index(tabId)
        if not self.connected and index != self.tabIndexes["设置"]:
            messagebox.showerror('连接错误', '未连接服务器，请检查网络、代理服务器，修改后连接')
            self.notebook.select(self.tabIndexes["设置"])
            self.widgets.tabs[self.tabIndexes["设置"]].show()

        else:
            self.widgets.tabs[index].show()
        # if index == 0:
        #     self.myCmd.do_versionCheck()
        #     self.widgets.tabs[index].viewSyncFiles("upload")

    def initStyles(self):
        self.font_label = 12
        self.font_text = 12
        font_label = ("黑体", 0 - self.font_label)
        font_text = ("黑体", 0 - self.font_text)

        self.style.configure("basic.TLabel", foreground="black", background="lightgray", font=font_label)
        self.style.configure("basic.TButton", foreground="black", background="lightgray", relief=GROOVE,
                             font=font_label)

        self.style.configure("basic.TEntry", foreground="black", background="lightgray", relief=GROOVE, font=font_text)
        self.style.configure("basic.TCombobox", foreground="black", background="lightgray", relief=GROOVE,
                             font=font_text)

    def login(self):  # 登录处理
        infoTab = InfoTab(self)
        syncTab = SyncTab(self)
        downloadTab = DownloadTab(self)
        setupTab = SetupTab(self)
        helpTab = HelpTab(self)
        infoPath = path.join(os.getcwd(), getMacAdr() + ".info")
        if not path.exists(infoPath):  # 初次使用
            self.notebook.select(self.tabIndexes["设置"])
            setupTab.fill()
        else:
            self.notebook.select(self.tabIndexes["设置"])
            setupTab.show()  # fill & readfile
            if self.connectServer() == 1:
                self.connected = True
                self.notebook.select(self.tabIndexes["同步"])
                syncTab.show()
                self.myCmd.do_versionCheck()
                syncTab.viewSyncFiles("upload")
            else:
                self.connected = False

                self.notebook.select(self.tabIndexes["设置"])
                # print(self.notebook.index(self.notebook.select()))

    def connectServer(self):
        setupTab = self.widgets.tabs[2]
        clientName = setupTab.clientNameVal.get()
        self.clientName = clientName
        if not clientName or clientName == "":
            self.PTab.info("终端名称为空，无法连接远程设备")
            return 0
        else:
            try:
                if not self.myClient or not self.myCmd or clientName != setupTab.clientNameInit or not self.isCheckLogin:  # 首次登录或更换用户或前次登录失败
                    self.myClient, self.myCmd = p2pCmd.gui_main(setupTab, self)
                    self.myClient.root = self
                    self.myCmd.root = self
                    # 保存配置文件
                    rs = self.myCmd.do_checkLogin(setupTab.passwordVal.get())
                    if rs == -1:  # 首次在服务器上注册
                        self.myCmd.do_saveSetupInServer()
                        self.myCmd.do_saveIntro()  # 在本地保存帮助信息
                        self.PTab.info("已完成首次注册!")
                    elif rs == 1:
                        self.PTab.info("用户名密码验证通过!")
                    elif rs == 0:
                        # messagebox.showerror('连接错误', '无法连接服务器，请检查用户名：{} 及密码'.format(self.clientName))
                        self.PTab.info("连接失败，用户名密码错误!")
                        self.isCheckLogin = False  # 记录连接失败过
                        return 0
                    self.isCheckLogin = True


                else:  # 更新信息
                    self.myClient = MyClient(setupTab, "update")
                    self.myClient.updateClientInfo()
                    self.myCmd.do_saveSetupInServer()

            except Fault as f:
                if f.faultCode == 2:
                    self.PTab.info("重新连接 " + f.faultString)
                    return 1
                else:
                    raise f
            except Exception as e:
                self.PTab.info("连接远程设备出错，请检查配置信息 出错信息:" + str(e))
                # messagebox.showerror('连接错误', '无法连接服务器，请检查网络、代理服务器')
                traceback.print_exc()
                return 0
            self.PTab.info("连接成功，可以传输或同步文件")
            self.checkVer()
            self.connected = True
            return 1

    def checkVer(self):
        rs = self.myCmd.do_checkVer()
        self.logger.info("核对版本，结果:{}".format(rs))
        if rs == -1:
            yesno = messagebox.askyesno('提示', '当前版本较旧是否下载新版本？')
            if yesno:
                webbrowser.open("http://106.13.113.252//p2p.htm")
                return
        return rs


class Widgets():  # Widgets= PButton+PTab
    def __init__(self, root):
        self.names = {"设置": 0, "传输": 1, "同步": 2, "帮助": 3}
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
        self.tab = Frame(self.root.notebook, width=root.shape[0], height=root.shape[1] - 30, bd=2, relief=FLAT,
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

        # self.tab.place(relx=0, rely=0) # self.root.buttonShape[1] / self.root.shape[1])
        # self.top = int(self.tab.place_info()["y"])

        self.fill()
        self.readInfo()

    def info(self, msg):
        self.root.logger.info(msg)
        self.root.infoList.insert(1.0, nowStr() + " " + msg + "...\n")

    def showEx(self):  # 用于在GUI中显示异常信息的装饰器
        def decorator(fn):
            @wraps(fn)
            def showFault(*args, **kwargs):
                try:
                    return fn(*args, **kwargs)
                except Fault as f:
                    self.info("远程调用异常: [" + fn.__name__ + "]:" + str(f))
                # traceback.print_exc()
                except Exception as e:
                    self.info("本地调用异常：[" + fn.__name__ + "]:" + str(e))

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

    def showFilelist(self, fileList, localDir=None):  # localDir用于远程文件与本地目录中的文件做状态比较
        col_num = 1
        nowPath = ".."
        self.fileList = []
        self.titleList.delete(2, END)
        for info in fileList:
            filename = info["name"]
            if filename.startswith("."): continue
            col_num += 1
            col_data = rowShow(self.titleDef, self.col_len_l, info,
                               localDir)
            self.titleList.insert(col_num, col_data)
            self.fileList.append(info)


class InfoTab():
    def __init__(self, root):
        self.name = "状态信息"
        self.root = root
        self.fill()

    def fill(self):
        rowX = 0
        rowY = self.root.shape[1] - 80
        self.infoFrame = ttk.LabelFrame(self.root.wnd, width=self.root.shape[0], text='状态信息', height=40)

        self.infoList = tkinter.scrolledtext.ScrolledText(self.infoFrame,
                                                          fg='black', bg='lightgray', font=("黑体", -10), relief=GROOVE,
                                                          width=154, height=3)

        self.root.infoList = self.infoList

        self.root.infoList.insert(1.0, nowStr() + " 欢迎使用Alex P2P 文件传送器\n")

        self.infoFrame.place(x=0, y=rowY)
        self.infoList.pack()


class HelpTab(PTab):
    def __init__(self, root):
        self.name = "帮助"
        PTab.__init__(self, root, self.name)

    def fill(self):
        self.textVal = StringVar()
        self.text = Text(self.tab, width=100, height=30, bg='lightgray', fg="black", font=("黑体", -12))

        self.text.place(x=5, y=5)
        # self.text.insert(INSERT, "AlexP2P 文件同步传输\n For Alex & Queena \n\n")

        intros = self.root.myCmd.do_getIntro()
        for i in intros:
            self.text.insert(INSERT, i)

        self.text.insert(INSERT, "\n" * 2)
        self.text.insert(INSERT, "【当前用户】 {} \n".format(self.root.clientName))
        self.text.insert(INSERT, "【当前版本】 {} \n".format(VERSION))
        self.text.insert(INSERT, "【更新时间】 {} \n".format("2020-03-23"))
        self.text.insert(INSERT, "【设计开发】 {} \n".format("骄华"))

        self.text["state"] = DISABLED


class SetupTab(PTab):
    def __init__(self, root):
        self.name = list(root.widgets.names.keys())[0]
        PTab.__init__(self, root, self.name)

    def fill(self):

        # 设定终端名称
        self.clientNameVal = StringVar()
        hostname = socket.getfqdn(socket.gethostname())
        hostname = re.sub('[ .-]', "_", hostname).strip()
        if not self.clientNameVal.get():
            self.clientNameVal.set(hostname[:10])
            self.clientNameInit = hostname[:10]
        helpX = self.lSpace + 58 * self.lSpace

        rowY = self.top + self.hSpace
        rowX = self.lSpace

        self.clientName_l = ttk.Label(self.tab, text='用户名称:  ', style="basic.TLabel")
        self.clientName_l.place(x=rowX, y=rowY)

        rowX += self.clientName_l.winfo_reqwidth() + 5
        self.clientName = ttk.Entry(self.tab, style='basic.TEntry',
                                    textvariable=self.clientNameVal)
        self.clientName.place(x=rowX, y=rowY)
        self.clientName.bind("<Any-KeyRelease>", self.changeDirName)

        rowX += self.clientName.winfo_reqwidth() + 5
        self.clientName_help = ttk.Label(self.tab, text='【作为远程访问和同步标识】', style="basic.TLabel")
        self.clientName_help.place(x=rowX, y=rowY)

        # 设定访问密码
        rowY += self.clientName_help.winfo_reqheight() + 10
        rowX = self.lSpace

        self.passwordVal = StringVar()
        if not self.passwordVal.get(): self.passwordVal.set("0628")

        self.password_l = ttk.Label(self.tab, text='访问密码:  ', style="basic.TLabel")
        self.password_l.place(x=rowX, y=rowY)

        rowX += self.password_l.winfo_reqwidth() + 5
        self.password = ttk.Entry(self.tab, style='basic.TEntry',
                                  textvariable=self.passwordVal, width=20, show="*")
        self.password.place(x=rowX, y=rowY)

        rowX += self.password.winfo_reqwidth() + 5
        self.password_help = ttk.Label(self.tab, text='【用于同步和远程访问的密码,默认0628】', style="basic.TLabel")
        self.password_help.place(x=rowX, y=rowY)

        # 设定下载文件夹
        rowY += self.password_l.winfo_reqheight() + 10
        rowX = self.lSpace
        self.downloadFolderVal = StringVar()
        if not self.downloadFolderVal.get():
            pathStr = path.join(os.getcwd(), self.clientNameVal.get(), "download")
            pathStr = re.sub(r"P2P_gui.app/Contents/Resources/", "", pathStr)  # 处理苹果APP目录
            self.downloadFolderVal.set(pathStr)

        self.downloadFolder_l = ttk.Label(self.tab, text='下载文件夹:', style="basic.TLabel")
        self.downloadFolder_l.place(x=rowX, y=rowY)

        rowX += self.downloadFolder_l.winfo_reqwidth() + 5
        self.downloadFolder = ttk.Entry(self.tab, style='basic.TEntry',
                                        textvariable=self.downloadFolderVal, width=50)
        self.downloadFolder.place(x=rowX, y=rowY)

        rowX += self.downloadFolder.winfo_reqwidth() + 3
        self.downloadFolder_btn = ttk.Button(self.tab, text="选择...", style="basic.TButton",
                                             command=lambda: self.chooseFolder(self.downloadFolderVal))
        # x = int(self.downloadFolder.place_info()["x"]) + self.downloadFolder.winfo_reqwidth() + 5
        self.downloadFolder_btn.place(x=rowX, y=rowY)

        rowX += self.downloadFolder_btn.winfo_reqwidth() + 5
        self.downloadFolder_help = ttk.Label(self.tab, text='【设定下载文件所存放的位置】', style="basic.TLabel")
        self.downloadFolder_help.place(x=rowX, y=rowY)

        # 设定同步文件夹
        self.syncFolderVal = StringVar()
        self.root.syncFolderVal = self.syncFolderVal
        if not self.syncFolderVal.get():
            pathStr = path.join(os.getcwd(), self.clientNameVal.get(), "sync")
            pathStr = re.sub(r"P2P_gui.app/Contents/Resources/", "", pathStr)  # 处理苹果APP目录
            self.syncFolderVal.set(pathStr)

        rowY += self.downloadFolder_help.winfo_reqheight() + 10
        rowX = self.lSpace
        self.syncFolder_l = ttk.Label(self.tab, text='同步文件夹:', style="basic.TLabel")
        self.syncFolder_l.place(x=rowX, y=rowY)

        rowX += self.syncFolder_l.winfo_reqwidth() + 5

        self.syncFolder = ttk.Entry(self.tab, style='basic.TEntry',
                                    textvariable=self.syncFolderVal, width=50)
        self.syncFolder.place(x=rowX, y=rowY)

        rowX += self.syncFolder.winfo_reqwidth() + 5
        self.syncFolder_btn = ttk.Button(self.tab, text="选择...", style="basic.TButton",
                                         command=lambda: self.chooseFolder(self.syncFolderVal))

        self.syncFolder_btn.place(x=rowX, y=rowY)

        rowX += self.syncFolder_btn.winfo_reqwidth() + 5
        self.syncFolder_help = ttk.Label(self.tab, text='【设定用于同步的文件夹】', style="basic.TLabel")
        self.syncFolder_help.place(x=rowX, y=rowY)

        # 设定代理服务器
        rowY += self.syncFolder_help.winfo_reqheight() + 15
        rowX = self.lSpace

        self.proxy_cbVal = IntVar()
        self.proxy_cbVal.set(0)

        self.proxy_cb = Checkbutton(self.tab, text='是否使用代理服务器', onvalue=1, offvalue=0, variable=self.proxy_cbVal,
                                    fg='black', bg='lightgray', font=("黑体", -12), command=self.proxyCheck)
        self.proxy_cb.place(x=rowX, y=rowY)

        # 设定代理服务器地址
        rowY += self.proxy_cb.winfo_reqheight() + 10
        rowX = self.lSpace

        self.proxyIPVal = StringVar()
        self.proxyIPVal.set("10.191.113.100")

        self.proxyIP_l = ttk.Label(self.tab, text='IP地址:    ', style="basic.TLabel")
        self.proxyIP_l.place(x=rowX, y=rowY)

        rowX += self.proxyIP_l.winfo_reqwidth() + 5
        self.proxyIP = ttk.Entry(self.tab, style='basic.TEntry',
                                 textvariable=self.proxyIPVal, width=16)
        self.proxyIP.place(x=rowX, y=rowY)

        rowX += self.proxyIP.winfo_reqwidth() + 5
        self.proxyIP_help = ttk.Label(self.tab, text='代理服务器IP地址【格式：XX.XX.XX.XX】', style="basic.TLabel")
        self.proxyIP_help.place(x=rowX, y=rowY)

        # 设定端口
        rowY += self.proxyIP_help.winfo_reqheight() + 10
        rowX = self.lSpace
        self.proxyPortVal = StringVar()
        self.proxyPortVal.set("8002")

        self.proxyPort_l = ttk.Label(self.tab, text='端口:      ', style="basic.TLabel")
        self.proxyPort_l.place(x=rowX, y=rowY)

        rowX += self.proxyPort_l.winfo_reqwidth() + 5
        self.proxyPort = ttk.Entry(self.tab, style='basic.TEntry',
                                   textvariable=self.proxyPortVal, width=6)
        self.proxyPort.place(x=rowX, y=rowY)

        rowX += self.proxyPort.winfo_reqwidth() + 5
        self.proxyPort_help = ttk.Label(self.tab, text='代理服务器端口【格式：XXXX】', style="basic.TLabel")
        self.proxyPort_help.place(x=rowX, y=rowY)

        # 设定用户名
        rowY += self.proxyPort_help.winfo_reqheight() + 10
        rowX = self.lSpace
        self.proxyUserVal = StringVar()
        self.proxyUserVal.set("")

        self.proxyUser_l = ttk.Label(self.tab, text='用户名:    ', style="basic.TLabel")
        self.proxyUser_l.place(x=rowX, y=rowY)

        rowX += self.proxyUser_l.winfo_reqwidth() + 5
        self.proxyUser = ttk.Entry(self.tab, style='basic.TEntry',
                                   textvariable=self.proxyUserVal, width=20)
        self.proxyUser.place(x=rowX, y=rowY)

        rowX += self.proxyUser.winfo_reqwidth() + 5
        self.proxyUser_help = ttk.Label(self.tab, text='【代理服务器用户名，可以为空】', style="basic.TLabel")
        self.proxyUser_help.place(x=rowX, y=rowY)

        # 设定用户密码
        rowY += self.proxyUser_help.winfo_reqheight() + 10
        rowX = self.lSpace
        self.proxyPasswordVal = StringVar()
        self.proxyPasswordVal.set("")

        self.proxyPassword_l = ttk.Label(self.tab, text='用户密码:  ', style="basic.TLabel")
        self.proxyPassword_l.place(x=rowX, y=rowY)

        rowX += self.proxyPassword_l.winfo_reqwidth() + 5
        self.proxyPassword = ttk.Entry(self.tab, style='basic.TEntry',
                                       textvariable=self.proxyPasswordVal, width=20, show="*")
        self.proxyPassword.place(x=rowX, y=rowY)

        rowX += self.proxyPassword.winfo_reqwidth() + 5
        self.proxyPassword_help = ttk.Label(self.tab, text='【代理服务器密码，可以为空】', style="basic.TLabel")
        self.proxyPassword_help.place(x=rowX, y=rowY)

        self.proxyCheck()
        # 恢复默认&确认修改
        rowY += self.proxyUser_help.winfo_reqheight() + 15
        rowX = self.lSpace
        self.reset_btn = ttk.Button(self.tab, text="恢复为默认", style="basic.TButton",
                                    command=lambda: self.updateInfo("reset"))
        x = self.root.shape[0] / 2 + 20
        self.reset_btn.place(x=x, y=rowY)

        self.update_btn = ttk.Button(self.tab, text="修改并连接", style="basic.TButton",
                                     command=lambda: self.updateInfo("update"))
        x = self.root.shape[0] / 2 - 20 - 80
        self.update_btn.place(x=x, y=rowY)

    def chooseFolder(self, val):
        dirStr = tkinter.filedialog.askdirectory()
        if os.sep == "\\" and dirStr.find("/") > -1:
            dirStr = dirStr.replace("/", "\\")
        val.set(dirStr)

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
            self.readInfo()
            rs = self.root.connectServer()
            if rs != 0:  # 0 为连接失败
                self.root.widgets.tabs[0].show()
            else:
                messagebox.showerror('连接错误', '无法连接服务器，请检查用户名：{} 及密码'.format(self.root.clientName))

    def readInfo(self):  # 读入设置信息
        if isfile(getMacAdr() + ".info"):
            with open(getMacAdr() + ".info") as f:
                data = json.loads(json.load(f))
            for attr in dir(self):
                if isinstance(getattr(self, attr), StringVar) or isinstance(getattr(self, attr), IntVar):
                    getattr(self, attr).set(data[attr])

            self.clientNameInit = data["clientNameVal"]

            self.proxyCheck()

        else:
            self.info("初次使用，需要设定相关参数")

    def changeDirName(self, event):

        pathStr = path.join(os.getcwd(), self.clientNameVal.get())
        pathStr = re.sub(r"P2P_gui.app/Contents/Resources/", "", pathStr)  # 处理苹果APP目录
        if os.sep == "\\" and pathStr.find("/") > -1:
            pathStr = pathStr.replace("/", "\\")

        self.downloadFolderVal.set(path.join(pathStr, "download"))
        self.syncFolderVal.set(path.join(pathStr, "sync"))


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

        self.connClient_l = ttk.Label(self.tab, text='在线终端:' + ' ' * 10, style="basic.TLabel")
        self.connClient_l.place(x=rowX, y=rowY)

        rowX += self.connClient_l.winfo_reqwidth() + 5
        self.connClient = ttk.Combobox(self.tab, style="basic.TCombobox",
                                       textvariable=self.connClientVal, width=18)
        self.connClient.place(x=rowX, y=rowY)
        # self.connClient["values"] = ("server", "dadmac", "officemac")

        rowX += self.connClient.winfo_reqwidth() + 5
        self.connClientPWD_l = ttk.Label(self.tab, text='连接密码:', style="basic.TLabel")
        self.connClientPWD_l.place(x=rowX, y=rowY)

        rowX += self.connClientPWD_l.winfo_reqwidth() + 5
        self.connClientPWDVal = StringVar()
        self.connClientPWD = ttk.Entry(self.tab, style='basic.TEntry',
                                       textvariable=self.connClientPWDVal, width=10, show="*")
        self.connClientPWD.place(x=rowX, y=rowY)

        rowX += self.connClientPWD.winfo_reqwidth() + 5
        self.connClientBtn = ttk.Button(self.tab, style="basic.TButton",
                                        text="连接",
                                        command=self.connectClient)
        self.connClientBtn.place(x=rowX, y=rowY)

        rowX += self.connClientBtn.winfo_reqwidth() + 5
        self.connClient_help = ttk.Label(self.tab, text='【连接远程终端】', style="basic.TLabel")
        self.connClient_help.place(x=rowX, y=rowY)

        # 设定当前目录#######
        rowY += self.connClientPWD.winfo_reqheight() + 10
        rowX = self.lSpace

        self.remoteDir_l = ttk.Label(self.tab, text='远程终端当前目录为:', style="basic.TLabel")
        self.remoteDir_l.place(x=rowX, y=rowY)

        rowX += self.remoteDir_l.winfo_reqwidth() + 5
        self.remoteDirVal = StringVar()
        self.remoteDir = ttk.Entry(self.tab, style='basic.TEntry',
                                   textvariable=self.remoteDirVal, width=50)
        self.remoteDir.place(x=rowX, y=rowY)

        rowX += self.remoteDir.winfo_reqwidth() + 5
        self.remoteDirEnterBtn = ttk.Button(self.tab, style="basic.TButton",
                                            text="进入目录",
                                            command=lambda: self.enterRemoteFolder(self.remoteDirVal.get()))
        self.remoteDirEnterBtn.place(x=rowX, y=rowY)

        rowX += self.remoteDirEnterBtn.winfo_reqwidth() + 5
        self.remoteDirReturnBtn = ttk.Button(self.tab, style="basic.TButton",
                                             text="返回上层",
                                             command=lambda: self.enterRemoteFolder(".."))
        self.remoteDirReturnBtn.place(x=rowX, y=rowY)

        # 设定本地目录#######
        rowY += self.remoteDirReturnBtn.winfo_reqheight() + 10
        rowX = self.lSpace

        self.localDir_l = ttk.Label(self.tab, text='本地存储目录为:    ', style="basic.TLabel")
        self.localDir_l.place(x=rowX, y=rowY)

        rowX += self.localDir_l.winfo_reqwidth() + 5
        self.localDirVal = StringVar()
        self.localDirVal.set(self.root.myClient.clientInfo["downloadFolderVal"])
        self.localDir = ttk.Entry(self.tab, style='basic.TEntry',
                                  textvariable=self.localDirVal, width=50)
        self.localDir.place(x=rowX, y=rowY)

        rowX += self.localDir.winfo_reqwidth() + 5
        self.localDirEnterBtn = ttk.Button(self.tab, style="basic.TButton",
                                           text="查看本地目录",
                                           command=lambda: self.enterLocalFolder(self.localDirVal.get()))
        self.localDirEnterBtn.place(x=rowX, y=rowY)

        rowX += self.localDirEnterBtn.winfo_reqwidth() + 5
        self.localDirReturnBtn = ttk.Button(self.tab, style="basic.TButton",
                                            text="返回远程目录",
                                            command=lambda: self.enterRemoteFolder(self.remoteDirVal.get()))
        self.localDirReturnBtn.place(x=rowX, y=rowY)
        # 显示文件列表###########

        rowX = self.lSpace
        rowY += self.remoteDirReturnBtn.winfo_reqheight() + 10

        listFrame = Frame(self.tab, width=700, height=300)
        listFrame.place(x=rowX, y=rowY)

        self.titleList = Listbox(listFrame, fg='black', bg='lightgray', font=("黑体", -10), relief=GROOVE,
                                 width=140, height=20, activestyle='dotbox')

        # self.titleList.place(x=rowX, y=rowY)
        self.titleList.grid(row=0, column=0)
        # 滚动条
        rowX += self.titleList.winfo_reqwidth() + 5
        yscrollbar = Scrollbar(listFrame, command=self.titleList.yview)
        yscrollbar.grid(row=0, column=1)

        # yscrollbar.place(x=rowX , y=rowY)

        self.titleList.config(yscrollcommand=yscrollbar.set)

        self.titleList.bind("<Double-Button-1>", self.fileChoosed)

        # 显示标题###########
        col_num = 1

        self.titleDef = [("名称", 16, "name"), ("类型", 5, "ext"), ("大小", 5, "size"), ("修改时间", 8, "mtime"),
                         ("创建时间", 8, "ctime"), ("本地状态", 5, "state")]

        self.title, self.col_len_l = rowTitle(self.titleDef)

        self.titleList.insert(col_num, self.title)

        col_num += 1
        self.titleList.insert(col_num, lenUtf(self.title) * "-" + "\n")

        # 显示进度条
        rowX = self.lSpace
        rowY += self.titleList.winfo_reqheight() + 10

        self.progressBarVal = DoubleVar()

        self.progressBar_l = ttk.Label(self.tab, text='执行进度:' + ' ' * 10, style='basic.TLabel')
        self.progressBar_l.place(x=rowX, y=rowY)

        rowX += self.progressBar_l.winfo_reqwidth() + 5
        self.progressBar = ttk.Progressbar(self.tab, variable=self.progressBarVal, length='400', mode='determinate')
        self.progressBar.place(x=rowX, y=rowY)
        self.root.progressBar = self.progressBar
        self.root.progressBarVal = self.progressBarVal
        self.progressBarVal.set(0)

        rowX = self.lSpace
        rowY += self.progressBar.winfo_reqheight() + 10
        self.progressInfo_l = ttk.Label(self.tab, text=' ' * 15, style='basic.TLabel', foreground='gray',
                                        font=("黑体", -10))
        self.progressInfo_l.place(x=rowX, y=rowY)
        self.root.progressInfo_l = self.progressInfo_l

    def show(self):
        self.fill()
        self.root.notebook.select(1)
        clientList = self.root.myCmd.do_getCl()
        if clientList:
            self.connClient["values"] = tuple(clientList.keys())
            self.connClient.current(1)

    def fileChoosed(self, event):
        w = event.widget
        line = w.curselection()
        if line[0] < 2:
            self.info("选择错误")
            return
        info = self.fileList[line[0] - 2]

        if info["isdir"]:  # 处理目录
            self.remoteDirVal.set(info["path"])
            self.enterRemoteFolder(info["path"])
        else:  # 处理文件下载
            # if info["state"] == "本地"
            yesno = messagebox.askyesno('提示', '要下载文件{}吗'.format(info["name"]))
            if yesno:
                self.root.myCmd.do_fetch(self.root.myClient, self.connClientVal.get(), info["dirName"], info["name"])

    # @self.showEx()
    def connectClient(self):
        try:
            clientName = self.connClientVal.get()
            client = self.root.myCmd.do_getClient(clientName, self.connClientPWDVal.get())
            if client:
                self.showFilelist(client["fileList"], self.root.myClient.clientInfo["downloadFolderVal"])
                self.remoteDirVal.set(client["downloadFolderVal"])
            else:
                messagebox.showerror('连接错误', '无法连接远程终端，密码错误')
        except Exception as e:
            self.info("连接远程设备出错，出错信息:" + str(e))

    def enterRemoteFolder(self, dirName):
        if not dirName or dirName == '':
            self.info("请先连接远程终端")
            messagebox.showerror('返回错误', '未连接远程终端，请先选择并连接')
            return
        sep = os.sep
        if self.remoteDirVal.get().find("\\") > 0: sep = "\\"
        if dirName == "..":
            # dirName = self.remoteDirVal.get() + ".." + os.sep

            if self.remoteDirVal.get().count(sep) < 2:
                self.info("当前已是根目录")
                return
            dirName = upFolderPath(self.remoteDirVal.get(), sep)
            self.remoteDirVal.set(dirName)
        elif not dirName.endswith(sep):
            dirName += sep

        self.remoteDirVal.set(dirName)

        client = self.root.myCmd.do_cd(dirName, self.root.myClient.clientName, self.connClientVal.get(),
                                       self.connClientPWDVal.get())
        if client:
            self.showFilelist(client["fileList"], self.root.myClient.clientInfo["downloadFolderVal"])
            self.root.progressInfo_l["text"] = "目录已切换成: {}".format(dirName)
            self.root.progressBarVal.set(100)
        else:
            self.root.progressInfo_l["text"] = "目录切换失败".format(dirName)
            self.root.progressBarVal.set(0)

    def enterLocalFolder(self, dirName):
        fileList = makeFileList(dirName)
        self.showFilelist(fileList)


class SyncTab(PTab):
    def __init__(self, root):
        self.name = list(root.widgets.names.keys())[2]
        PTab.__init__(self, root, self.name)

    def fill(self):

        rowY = self.top + self.hSpace
        rowX = self.lSpace
        self.syncFolder_l = ttk.Label(self.tab, text='本机同步文件夹：' + 2 * " ", style="basic.TLabel")
        self.syncFolder_l.place(x=rowX, y=rowY)

        rowX += self.syncFolder_l.winfo_reqwidth() + 10
        self.syncFolder = ttk.Entry(self.tab, style='basic.TEntry',
                                    textvariable=self.root.syncFolderVal, width=50, state=DISABLED)
        self.syncFolder.place(x=rowX, y=rowY)

        rowX += self.syncFolder.winfo_reqwidth() + 10
        self.syncFolderIntro_l = ttk.Label(self.tab, text='【说明】 请将需要同步的文件拷入此文件夹', style="basic.TLabel")
        self.syncFolderIntro_l.place(x=rowX, y=rowY)

        # 查看待上传文件按钮

        rowY += self.syncFolder_l.winfo_reqheight() + 20
        rowX = self.lSpace

        self.viewUploadBtn = ttk.Button(self.tab, style="basic.TButton",
                                        text="查看本机待上传文件",
                                        command=lambda: self.viewSyncFiles('upload'))
        self.viewUploadBtn.place(x=rowX, y=rowY)

        # 查看待下载文件按钮
        rowX += self.viewUploadBtn.winfo_reqwidth() + 10
        self.viewDownloadBtn = ttk.Button(self.tab, style="basic.TButton",
                                          text="查看远程待下载文件",
                                          command=lambda: self.viewSyncFiles('download'))
        self.viewDownloadBtn.place(x=rowX, y=rowY)

        # 查看待本机同步文件按钮
        rowX += self.viewDownloadBtn.winfo_reqwidth() + 10
        self.viewLocalBtn = ttk.Button(self.tab, style="basic.TButton",
                                       text="查看本机同步文件夹",
                                       command=lambda: self.viewSyncFiles('local'))
        self.viewLocalBtn.place(x=rowX, y=rowY)

        # 查看待本机同步文件按钮
        rowX += self.viewLocalBtn.winfo_reqwidth() + 10
        self.syncRenewBtn = ttk.Button(self.tab, style="basic.TButton",
                                       text="刷新同步信息",
                                       command=lambda: self.syncRenew())
        self.syncRenewBtn.place(x=rowX, y=rowY)

        # 说明
        rowY += self.syncRenewBtn.winfo_reqheight() + 10
        rowX = self.lSpace
        self.syncIntro_l = ttk.Label(self.tab, foreground='blue', text="【本机待上传文件】：以下文件修改时间较新，需要上传同步 ",
                                     style="basic.TLabel")
        self.syncIntro_l.place(x=rowX, y=rowY)

        # 文件列表
        rowY += self.syncIntro_l.winfo_reqheight() + 10
        rowX = self.lSpace

        listFrame = Frame(self.tab, width=700, height=300)
        listFrame.place(x=rowX, y=rowY)

        self.titleList = Listbox(listFrame, fg='black', bg='lightgray', font=("黑体", -10), relief=GROOVE,
                                 width=140, height=20, activestyle='dotbox')

        # self.titleList.place(x=rowX, y=rowY)
        self.titleList.grid(row=0, column=0)

        yscrollbar = Scrollbar(listFrame, command=self.titleList.yview)
        # yscrollbar.place(x=rowX + self.titleList.winfo_reqwidth() , y=rowY)
        yscrollbar.grid(row=0, column=1)
        self.titleList.config(yscrollcommand=yscrollbar.set)

        self.titleList.bind("<Double-Button-1>", self.fileChoosed)

        # 显示标题###########
        col_num = 1

        self.titleDef = [("名称", 12, "name"), ("所在目录", 6, "folderName"), ("类型", 5, "ext"), ("大小", 5, "size"),
                         ("修改时间", 8, "mtime"),
                         ("创建时间", 8, "ctime"), ("本地状态", 5, "state")]

        self.title, self.col_len_l = rowTitle(self.titleDef)

        self.titleList.insert(col_num, self.title)

        col_num += 1
        self.titleList.insert(col_num, lenUtf(self.title) * "-" + "\n")

        # 同步按钮
        rowX = self.lSpace
        rowY += self.titleList.winfo_reqheight() + 20
        self.uploadBtn = ttk.Button(self.tab, style="basic.TButton",
                                    text="全部上传同步",
                                    command=lambda: self.syncFiles('upload'))
        self.uploadBtn.place(x=rowX, y=rowY)

        rowX += self.uploadBtn.winfo_reqwidth() + 20
        self.downloadBtn = ttk.Button(self.tab, style="basic.TButton",
                                      text="全部下载同步",
                                      command=lambda: self.syncFiles('download'))
        self.downloadBtn.place(x=rowX, y=rowY)

        rowX += self.downloadBtn.winfo_reqwidth() + 20
        self.syncAllBtn = ttk.Button(self.tab, style="basic.TButton",
                                     text="一键同步【上传+下载】",
                                     command=lambda: self.syncFiles('syncAll'))
        self.syncAllBtn.place(x=rowX, y=rowY)

        # 显示进度条
        rowX = self.lSpace
        rowY += self.syncAllBtn.winfo_reqheight() + 10

        self.syncProgressBarVal = DoubleVar()

        self.syncProgressBar_l = ttk.Label(self.tab, text='执行进度:' + ' ' * 10, style='basic.TLabel')
        self.syncProgressBar_l.place(x=rowX, y=rowY)

        rowX += self.syncProgressBar_l.winfo_reqwidth() + 5
        self.syncProgressBar = ttk.Progressbar(self.tab, variable=self.syncProgressBarVal, length='400',
                                               mode='determinate')
        self.syncProgressBar.place(x=rowX, y=rowY)
        self.root.syncProgressBar = self.syncProgressBar
        self.root.syncProgressBarVal = self.syncProgressBarVal
        self.syncProgressBarVal.set(0)

        rowY += self.syncProgressBar.winfo_reqheight() + 5
        self.syncProgressInfo_l = ttk.Label(self.tab, text=' ' * 15, style='basic.TLabel', foreground='gray',
                                            font=("黑体", -10))
        self.syncProgressInfo_l.place(x=rowX, y=rowY)
        self.root.syncProgressInfo_l = self.syncProgressInfo_l

        # 显示批量传送进度条
        rowX = self.lSpace
        rowY += self.syncProgressInfo_l.winfo_reqheight() + 5

        self.syncAllProgressBarVal = DoubleVar()

        self.syncAllProgressBar_l = ttk.Label(self.tab, text='整体执行进度:' + ' ' * 6, style='basic.TLabel')
        self.syncAllProgressBar_l.place(x=rowX, y=rowY)

        rowX += self.syncAllProgressBar_l.winfo_reqwidth() + 5
        self.syncAllProgressBar = ttk.Progressbar(self.tab, variable=self.syncAllProgressBarVal, length='400',
                                                  mode='determinate')
        self.syncAllProgressBar.place(x=rowX, y=rowY)
        self.root.syncAllProgressBar = self.syncProgressBar
        self.root.syncAllProgressBarVal = self.syncAllProgressBarVal
        self.syncAllProgressBarVal.set(0)

        rowY += self.syncAllProgressBar.winfo_reqheight() + 5
        self.syncAllProgressInfo_l = ttk.Label(self.tab, text=' ' * 15, style='basic.TLabel', foreground='gray',
                                               font=("黑体", -10))
        self.syncAllProgressInfo_l.place(x=rowX, y=rowY)
        self.root.syncAllProgressInfo_l = self.syncAllProgressInfo_l

    def show(self):
        # self.root.notebook.select(self.root.tabIndexes["同步"])
        self.fill()
        # self.root.myCmd.do_versionCheck()
        # self.viewSyncFiles("upload")
        self.root.notebook.select(0)

    def viewSyncFiles(self, typeStr):
        try:
            self.root.syncListSelected = typeStr
            # if not self.root.upload_files or not self.root.download_files:
            #     self.root.myCmd.do_versionCheck()
            #     self.viewSyncFiles("upload")
            if typeStr == "upload":
                self.showFilelist(self.root.upload_files)
                self.syncIntro_l["text"] = '【本机待上传文件】：以下文件修改时间较新，需要上传同步 '
            elif typeStr == "download":
                self.showFilelist(self.root.download_files)
                self.syncIntro_l["text"] = '【远程待下载文件】：以下文件本机缺失或版本较旧，需要下载同步 '
            elif typeStr == "local":
                # self.showFilelist(makeFileList(self.root.syncFolderVal.get()))
                self.showFilelist(self.root.upload_files + self.root.same_files)
                self.syncIntro_l["text"] = '【本机同步文件夹】：以下文件本机同步文件夹中内容，请将需要同步的文件拷入'
        except Exception as e:
            self.root.logger.info(e)

    def syncRenew(self):
        self.root.myCmd.do_versionCheck()
        self.viewSyncFiles("upload")

    def syncFiles(self, typeStr):
        self.root.syncListSelected = "local"
        if typeStr == "download":
            self.root.myCmd.do_syncDownloadAll()
        elif typeStr == "upload":
            self.root.myCmd.do_syncUploadAll()
        elif typeStr == "syncAll":
            self.root.syncListSelected = "syncAll"
            self.root.myCmd.do_syncAll()

        self.root.myCmd.do_versionCheck()
        self.viewSyncFiles("local")

    def fileChoosed(self, event):
        w = event.widget
        line = w.curselection()
        if line[0] < 2:
            self.info("选择错误")
            return
        info = self.fileList[line[0] - 2]

        # 处理文件上传、下载
        if info["state"] == "远程较新" or info["state"] == "本地尚无":  # download
            yesno = messagebox.askyesno('提示', '要下载文件{}吗'.format(info["name"]))
            if yesno:
                self.root.myCmd.do_syncDownload(info)
        elif info["state"] == "本地新建" or info["state"] == "本地较新":  # upload
            yesno = messagebox.askyesno('提示', '要上传文件{}至服务器同步文件夹吗'.format(info["name"]))
            if yesno:
                self.root.myCmd.do_syncUpload(info)
        elif info["state"] == "已作同步":
            messagebox.showwarning('提示', '文件{}已进行过同步，本地与远程信息一致'.format(info["name"]))

        self.root.myCmd.do_versionCheck()
        self.viewSyncFiles(self.root.syncListSelected)


def main():
    r = Root((800, 600))
    r.login()
    print("loop")

    r.wnd.mainloop()


if __name__ == '__main__':
    main()
