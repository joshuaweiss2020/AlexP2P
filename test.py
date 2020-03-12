
t = "中国人tt"
print(len(t))
print(len(t.encode("utf-8")))

a ={"占":1,"占3":2,"占1":2}

for k in a:
    print(k,a[k])

titleDef = [("名称", 15, "name"), ("类型", 5, "ext"), ("大小", 5, "size"), ("修改时间", 5, "mtime"),
            ("创建时间", 5, "ctime"), ("本地状态", 5, "stat")]

#for k,v in titleDef:
#    print(k[1],v)



from myUtils import *
from xmlrpc.client import ServerProxy, Fault, Binary

URL = "http://127.0.0.1:2001"
proxy = ServerProxy(URL)
clientName = "server"
clientInfo = {}
clientInfo["clientNameVal"] = "DadMac"
clientInfo["downloadFolderVal"] = "DadMac"
clientInfo["syncFolderVal"] = "DadMac"
clientInfo["macAddr"] = getMacAdr()
try:
    proxy.regClient("DadMac", clientInfo)
   # proxy.test()
except Fault as f:
    print("F:", f)
except Exception as e:
    print("e:", e)



@catchRpcEx
def t(proxy):
    #proxy.test()
    print(proxy.getClientList())


t(proxy)
# print()

from tkinter import ttk
help(ttk.Combobox)
