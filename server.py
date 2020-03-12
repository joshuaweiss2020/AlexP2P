from xmlrpc.client import ServerProxy, Fault, Binary
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
from os.path import join, isfile, abspath
from urllib.parse import urlparse
from time import sleep
import time
from threading import Thread
from os import listdir
from myUtils import *
from p2pClient import MyClient, URL

import sys

OK = 1
FAIL = 2
EMPTY = ''
PASSWORD = '89'
SimpleXMLRPCServer.allow_reuse_address = 1
UNHANDLED = 100
ACCESS_DENIED = 200


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


def ilog(*args, show=0):
	print(*args)


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
		# ilog(clientInfo["clientNameVal"], self.server.get_request()[1], " 已更新信息.....", nowStr())
		ilog(clientInfo["clientNameVal"], " 已更新信息.....", nowStr())
		return 1

	def updateClientStamp(self, name):  # 更新时间戳
		self.clients[name]["stamp"] = time.time()
		return 1

	@rpcEx
	def regClient(self, name, clientInfo):  # 注册客户端
		if name not in self.clients.keys():
				if not os.path.exists(name):  # 如果不存在则创建目录
					os.makedirs(name)
				if not os.path.exists(join(name, clientInfo["downloadFolderVal"])):  # 如果不存在则创建目录
					os.makedirs(join(name, clientInfo["downloadFolderVal"]))
				if not os.path.exists(join(name, clientInfo["syncFolderVal"])):  # 如果不存在则创建目录
					os.makedirs(join(name, clientInfo["syncFolderVal"]))
				self.updateClient(name, clientInfo)
				ilog(clientInfo["clientNameVal"], " 已注册.....", nowStr())
				return 1
		else:
			ilog(clientInfo["clientNameVal"], " 名称已存在，请更换名称.....", nowStr())
			raise Fault(2, "名称已存在，请更换名称")
			return 0

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
		for name in self.clients:
			client = self.clients[name]
			if time.time() - client["stamp"] > 5 * 60:  # 5分钟
				del self.clients[client["clientNameVal"]]
				ilog(client["clientNameVal"], " 连接超时，从清单清除.....", nowStr())
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

	def setSessionState(self, clientName, item, value):
		self.sessionState[clientName] = {}
		self.sessionState[clientName][item] = value
		return 0

	def getSessionState(self, clientName, item):
		return self.sessionState[clientName][item]

	def getFileFromOther(self, fromW, byW, filename):  # 从另一台电脑上获取文件
		cmd = MyCmd(byW, fromW, 'sendFileToServer', [filename], 'noticeToGetFile')
		self.sendCmd(cmd)
		return 0

	def sendFileToServer(self, data, filename):  # 向服务器发送文件
		f = open(join('server', filename), 'wb')
		f.write(data.data)
		f.close()
		self.trans_ok = 1
		return 1

	def noticeToGetFile(self, fromW, sendW, filename):
		cmd = MyCmd(fromW, sendW, 'getFileFromServer', [filename])
		self.cmds.append(cmd)
		return 0

	def getFileFromServer(self, filename, dirName):
		self.fetch(filename, PASSWORD, dirName)
		return 0

	def _handle(self, query):
		dir = self.dirname
		name = join(dir, query)
		if not isfile(name):
			raise UnhandledQuery
		if not inside(dir, name): raise AccessDenied
		return Binary(open(name, 'rb').read())

	def query(self, query, history=[]):
		try:
			return self._handle(query)
		except UnhandledQuery:
			raise
		# history = history + [self.url + str(self.port)]
		# return self._broadcast(query,history)
		# return FAIL,EMPTY

	def fetch(self, query, secret, dirname):
		if dirname == None:
			dirname = self.dirname
		# if secret != self.secret: raise AccessDenied
		data = self.query(query).data
		f = open(join(dirname, query), 'wb')
		f.write(data)
		f.close()
		return 0

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
	main()
# print(sys.argv)