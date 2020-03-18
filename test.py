
t = "中国人tt"
print(len(t))
print(len(t.encode("utf-8")))

a ={"占":1,"占3":2,"占1":2}

for k in a:
    print(k,a[k])

titleDef = [("名称", 15, "name"), ("类型", 5, "ext"), ("大小", 5, "size"), ("修改时间", 5, "mtime"),
            ("创建时间", 5, "ctime"), ("本地状态", 5, "stat")]

p = "c:/aa/dd/"

i=p.rindex("/",0,len(p)-1)
print(p[0:i+1])

import re
def f(*args):
    msg = re.sub(r"\(|\)|,|'", '', str(args))
    print(msg)
    msg = str(args).replace("(", "")
    msg = str(msg).replace(")", "")
    msg = str(msg).replace(",", " ")
    msg = str(msg).replace("'", " ")

    print(msg)

f("dd","ff")


from tkinter import ttk
from tkinter import *
import time
import tkinter.font as tkFont
wnd = Tk()
shape = (800, 600)
wnd.title("Alex P2P 文件传送器")
screenwidth = wnd.winfo_screenwidth()
screenheight = wnd.winfo_screenheight()
alignstr = '%dx%d+%d+%d' % (
    shape[0], shape[1], (screenwidth - shape[0]) / 2, (screenheight - shape[1]) / 2)  # 屏幕居中
wnd.geometry(alignstr)


pVal = DoubleVar()

style = ttk.Style()
style.configure("style.Label", foreground="black", background="lightgray", font=("黑体", -10))
#

progressBar_l = ttk.Label(wnd, text='执行进度:', style='style.Label')
progressBar_l.place(x=100, y=100)

p= ttk.Progressbar(wnd, variable=pVal, length='400', mode='determinate', maximum=100)
p.place(x=100, y=300)

btn = Button(wnd, text="选择...", font=("黑体", 9),
                                 command=lambda: btntest(1), relief=GROOVE)

btn.place(x=500, y=300)


def btntest(t):

    pVal.set(0)
    i=1
    while i<=5:
        p.step(20)
        # pVal.set(i*5)
        p.update()
        time.sleep(1)
        print(i)
        i+=1

    p.stop()
f = tkFont.Font(family='黑体',size=-12)
print(f.metrics())
#print(tkFont.families())
#wnd.mainloop()

#p.step(5)
#p.step(10)














#for k,v in titleDef:
#    print(k[1],v)

''' 
from myUtils import *
from xmlrpc.client import ServerProxy, Fault, Binary
from myUtils import MyException

URL = "http://127.0.0.1:2001"
URL = "http://106.13.113.252:9001"
proxy = ServerProxy(URL)
clientName = "server"
clientInfo = {}
clientInfo["clientNameVal"] = "DadMac"
clientInfo["downloadFolderVal"] = "DadMac"
clientInfo["syncFolderVal"] = "DadMac"
clientInfo["macAddr"] = getMacAdr()
try:
    #proxy.regClient("DadMac", clientInfo)
    c = proxy.getClient("DavidWeiss")
    print(c)
    raise MyException("test error")

   # proxy.test()
except Fault as f:
    print("F:", f)
except Exception as e:
    print("e:", e)



@catchRpcEx
def t(proxy):
    #proxy.test()
    print(proxy.getClientList())


# t(proxy)
# print()

# from tkinter import ttk
# help(ttk.Combobox)
f = {"a": 1, "b": 2}
for a in f:
    if a == "b":
        f["b"]=3

print(f)

class cc:
    def f_cc(self):
        print("fcc")

a = cc()

print(dir(a.f_cc))
'''