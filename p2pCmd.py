from xmlrpc.client import ServerProxy,Fault
from cmd import Cmd
from os import listdir
from threading import Thread
from multiprocessing import Process
from time import sleep
import os
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


	def do_fetch(self,arg):
		args = arg.split(" ")
		fromW,filename = args[0],args[1] 
		try:
			if  not isfile(join(self.clientName,filename)):
				self.proxy.getFileFromOther(fromW,self.clientName,filename)
				print("From ",fromW,":",filename," start getting file.....")
				self.proxy.setSessionState(self.clientName,"fileFetch","0") 
				i=0
				while not isfile(join(self.clientName,filename)):
					
					state = self.proxy.getSessionState(self.clientName,"fileFetch")
					if state == "fail":
						sleep(4)
						return
					sleep(1)
					i+=1
					if i>20:
						print("time out")
						return
				print("From ",fromW,":",filename," checked successfully")
			else:
				print(filename," is existed!")

		except Fault as f:
			if f.faultCode != UNHANDLED: raise
			#print(f.faultCode)
			print("Couldn't find file:",arg)
		#finally:
		#	print("fail")

	def do_get(self,arg):
		filename = arg
		if self.host == self.clientName:
			print("use conn to set host firstly..")
		else:
			self.do_fetch(self.host + " " + filename)



	def do_test(self,arg,arg1='arg1'):
		print("arg:",arg,"arg1:",arg1)
			
	def do_cd(self,arg):
		#args = arg.split(" ")
		#clientName,dirName = args[0],args[1] 
		dirName = arg
		clientName = self.host
		#print(self.clientName,clientName,dirName)
		self.proxy.changeDir(self.clientName,clientName,dirName)
		print("Start to change ",clientName," dir to ",dirName,"...")
		sleep(4)
		self.do_getClient(clientName)

	@catchRpcEx
	def do_conn(self, host):
		if host.strip()=='':
			self.do_getCl("")
			return
		cl = self.proxy.getClientList()
		if host in cl.keys():
			self.host = host
			print("已连接远程终端： " ,self.host)
			MyCmd.prompt = 'Alex_p2p@' + self.host + '>'
		else:
			print("远程客户端：{} 未注册到服务器".format(host))
		return cl



	def do_getClient(self,clientName):
		c = self.proxy.getClient(clientName)
		print(clientName,":",c["absDir"],"@",c["dirName"],":")
		for f in c["filelist"]:
			print(f)
		return c["filelist"]

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
		print()
		sys.exit()

	do_EOF = do_exit

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
	t1 = Thread(target=myClient.clientLoop)
	t1.setDaemon(True)
	#t1.daemon = True
	t1.start()
	sleep(0.5)
	myCmd = MyCmd(clientName)
	return myClient,myCmd


if __name__ == '__main__':
	main()
