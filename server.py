from xmlrpc.client import ServerProxy, Fault, Binary
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
from os.path import join, isfile, abspath
from urllib.parse import urlparse
from time import sleep
from threading import Thread
from myUtils import *
from p2pClient import MyClient
import re
import sys
import json

OK = 1
FAIL = 2
EMPTY = ''
PASSWORD = '89'
SimpleXMLRPCServer.allow_reuse_address = 1
UNHANDLED = 100
ACCESS_DENIED = 200
SERVER_START_PATH = "C:\\AlexP2P\\"
VERSION = 1.0



class UnhandledQuery(Fault):  # 远程无法抛异常，只能通过Fault的faultcode来处理，Fault被客户端作为异常处理
    def __init__(self, message="Couldn't handle the query "):
        super().__init__(UNHANDLED, message)


class AccessDenied(Fault):
    def __init__(self, message="Access denied"):
        super().__init__(ACCESS_DENIED, message)


class MyCmd:
    def __init__(self, fromW, sendW='', cmdC='', args=[], nextCmd='notice', nextArg=[],
                 id=time.strftime("%Y%m%d %H:%M:%S", time.localtime())):
        self.fromW = fromW
        self.sendW = sendW
        self.cmdC = cmdC
        self.args = args
        self.state = 0  # 0 为待执行 1为已获取
        self.nextCmd = nextCmd  # 执行完后下一步操作 默认为通知完成
        self.id = id





def get_port(url):  # 从URL中提取port
    name_l = urlparse(url)
    print(name_l)
    name = name_l[1]
    port = name.split(":", 1)[1]


def inside(dir, name):  # 用于防止 /a/../b/c攻击
    dir = abspath(dir)
    name = abspath(name)
    return name.startswith(join(dir, ''))


class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

    def do_POST(self):
        try:
            SimpleXMLRPCRequestHandler.do_POST(self)
        except Exception as e:
            print("do_post exception:", e)


