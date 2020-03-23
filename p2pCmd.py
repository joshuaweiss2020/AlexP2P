from xmlrpc.client import ServerProxy
from cmd import Cmd
from os import listdir
from threading import Thread
from time import sleep
import re
from os.path import join, isfile
from p2pClient import URL, MyClient,VERSION
from myUtils import *
import server
import sys




class MyCmd(Cmd):
    prompt = 'Alex_p2p>'

    def __init__(self, clientName):
        Cmd.__init__(self)
        self.clientName = clientName
        self.proxy = ServerProxy(URL)  # 连接自己启动的服务器
        self.host = clientName  # 已连接的对象默认为自己
        MyCmd.prompt = 'Alex_p2p@' + self.host + '>'
        self.root = None

    def do_fetch(self, client, fromW, pathStr, filename):
        downloadDir = client.clientInfo["downloadFolderVal"]
        try:
            if not isfile(join(downloadDir, filename)):
                self.proxy.getFileFromOther(fromW, self.clientName, pathStr, filename)
                self.mPrint("From ", fromW, ":", filename, " start getting file.....")
                self.proxy.setSessionState(self.clientName, "fileFetch", nowStr() + "开始传送文件{}".format(filename), 1)
                self.root.progressBarVal.set(20)
                self.root.progressInfo_l["text"] = nowStr() + \
                                                   "开始从{} 传送文件{} 至 {} ".format(fromW, filename, downloadDir)
                self.root.progressBar.update()
                i = 0
                state_temp = 0
                while not isfile(join(downloadDir, filename)):

                    msg, state = self.proxy.getSessionState(self.clientName, "fileFetch")
                    if state > state_temp:
                        self.root.progressBarVal.set(20 * state)
                        self.root.progressInfo_l["text"] = msg
                        self.root.progressBar.update()
                    #self.mPrint(msg, state)
                    if state == -1 or state == 5:
                        sleep(1)
                        return
                    sleep(1)
                    i += 1
                    if i > 300:
                        self.mPrint("time out")
                        return
                self.mPrint("从 ", fromW, "获取的文件", filename, " 已保存成功！")
                self.root.progressBarVal.set(100)
                self.root.progressInfo_l["text"] = "文件{} 下载成功！ 存放于{} ".format(filename, downloadDir)
            else:
                self.mPrint(downloadDir, " ", filename, " 在下载目录中已存在!")

        except Fault as f:
            self.mPrint("打不到文件:", filename)

    def do_versionCheck(self):  # 同步的版本比较
        upload_files, download_files, same_files = [], [], []

        sInfo = self.proxy.getSyncInfoFromServer(self.clientName, getMacAdr())
        localSyncDir = self.root.myClient.clientInfo["syncFolderVal"]
        sInfo_c = sInfo.copy()  # 用于作比较

        for root, dirs, files in os.walk(localSyncDir):
            fPath = getReDir(root, localSyncDir)  # 保留的目录为从同步文件开始的路径，以保证服务器与客户端一致
            absPathStr = os.path.abspath(root)
            for f in files:
                info = fileInfo(f, absPathStr)
                if join(fPath, f) not in sInfo:  # 远程无文件
                    info["state"] = "本地新建"
                    upload_files.append(info)
                else:
                    localStamp = os.path.getmtime(join(root, f))
                    localSize = os.path.getsize(join(root, f))

                    remoteStamp = sInfo[join(fPath, f)]["mtime"]
                    remoteSize = sInfo[join(fPath, f)]["size"]

                    if localSize == remoteSize:
                        info["state"] = "已作同步"
                        same_files.append(info)

                    elif remoteStamp > localStamp:  # 远程文件较新
                        info["state"] = "远程较新"
                        download_files.append(info)
                    else:  # 本地文件较新
                        info["state"] = "本地较新"
                        upload_files.append(info)

                    del sInfo_c[join(fPath, f)]

        # 对于远程同步存在，但本地不存在的文件，加入到待下载列表
        download_files += self.proxy.getSyncInfoListFromServer(self.clientName, getMacAdr(), list(sInfo_c.keys()),
                                                               '本地尚无')

        self.mPrint("已完成同步信息刷新：待上传文件{}个，待下载文件{}，已同步文件{}个".format(str(len(upload_files)), str(len(download_files)),
                                                                 str(len(same_files))))

        self.root.upload_files, self.root.download_files, self.root.same_files = upload_files, download_files, same_files
        return upload_files, download_files, same_files

    def do_syncDownload(self, info):  # 从服务器下载同步文件
        filename = info["name"]
        # syncPath 为同步目录的文件相对路径
        severSyncDir = join(server.SERVER_START_PATH, "userData", getMacAdr() + "_" + self.clientName, "sync")
        localSyncDir = self.root.myClient.clientInfo["syncFolderVal"]

        if info["dirName"].find(localSyncDir) > -1:
            syncDir = getReDir(info["dirName"], localSyncDir)
        else:
            syncDir = getReDir(info["dirName"], severSyncDir)

        syncDir = re.sub('^[\\\/]', '', syncDir)  # 去掉开头的\或/
        self.root.syncProgressBarVal.set(20)
        self.root.syncProgressInfo_l["text"] = nowStr() + " 开始从同步文件夹传回文件{}".format(filename)
        data = self.proxy.query(filename, self.clientName, join("sync", syncDir))  # 服务器中同步文件在目录sync之下

        self.root.syncProgressBarVal.set(40)
        self.root.syncProgressInfo_l["text"] = nowStr() + " 远程同步文件夹中的文件{} 数据读取成功".format(filename)
        self.root.syncAllProgressBar.update()

        self.root.myClient.saveFileInClient(data, filename, syncDir)
        self.root.syncProgressBarVal.set(100)
        self.root.syncProgressInfo_l["text"] = nowStr() + \
                                               " 文件{}下载同步成功！存放于{}".format(filename,
                                                                          join(self.root.myClient.clientInfo[
                                                                                   "syncFolderVal"], syncDir))
        self.root.syncAllProgressBarVal.set(100)
        self.root.syncAllProgressBar.update()

        self.mPrint("文件{} 下载成功！ 存放于{} ".format(filename, join(self.root.myClient.clientInfo["syncFolderVal"], syncDir)))

    def do_syncDownloadAll(self):  # 下载所有文件
        progress = 0
        fileCount = len(self.root.download_files)
        if self.root.syncListSelected == "syncAll":
            fileCount += len(self.root.upload_files)

        if fileCount == 0:
            step = 100
        else:
            step = 100 / fileCount
        i = 0
        for info in self.root.download_files:
            self.do_syncDownload(info)
            i += 1
            progress += step
            self.root.syncAllProgressBarVal.set(progress)
            self.root.syncAllProgressInfo_l["text"] = nowStr() + " 正在从服务器下载文件({}/{}){}".format(i, fileCount,
                                                                                               info["name"])
            self.root.syncAllProgressBar.update()

        downCount = len(self.root.download_files)
        self.root.syncAllProgressInfo_l["text"] = nowStr() + " 已完成全部下载文件({}/{})".format(downCount,downCount)

        self.mPrint(" 已完成全部下载文件({}/{})".format(downCount,downCount))
        return len(self.root.download_files)

    def do_syncUpload(self, info):  # 从服务器上传同步文件

        filename = info["name"]
        # syncPath 为同步目录的文件相对路径
        syncDir = join(getReDir(info["dirName"], self.root.myClient.clientInfo["syncFolderVal"]))

        self.root.syncProgressBarVal.set(20)
        self.root.syncProgressInfo_l["text"] = nowStr() + " 开始读取本地同步文件夹中文件{}".format(filename)

        data = self.root.myClient.getFileData(join(info["dirName"], filename))
        self.root.syncProgressBarVal.set(40)
        self.root.syncProgressInfo_l["text"] = nowStr() + " 开始向服务器同步文件夹上传文件{}".format(filename)
        self.root.syncAllProgressBar.update()

        syncDir = re.sub('^[\\\/]', '', syncDir)
        syncDir = join("sync", syncDir)
        self.proxy.sendFileToServer(data, filename, self.clientName, syncDir)
        self.root.syncProgressBarVal.set(100)
        self.root.syncProgressInfo_l["text"] = nowStr() + " 文件{}上传同步成功！".format(filename)

        self.root.syncAllProgressBarVal.set(100)
        self.root.syncAllProgressBar.update()

        self.mPrint("文件{} 上传成功至{}！".format(filename, syncDir))

    def do_syncUploadAll(self):  # 上传所有文件
        progress = 0
        i = 0
        fileCount = len(self.root.upload_files)
        if self.root.syncListSelected == "syncAll":  # 处理一键上传的进度条
            fileCount += len(self.root.download_files)
            progress += 100 * len(self.root.download_files) / fileCount
            i += len(self.root.download_files)

        if fileCount == 0:
            step = 100
        else:
            step = 100 / fileCount

        for info in self.root.upload_files:
            self.do_syncUpload(info)
            i += 1
            progress += step
            self.root.syncAllProgressBarVal.set(progress)
            self.root.syncAllProgressInfo_l["text"] = nowStr() + " 正在向服务器上传文件({}/{}){}".format(i, fileCount,
                                                                                               info["name"])
            self.root.syncAllProgressBar.update()

        uploadCount = len(self.root.upload_files)
        self.root.syncAllProgressInfo_l["text"] = nowStr() + " 上传文件同步全部已完成({}/{})".format(uploadCount,uploadCount)

        self.mPrint(" 上传文件同步全部已完成({}/{})".format(uploadCount,uploadCount))

        return len(self.root.upload_files)

    def do_syncAll(self):  # 一键同步
        self.do_syncDownloadAll()
        self.do_syncUploadAll()


        self.root.syncAllProgressInfo_l["text"] = "{} 同步文件全部已完成 (上传：{} 下载：{}) ".format(nowStr(),
                                                                                     len(self.root.upload_files),
                                                                                     len(self.root.download_files))

        self.mPrint(" 同步文件全部已完成( 上传：{} 下载：{} )".format(len(self.root.upload_files),len(self.root.download_files)))


    def do_saveSetupInServer(self): # 在服务器上保存配置信息
        # 保存配置文件
        infoFileName = getMacAdr() + ".info"
        data = self.root.myClient.getFileData(infoFileName, ".")
        rs = self.proxy.sendFileToServer(data, infoFileName, self.clientName, ".")
        return rs


    def do_checkLogin(self,clientPW):
        return self.proxy.checkLogin(self.clientName, getMacAdr() , clientPW)


    def do_checkVer(self):
        return self.proxy.checkVer(VERSION)

    def do_getIntro(self):
        return self.proxy.getIntro()

    def do_get(self, arg):
        filename = arg
        if self.host == self.clientName:
            self.mPrint("use conn to set host firstly..")
        else:
            self.do_fetch(self.host + " " + filename)

    def do_test(self, arg, arg1='arg1'):
        self.mPrint("arg:", arg, "arg1:", arg1)

    def do_cd(self, dirName, fromW=None, toW=None, pw=None):

        if not toW: toW = self.host
        if not fromW: fromW = self.clientName

        # self.mPrint(self.clientName,clientName,dirName)
        self.proxy.changeDir(fromW, toW, dirName)
        self.mPrint("开始进入远程终端 ", toW, " 的目录： ", dirName, "...")

        setProgressBar(self.root.progressBar, 4, 100)

        return self.do_getClient(toW, pw)

    @catchRpcEx
    def do_conn(self, host):
        if host.strip() == '':
            self.do_getCl("")
            return
        cl = self.proxy.getClientList()
        if host in cl.keys():
            self.host = host
            self.mPrint("已连接远程终端： ", self.host)
            MyCmd.prompt = 'Alex_p2p@' + self.host + '>'
        else:
            self.mPrint("远程客户端：{} 未注册到服务器".format(host))
        return cl

    def do_getClient(self, clientName, connPwd='000'):

        client = self.proxy.getClient(clientName)
        clientPassword = client["passwordVal"]
        # self.mPrint(c)

        if clientPassword.strip() == connPwd.strip():
            return client
        else:
            raise MyException("密码:{} 有误，无法连接{}{}".format(connPwd, clientName, "PP"+clientPassword.strip()))

    @catchRpcEx
    def do_getCl(self, args=None):
        cl = self.proxy.getClientList()
        return cl

    def do_getHost(self, args):
        self.do_getClient(self.host)
        c = self.proxy.getClient(self.host)

    do_dir = do_getHost

    def do_exit(self, arg):
        self.mPrint()
        sys.exit()

    do_EOF = do_exit

    def mPrint(self, *args):
        msg = re.sub(r"\(|\)|,|'", '', str(args))
        if self.root:
            self.root.infoList.insert(1.0, nowStr() + " " + msg + "...\n")
        self.root.logger.info(msg)


