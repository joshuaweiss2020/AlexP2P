from xmlrpc.client import ServerProxy, Binary, Fault
from myUtils import *
import sys, time
# import server
import os
import re
from os.path import join, isfile, abspath
from tkinter import StringVar, IntVar

# s = ServerProxy('http://106.13.113.252:9001')

URL = "http://106.13.113.252:9001"


URL = "http://127.0.0.1:2001"
VERSION = 1.0


class MyClient:
    @catchRpcEx
    def __init__(self, setupTab=None):
        self.clientInfo = {}
        cmd = None
        if not setupTab:  # 以server方式启动client
            self.clientName = "server"
            self.clientInfo["clientNameVal"] = "server"
            self.clientInfo["downloadFolderVal"] = "C:\\AlexP2P\\server\\"
            self.clientInfo["syncFolderVal"] = "server"
            self.clientInfo["passwordVal"] = "server"
            cmd = {"args": ["server"]}
            self.clientInfo["macAddr"] = "server"
            self.root = None

        else:
            self.clientName = setupTab.clientNameVal.get()

            self.clientInfo["macAddr"] = getMacAdr()

            for attr in dir(setupTab):
                if isinstance(getattr(setupTab, attr), StringVar) or isinstance(getattr(setupTab, attr), IntVar):
                    self.clientInfo[attr] = getattr(setupTab, attr).get()

        if not os.path.exists(self.clientInfo["downloadFolderVal"]):  # 如果不存在则创建目录
            os.makedirs(self.clientInfo["downloadFolderVal"])

        if not os.path.exists(self.clientInfo["syncFolderVal"]):  # 如果不存在则创建目录
            os.makedirs(self.clientInfo["syncFolderVal"])

        self.fileList = makeFileList(self.clientInfo["downloadFolderVal"])
        self.clientInfo["fileList"] = self.fileList

        self.clientInfo["sep"] = os.sep

        self.dirName = self.clientInfo["downloadFolderVal"]  # 当前文件夹默认为下载文件夹

        self.absDir = sys.path[0]

        self.proxy = ServerProxy(URL)

        self.proxy.regClient(self.clientName, self.clientInfo)

    @catchRpcEx
    def checkCmds(self):
        code, cmd = self.proxy.getCmd(self.clientName)
        # print(str(code),":",cmd)
        if code == 1:
            if cmd["cmdC"] == "sendFileToServer":  # 传输指定文件到服务器
                try:
                    pathStr = cmd["args"][0]
                    filename = cmd["args"][1]
                    data = self.getFileData(join(pathStr, filename))
                    self.proxy.setSessionState(cmd["fromW"], "fileFetch", nowStr() + " 已从{}找到文件{}".format(self.clientName,filename),2)
                    self.proxy.sendFileToServer(data, filename, cmd["fromW"])

                    self.proxy.setSessionState(cmd["fromW"], "fileFetch",
                                               nowStr() + " 已准备好文件{}".format(filename), 3)

                    self.mPrint("sendFileToServer successfully:", filename)
                    self.proxy.noticeToGetFile(self.clientName, cmd["fromW"], filename)
                    self.mPrint("noticeToGetFile successfully:", cmd["fromW"], ",", filename)
                except FileNotFoundError as e:
                    self.mPrint(cmd["fromW"], "file:" + filename + " cann't find!")
                    self.proxy.sendInfo(self.clientName, cmd["fromW"], "file:" + filename + " cann't find!")
                    self.proxy.setSessionState(cmd["fromW"], "fileFetch", nowStr() + " 未找到文件{}".format(filename), -1)

            elif cmd["cmdC"] == "getFileFromServer":  # 去服务器取文件
                filename = cmd["args"][0]
                self.proxy.setSessionState(self.clientName, "fileFetch",
                                           nowStr() + " 开始传回文件{}".format(filename), 4)
                data = self.proxy.query(filename, self.clientName)
                self.saveFileInClient(data, filename)
                # self.proxy.getFileFromServer(filename,self.dirName)
                self.mPrint("文件{} 下载成功！ 存放于{} ".format(filename, self.clientInfo["downloadFolderVal"]))
            elif cmd["cmdC"] == "changeDir":
                # self.dirName = cmd["args"][0]
                self.updateClientInfo(cmd)
                self.mPrint("切换目录成功，当前目录:", self.dirName)
            elif cmd["cmdC"] == "info":
                info = cmd["args"][0]
                self.mPrint("Info From ", cmd["fromW"], ":", info)
            else:
                self.mPrint(cmd)
        return "checking cmds " + time.strftime("%Y%m%d %H:%M:%S", time.localtime())

    def getFileData(self, filename,dirName=None):
        if not dirName:
            dirName = self.dirName
        return Binary(open(join(dirName, filename), 'rb').read())

    def updateClientInfo(self, cmd=None):
        dirName=""
        try:
            if cmd:
                dirName = cmd["args"][0]
                fileList = makeFileList(dirName)
                self.dirName = dirName
                self.fileList = fileList
                self.clientInfo["fileList"] = fileList
            # self.clientInfo["downloadFolderVal"] = dirName
            self.proxy.updateClient(self.clientName, self.clientInfo)
        except FileNotFoundError as e:
            self.proxy.sendInfo(self.clientName, cmd["fromW"], dirName + " 目录未找到，返回原目录 " + self.dirName)

    def saveFileInClient(self, data, filename ,syncDir=None):
        if syncDir == None: # 下载
            pathStr = self.clientInfo["downloadFolderVal"]
        else: # 同步
            pathStr = join(self.clientInfo["syncFolderVal"], syncDir)
            if not path.exists(pathStr):
                os.makedirs(pathStr, exist_ok=True)

        with open(join(pathStr, filename), 'wb') as f:
            f.write(data.data)

    def clientLoop(self):
        print("client threading start....")
        while True:
            self.checkCmds()
            # print(self.checkCmds())
            time.sleep(3)

    def mPrint(self, *args):
        msg = re.sub(r"\(|\)|,|'", '', str(args))
        if self.root:
            self.root.infoList.insert(1.0, nowStr() + " " + msg + "...\n")
            print(*args)
        else:
            print(*args)