class MyServer:
    def __init__(self, url, port, dirname, secret=PASSWORD):
        self.dirname = dirname
        self.url = url
        self.known = set()
        self.secret = secret
        self.port = port
        self.clients = {}
        self.cmds = []
        self.sessionState = {}
        self.trans_ok = 0
        self.break_out = 0
        self.startPath = SERVER_START_PATH
        self.logger = logInit("server.log")

    def ilog(self, *args, show=0):
        msg = re.sub(r"\(|\)|,|'", '', str(args))
        self.logger.info(msg)

    @rpcEx
    def _start(self):
        s = SimpleXMLRPCServer(("", self.port), requestHandler=RequestHandler, logRequests=False)
        s.register_instance(self)
        # h = s.get_request()
        # x = h[1]
        s.register_introspection_functions()
        print("server start....")
        self.server = s
        s.serve_forever()

    @rpcEx
    def updateClient(self, name, clientInfo):  # 客户端信息更新
        self.clients[name] = clientInfo
        self.updateClientStamp(name)
        # self.ilog(clientInfo["clientNameVal"], self.server.get_request()[1], " 已更新信息.....", nowStr())
        self.ilog(clientInfo["clientNameVal"], " 已更新信息.....", nowStr())
        return 1

    def updateClientStamp(self, name):  # 更新时间戳
        self.clients[name]["stamp"] = time.time()
        return 1

    @rpcEx
    def regClient(self, name, clientInfo):  # 注册客户端
        if name not in self.clients.keys():
            pathStr = join(self.startPath, "userData", clientInfo["macAddr"]+ "_" + name)
            if not os.path.exists(pathStr):  # 如果不存在则创建目录
                os.makedirs(pathStr)
                os.makedirs(join(pathStr, "download"))
                os.makedirs(join(pathStr, "sync"))

            self.updateClient(name, clientInfo)
            self.ilog(clientInfo["clientNameVal"], " 已注册.....", nowStr())
            return 1
        else:
            self.ilog(clientInfo["clientNameVal"], " 名称已存在，请更换名称.....", nowStr())
            raise Fault(2, clientInfo["clientNameVal"] + "服务器已有连接")

    def changeDir(self, fromW, SendW, dirName):  # 改变client当前目录
        cmd = MyCmd(fromW, SendW, 'changeDir', [dirName])
        self.sendCmd(cmd)
        return 0

    def sendInfo(self, fromW, sendW, info):  # 发送信息
        cmd = MyCmd(fromW, sendW, 'info', [info])
        self.sendCmd(cmd)
        return 0

    def getClient(self, name):  # 客户端信息
        return self.clients[name]

    # return 0
    @rpcEx
    def getClientList(self):
        # 检查并剔除超时未连接的客户端
        for name in self.clients.copy():
            client = self.clients[name]
            clientName = client["clientNameVal"]
            if time.time() - client["stamp"] > 5 * 60:  # 5分钟
                del self.clients[clientName]
                self.ilog(client["clientNameVal"], " 连接超时，从清单清除.....", nowStr())
        return self.clients

    def getCmd(self, name):  # 获取待执行任务
        try:
            self.updateClientStamp(name)
            for cmd in self.cmds:
                if cmd.sendW == name and cmd.state == 0:
                    with open("state.txt", "w") as f:
                        f.write("1")
                    cmd.state = 1
                    return 1, cmd
        except Fault as f:
            print(f)
        # raise f

        return 0, self.cmds

    def sendCmd(self, cmd):
        self.cmds.append(cmd)
        return len(self.cmds)

    def setSessionState(self, clientName, item, value, state=0):
        self.sessionState[clientName] = {}
        self.sessionState[clientName][item] = value
        self.sessionState[clientName]["state"] = state
        return 0

    def getSessionState(self, clientName, item):
        return self.sessionState[clientName][item], self.sessionState[clientName]["state"]

    def getFileFromOther(self, fromW, byW, pathStr, filename):  # 从另一台电脑上获取文件
        cmd = MyCmd(byW, fromW, 'sendFileToServer', [pathStr, filename], 'noticeToGetFile')
        self.sendCmd(cmd)
        return 0

    @rpcEx
    def sendFileToServer(self, data, filename, fromW=None, syncPath="download"):  # 向服务器发送文件 sendType 标记下载 或同步
        if data.data == b'': #处理空文件
            data.data = b' '
        pathStr = join(self.startPath, "userData", self.clients[fromW]["macAddr"] + "_" + fromW)

        syncPath = re.sub('^[\\\/]', '', syncPath)  # 去掉开头的\或/
        pathStr = join(pathStr, syncPath)
        if not path.exists(pathStr):
            os.makedirs(pathStr, exist_ok=True)

        f = open(join(pathStr, filename), 'wb')
        f.write(data.data)
        f.close()
        self.trans_ok = 1
        self.ilog("已保存远端上传文件{}到{}".format(filename,pathStr))
        return 1

    def noticeToGetFile(self, fromW, sendW, filename):
        cmd = MyCmd(fromW, sendW, 'getFileFromServer', [filename])
        self.cmds.append(cmd)

        return 0

    def getFileFromServer(self, filename, dirName,typeStr="download"):
        self.query(filename, PASSWORD, dirName , typeStr)
        return 0


    def checkLogin(self,clientName,macAddr,clientPW): # 从info文件核对密码，判断能否连接
        pathStr = join(self.startPath, "userData", macAddr + "_" + clientName,macAddr+".info")
        if not path.exists(pathStr):
            return -1
        else:
            with open(pathStr) as f:
                data = json.loads(json.load(f))
                self.ilog("核对{}的密码:{},传入：{}".format(clientName,data["passwordVal"],clientPW))
            if data["passwordVal"] == clientPW:
                return 1
            else:
                return 0

    def checkVer(self,versionNo): #核对软件版本
        self.ilog("核对版本，服务器{},客户端{}".format(VERSION,versionNo))
        if versionNo < VERSION:
            return -1
        else:
            return 1

    def getIntro(self): #读取帮助信息
            pathStr = join(self.startPath, "help.txt")
            intro = []
            with open(pathStr, 'r', encoding='utf-8') as f:
                intro = f.readlines()
            return intro




    def _handle(self, query):
        dir = self.dirname
        name = join(dir, query)
        if not isfile(name):
            raise UnhandledQuery
        if not inside(dir, name): raise AccessDenied
        return Binary(open(name, 'rb').read())

    @rpcEx
    def query(self, filename, clientName, syncPath="download"): #syncPath 为同步目录的文件相对路径 ，默认为下载目录
        # pathStr = self.clients[clientName]["serverDownload"]
        pathStr = join(self.startPath, "userData", self.clients[clientName]["macAddr"] + "_" + clientName)

        pathStr = join(pathStr, syncPath, filename)
        self.ilog("读取文件：", pathStr)
        return Binary(open(pathStr, 'rb').read())

    @rpcEx
    def fetch(self, query, secret, dirname):
        if dirname == None:
            dirname = self.dirname
        # if secret != self.secret: raise AccessDenied
        data = self.query(query).data
        f = open(join(dirname, query), 'wb')
        f.write(data)
        f.close()
        return 0

    def getSyncInfoFromServer(self,clientName,macAddr): # 从服务器上读取用户的同步文件时间戳
        pathStr = join(self.startPath, "userData", macAddr + "_" + clientName) # clientName 发起同步获取请求的客户端
        pathStr = join(pathStr, "sync")

        sInfo = {}

        for root, dirs, files in os.walk(pathStr):
            fPath = getReDir(root, pathStr) # 保留的目录为从同步文件开始的路径，以保证服务器与客户端一致
            for f in files:
                sInfo[join(fPath,f)] ={}
                sInfo[join(fPath, f)]["mtime"] = os.path.getmtime(join(root,f))
                sInfo[join(fPath, f)]["size"] = os.path.getsize(join(root, f))
        return sInfo


    def getSyncInfoListFromServer(self, clientName,macAddr,pathList,state=None): #获取服务器中列表的详细信息

        infoList = []
        for f in pathList:
            f = re.sub('^[\\\/]', '', f) # 去掉开头的\或/
            pathStr = join(self.startPath, "userData", macAddr + "_" + clientName, "sync", f)  # clientName 发起同步获取请求的客户端
            filename = os.path.basename(pathStr)
            dirname = os.path.dirname(pathStr)
            info = fileInfo(filename, dirname)
            if info:
                info["state"] = state
                infoList.append(info)

        return infoList



    def hello(self, other):
        if other not in self.known:
            self.known.add(other)  # other 为URL
        return 0

    def _broadcast(self, query, history):
        for other in self.known.copy():
            if other in history: continue  # 已广播查询过
            try:
                s = ServerProxy(other)
                k = s.query(query, history)
                return k
            except Fault as f:
                if f.faultCode == UNHANDLED:
                    pass
                else:
                    self.known.remove(other)
            except:
                self.known.remove(other)
        raise UnhandledQuery

    @rpcEx
    def test(self):
        # try:
        a = ['3']
        print(a[1])
        return 0
    # except Exception as e:
    # 	raise Fault(0, str(e))


def main():
    port, dirname = sys.argv[1:]
    url, secret = '', '123'
    s = MyServer(url, int(port), dirname, secret)

    clientName = 'server'

    # 启动服务器端线程
    severThread = Thread(target=s._start)
    severThread.setDaemon(False)
    severThread.start()

    sleep(0.5)
    # 启动作为客户端的线程
    # c = MyClient(clientName,listdir(clientName),clientName)
    c = MyClient()
    clientThread = Thread(target=c.clientLoop)
    clientThread.setDaemon(True)
    clientThread.start()


if __name__ == '__main__':
    print("start..")
    main()
# print(sys.argv)
