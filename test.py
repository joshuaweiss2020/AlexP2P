
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

#




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


# from myUtils import *
#
# print(nowStr())
# i = 0.01
# while i < 3:
#     i+=0.01
#     time.sleep(0.01)
# print(nowStr())

import tkinter.ttk

style = ttk.Style()
print(style.theme_names())
# style.configure("style.Label", foreground="black", background="lightgray", font=("黑体", 12))
# print(dir(style))

style.configure("basic.TLabel", foreground="black", background="lightgray", font=("黑体", -20))

# style.configure("label.basic.TLabel",font=("黑体", -50))


progressBar_l = ttk.Label(wnd, text='执行进度:', style='basic.TLabel')
progressBar_l.place(x=100, y=100)

p= ttk.Progressbar(wnd, variable=pVal, length='400', mode='determinate', maximum=100)
p.place(x=100, y=300)

btn = Button(wnd, text="选择...", font=("黑体", 9),
                                 command=lambda: btntest(1), relief=GROOVE)

btn.place(x=500, y=200)

infoFrame = ttk.LabelFrame(wnd, width=800, height=20,text="dddfffff中国")
infoFrame.place(x=0, y=600-180)

infoVar = StringVar()
info_l = ttk.Label(infoFrame, text='状态信息:', style="basic.TLabel")


# info_l.grid(row=1, column=1, sticky=W)

import tkinter.scrolledtext

infoList = tkinter.scrolledtext.ScrolledText(infoFrame,
                                             fg='black', bg='lightgray', font=("黑体", -10), relief=GROOVE,
                                             width=140,height=3)

#infoFrame.grid_propagate(0)
infoList.grid(row=0, column=0, sticky=EW)


infoList.insert(1.0, " 欢迎使用Alex P2P 文件传送器\n")










#print(tkFont.families())
#wnd.mainloop()

#p.step(5)
#p.step(10)


import os

# from myUtils import *
#
# for root,dirs,files in os.walk("C:\\AlexP2P\\"):
#     print("root:",getReDir(root,"C:\\AlexP2P\\"))
#     print("dirs:",dirs)
#     for f in files:
#         print(fileInfo(f, root))
#
#
# p = "C:\\AlexP2P\\aa\\"
# p = "/usr/pddd"
# print(getFolderName(p))













#for k,v in titleDef:
#    print(k[1],v)


from myUtils import *
from xmlrpc.client import ServerProxy, Fault, Binary
from myUtils import MyException

URL = "http://127.0.0.1:2001"
# URL = "http://106.13.113.252:9001"
proxy = ServerProxy(URL)
clientName = "DadMac1"
clientInfo = {}
clientInfo["clientNameVal"] = "DadMac1"
clientInfo["downloadFolderVal"] = "DadMac1"
clientInfo["syncFolderVal"] = "DadMac1"
clientInfo["macAddr"] = getMacAdr()
try:
    # proxy.regClient("DadMac1", clientInfo)
    # c = proxy.getClient("DadMac1")
    # print(c)
    # p = proxy.getSyncInfoFromServer(clientName,clientInfo["macAddr"])
    # print(p)
    pass
except Fault as f:
    print("F:", f)
except Exception as e:
    print("e:", e)



# @catchRpcEx
# def t(proxy):
#     #proxy.test()
#     print(proxy.getClientList())
#
#
# # t(proxy)
# # print()
#
# # from tkinter import ttk
# # help(ttk.Combobox)
# f = {"a": 1, "b": 2}
# for a in f:
#     if a == "b":
#         f["b"]=3
#
# print(f)
#
# class cc:
#     def f_cc(self):
#         print("fcc")
#
# a = cc()
#
# print(dir(a.f_cc))
hostname = "aaaa.fdada-fda d "
hostname = re.sub('[ .-]', "_", hostname)
print(hostname)

print(showByWidth("你们好吗hello",10))

data = b"test"
path = os.path.join("C:\\AlexP2P\\userData\\94e6f77fae94_CXYSL_C1CF\\sync\\Log", "Log\\lva_setupfull_20190625141900_0.log")
p = "/log/ald.txt"
p = re.sub('^[\\\/]','',p)

print(p)
#dir = os.path.dirname(path)


#
# os.makedirs(dir, exist_ok=True)
# with open(path, 'wb') as f:
#    f.write(data)
p = "远程办公三足鼎立，飞书能否后来居上，拳打钉钉脚{}...".format("dd")
print(p)


l = logInit("D:\\AlexP2P\\test.log")

l.info("日志")

def aaa(*arg):
    get_invoke_info()
    # print(sys._getframe().f_code.co_filename)  # 当前文件名，可以通过__file__获得
    # print(sys._getframe(0).f_code.co_name) # 当前函数名
    # print(sys._getframe(1).f_code.co_name)  # 调用该函数的函数名字，如果没有被调用，则返回<module>
    # print(sys._getframe(0).f_lineno) #当前函数的行号
    # print(sys._getframe(1).f_lineno) # 调用该函数的行号
    print(arg)

def bbb(*arg):
    aaa(*arg)
bbb(4,"d","ddd")
# a="c:\\fdafda/fdsaf/fdafd"
# a=a.replace("/","\\")
# print(a)