def main():
    if len(sys.argv) == 3:
        URL = sys.argv[2]
    elif len(sys.argv) == 2:
        clientName = sys.argv[1]

    # urlfile = join(dirname,'url.txt')

    c = MyClient(clientName, listdir(clientName), clientName)

    t1 = Thread(target=c.clientLoop)
    # t1 = Process(target=c.clientLoop(), name="client_p")
    t1.setDaemon(True)
    t1.start()
    sleep(0.5)

    myCmd = MyCmd(clientName)
    t2 = Thread(target=myCmd.cmdloop)
    t2.setDaemon(False)
    t2.start()


# time.sleep(0.5)

# myCmd = MyCmd(clientName)
# myCmd.cmdloop()

@catchRpcEx
def gui_main(setupTab):
    clientName = setupTab.clientNameVal.get()
    if not os.path.exists(clientName):  # 如果不存在则创建目录
        os.makedirs(clientName)

    myClient = MyClient(setupTab)
    # t1 = Process(target=myClient.clientLoop(), name="client_p")
    client_thread = Thread(target=myClient.clientLoop, name="client_thread")
    client_thread.setDaemon(True)
    # t1.daemon = True
    client_thread.start()
    sleep(0.5)

    myCmd = MyCmd(clientName)
    return myClient, myCmd


if __name__ == '__main__':
    main()