def main():
    if len(sys.argv) == 3:
        URL = sys.argv[2]
    clientName = sys.argv[1]
    # if url:URL = url
    c = MyClient(clientName, os.listdir(clientName), clientName)
    c.proxy.updateClient(clientName, c.absDir, c.dirName, c.fileList)
    print("client start....")
    c.clientLoop()


if __name__ == '__main__':
    main()

'''
s = ServerProxy('http://127.0.0.1:2222')

name = 'officePC'
print(s.test3())

c = MyClient(name,listdir(name),name)
#data = s.query('tt.txt')
print(s.updateClient(name,c))

print(s.getClient(name))

#cmd = MyCmd(name,name,'getClient',['Alex',1])

#print(s.sendCmd(cmd))

c = True
while c:
	time.sleep(5)
	code,cmd = s.getCmd(name)
	print("code:",code,"cmd",cmd)
	#if code==1:
	#	print("code:",code,"cmd",cmd)
	#	c=False

print('finish')


'''
# print(listdir())

# print("code:",code)
# print("data:",data)
# name='dd.txt'
# pic = s.fetchPIC(name)
# print(type(pic))
# with open(name,'wb') as f:
#	f.write(pic.data)


# s.saveDir('testtest')
# s.hello('http://127.0.0.1:2221')


# code= s.fetch('tt.txt','123','file2')


# code,data = s.query('tt.txt')

# print("code:",code)
# print("data:",data)

'''
url,port,dirname,secret = '',2221,'file2','123'
n = Node(url,port,dirname,secret)
print("start.... 2222")
n._start()
'''
