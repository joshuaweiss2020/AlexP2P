from xmlrpc.client import ServerProxy,Binary
from os import listdir

import sys,time
#import server 
from os.path import join,isfile,abspath
#s = ServerProxy('http://106.13.113.252:9001')

URL = "http://106.13.113.252:9001"
#URL = "http://127.0.0.1:2001"
def mPrint(*args):
	print(*args)

class MyClient:
	def __init__(self,clientName,fileList,dirName):
		self.clientName = clientName
		self.fileList = fileList
		self.dirName = dirName
		self.absDir = sys.path[0] 
		self.proxy = ServerProxy(URL)

		self.updateClientInfo()


	def checkCmds(self):
		code,cmd = self.proxy.getCmd(self.clientName)
		#print(str(code),":",cmd)
		if code ==1:
			if cmd["cmdC"] == "sendFileToServer": #传输指定文件到服务器
				try:
					filename = cmd["args"][0]
					data = self.getFileData(filename)
					self.proxy.sendFileToServer(data,filename)
					mPrint("sendFileToServer successfully:",filename)
					self.proxy.noticeToGetFile(self.clientName,cmd["fromW"],filename)
					mPrint("noticeToGetFile successfully:",cmd["fromW"],",",filename)
				except FileNotFoundError as e:
					mPrint(cmd["fromW"],"file:" + filename + " cann't find!")
					self.proxy.sendInfo(self.clientName,cmd["fromW"],"file:" + filename + " cann't find!")
					self.proxy.setSessionState(cmd["fromW"],"fileFetch","fail") 
		
			elif cmd["cmdC"] == "getFileFromServer": #去服务器取文件
				filename = cmd["args"][0]
				data = self.proxy.query(filename)
				self.saveFileInClient(data,filename)
				#self.proxy.getFileFromServer(filename,self.dirName)
				mPrint("download successfully file ",filename)
			elif cmd["cmdC"] == "changeDir":
				#self.dirName = cmd["args"][0]
				self.updateClientInfo(cmd)
				mPrint("changeDir successfully ,dir:",self.dirName)
			elif cmd["cmdC"] == "info":
				info = cmd["args"][0]
				mPrint("Info From ",cmd["fromW"],":",info)				
			else:
				mPrint(cmd)
		return "checking cmds " + time.strftime("%Y%m%d %H:%M:%S", time.localtime())

	def getFileData(self,filename):

		return Binary(open(join(self.dirName,filename),'rb').read())

	def updateClientInfo(self,cmd=None):
		try:
			if cmd:
				dirName = cmd["args"][0]
				fileList = listdir(dirName)
				self.dirName = dirName
				self.fileList = fileList
			self.proxy.updateClient(self.clientName,self.absDir,self.dirName,self.fileList)
		except FileNotFoundError as e:
			self.proxy.sendInfo(self.clientName,cmd["fromW"],dirName + " dir cann't find! Still in " + self.dirName )


	def saveFileInClient(self,data,filename):
		with open(join(self.dirName,filename),'wb') as f:
			f.write(data.data)

	def clientLoop(self):
		print("client threading start....")
		while True:
			self.checkCmds()
			#print(self.checkCmds())
			time.sleep(3)

def main():
		if len(sys.argv)==3:
			URL = sys.argv[2]
		clientName= sys.argv[1]
		#if url:URL = url
		c = MyClient(clientName,listdir(clientName),clientName)
		c.proxy.updateClient(clientName,c.absDir,c.dirName,c.fileList)
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
#print(listdir())

#print("code:",code)
#print("data:",data)
#name='dd.txt'
#pic = s.fetchPIC(name)
#print(type(pic))
#with open(name,'wb') as f:
#	f.write(pic.data)


#s.saveDir('testtest')
#s.hello('http://127.0.0.1:2221')


#code= s.fetch('tt.txt','123','file2')



#code,data = s.query('tt.txt')

#print("code:",code)
#print("data:",data)

'''
url,port,dirname,secret = '',2221,'file2','123'
n = Node(url,port,dirname,secret)
print("start.... 2222")
n._start()
'''
