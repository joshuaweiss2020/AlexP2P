from xmlrpc.client import ServerProxy,Fault
from cmd import Cmd
from os import listdir
from threading import Thread
from multiprocessing import Process
from time import sleep
import os
import re
from os.path import join,isfile
from p2pClient import URL,MyClient
from myUtils import *
#from P2P_gui import *
import sys


class UnhandledQuery(Fault): # 远程无法抛异常，只能通过Fault的faultcode来处理，Fault被客户端作为异常处理
	def __init__(self,message="Couldn't handle the query "):
		super().__init__(UNHANDLED,message)

class AccessDenied(Fault):
	def __init__(self,message="Access denied"):
		super().__init__(ACCESS_DENIED,message)


class MyCmd(Cmd):
	prompt = 'Alex_p2p>'

	def __init__(self,clientName):
		Cmd.__init__(self)
		self.clientName=clientName
		self.proxy = ServerProxy(URL)  #连接自己启动的服务器
		self.host = clientName #已连接的对象默认为自己
		MyCmd.prompt = 'Alex_p2p@' + self.host + '>' 
		self.root = None

	def do_fetch(self,client,fromW,pathStr,filename):
		downloadDir = client.clientInfo["downloadFolderVal"]
		#fromW = client.clientName
		#args = arg.split(" ")
		#fromW,filename = args[0],args[1]
		try:
			if  not isfile(join(downloadDir, filename)):
				self.proxy.getFileFromOther(fromW,self.clientName,pathStr,filename)
				self.mPrint("From ",fromW,":",filename," start getting file.....")
				self.proxy.setSessionState(self.clientName, "fileFetch", nowStr() + "开始传送文件{}".format(filename), 1)
				self.root.progressBarVal.set(20)
				self.root.progressInfo_l["text"] = nowStr() + \
												   "开始从{} 传送文件{} 至 {} ".format(fromW, filename,downloadDir)
				self.root.progressBar.update()
				i=0
				state_temp = 0
				while not isfile(join(self.clientName,filename)):
					
					msg, state = self.proxy.getSessionState(self.clientName,"fileFetch")
					if state > state_temp:
						self.root.progressBarVal.set(20 * state)
						self.root.progressInfo_l["text"] = msg
						self.root.progressBar.update()
					self.mPrint(msg, state)
					if state == -1 or state == 5 :
						sleep(1)
						return
					sleep(1)
					i+=1
					if i>20:
						self.mPrint("time out")
						return
				self.mPrint("From ",fromW,":",filename," checked successfully")
				self.root.progressBarVal.set(100)
				self.root.progressInfo_l["text"] = "文件{} 下载成功！ 存放于{} ".format(filename, downloadDir)
			else:
				self.mPrint(downloadDir, " ", filename ," 在下载目录中已存在!")

		except Fault as f:
			#self.mPrint(f.faultCode)
			self.mPrint("Couldn't find file:",filename)
		#finally:
		#	self.mPrint("fail")

	def do_get(self,arg):
		filename = arg
		if self.host == self.clientName:
			self.mPrint("use conn to set host firstly..")
		else:
			self.do_fetch(self.host + " " + filename)



	def do_test(self,arg,arg1='arg1'):
		self.mPrint("arg:",arg,"arg1:",arg1)
			
	def do_cd(self, dirName , fromW=None,toW=None,pw=None):

		if not toW: toW = self.host
		if not fromW: fromW = self.clientName

		#self.mPrint(self.clientName,clientName,dirName)
		self.proxy.changeDir(fromW, toW , dirName)
		self.mPrint("Start to change ", toW ," dir to ",dirName,"...")

		setProgressBar(self.root.progressBar, 4, 100)

		return self.do_getClient(toW, pw)

	@catchRpcEx
	def do_conn(self, host):
		if host.strip()=='':
			self.do_getCl("")
			return
		cl = self.proxy.getClientList()
		if host in cl.keys():
			self.host = host
			self.mPrint("已连接远程终端： " ,self.host)
			MyCmd.prompt = 'Alex_p2p@' + self.host + '>'
		else:
			self.mPrint("远程客户端：{} 未注册到服务器".format(host))
		return cl



	def do_getClient(self,clientName,connPwd='000'):

		client = self.proxy.getClient(clientName)
		clientPassword = client["passwordVal"]
		#self.mPrint(c)

		if clientPassword.strip() == connPwd.strip():
			return client
		else:
			raise MyException("密码:{} 有误，无法连接{},{}".format(connPwd, clientName,clientPassword.strip()))

	@catchRpcEx
	def do_getCl(self,args=None):
		cl = self.proxy.getClientList()
		for c in cl.keys():
			print(c)
		return cl


	def do_getHost(self,args):
		self.do_getClient(self.host)
		c = self.proxy.getClient(self.host)

	do_dir = do_getHost

	def do_exit(self,arg):
		self.mPrint()
		sys.exit()

	do_EOF = do_exit


	def mPrint(self, *args):
		msg = re.sub(r"\(|\)|,|'", '', str(args))
		if self.root:
			self.root.infoList.insert(1.0, nowStr() + " " + msg + "...\n")
			print(*args)
		else:
			print(*args)

def main():
	if len(sys.argv)==3:
		URL = sys.argv[2]
	elif len(sys.argv) ==2:
		clientName = sys.argv[1]

	#urlfile = join(dirname,'url.txt')
	
	c = MyClient(clientName,listdir(clientName),clientName)

	t1 = Thread(target=c.clientLoop)
	#t1 = Process(target=c.clientLoop(), name="client_p")
	t1.setDaemon(True)
	t1.start()
	sleep(0.5)

	myCmd = MyCmd(clientName)
	t2 = Thread(target=myCmd.cmdloop)
	t2.setDaemon(False)
	t2.start()
	#time.sleep(0.5)
		
	#myCmd = MyCmd(clientName)
	#myCmd.cmdloop()

@catchRpcEx
def gui_main(setupTab):
	clientName = setupTab.clientNameVal.get()
	if not os.path.exists(clientName): # 如果不存在则创建目录
		os.makedirs(clientName)

	myClient = MyClient(setupTab)
	#t1 = Process(target=myClient.clientLoop(), name="client_p")
	t1 = Thread(target=myClient.clientLoop, name="client_thread")
	t1.setDaemon(True)
	#t1.daemon = True
	t1.start()
	sleep(0.5)
	myCmd = MyCmd(clientName)
	return myClient, myCmd


if __name__ == '__main__':
	main()
