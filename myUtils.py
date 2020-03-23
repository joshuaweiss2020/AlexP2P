import time
import uuid
import os.path as path
from xmlrpc.client import Fault
from functools import wraps
import traceback
import os


import logging


class MyException(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)
        self.msg = msg

    def __str__(self):
        return "自定义异常：" + self.msg


def logInit(logPath):
    # 创建一个logging对象
    logger = logging.getLogger()
    # 创建一个文件对象  创建一个文件对象,以UTF-8 的形式写入 标配版.log 文件中
    fh = logging.FileHandler(logPath, encoding='utf-8')
    # 创建一个屏幕对象
    sh = logging.StreamHandler()
    # 配置显示格式  可以设置两个配置格式  分别绑定到文件和屏幕上
    formatter = logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')
    fh.setFormatter(formatter)  # 将格式绑定到两个对象上
    sh.setFormatter(formatter)
    logger.addHandler(fh)  # 将两个句柄绑定到logger
    logger.addHandler(sh)
    logger.setLevel(10)  # 总开关
    fh.setLevel(10)  # 写入文件的从10开始
    sh.setLevel(10)  # 在屏幕显示的从30开始
    return logger

def deb(fn):  # 用于调试的装饰器函数
    def debugPrint(*args, **kwargs):
        print("function name:", fn.__name__, ", start debug:", nowStr(), 10 * ">")
        print("inner vars:", fn.__code__.co_varnames)

        # print(objInfo(fn.__code__))
        print("args:", *args)
        print("kwargs:", **kwargs)
        # print(locals())
        print("start execute ", 10 * '>')
        o = fn(*args, **kwargs)
        print("end execute ", nowStr(), 10 * '<')
        print("function return:", o)

    return debugPrint


def rpcEx(fn):  # 用于在 rpc的服务器端向远程客户端抛Fault异常的装饰器
    @wraps(fn)
    def raiseFault(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            print(fn.__class__, ":", fn.__name__, "rpc 调用异常（服务器端）：", str(e))
            traceback.print_exc()
            raise Fault(0, str(e))

    return raiseFault


def catchRpcEx(fn) -> object:  # 用于在rpc的客户端抓取Fault异常的装饰器
    @wraps(fn)
    def catchFault(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Fault as f:
            print(":", fn.__name__, " rpc 远程调用异常（客户端）：", str(f))
        # traceback.print_exc()
        except Exception as e:
            traceback.print_exc()
            print(":", fn.__name__, "rpc 客户端本地调用异常：", str(e))

    # traceback.print_exc()

    return catchFault


def showEx(tab):  # 用于在GUI中显示异常信息的装饰器
    def decorator(fn):
        @wraps(fn)
        def showFault(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Fault as f:
                tab.info("远程调用异常: [", fn.__name__, "]:", str(f))
            # traceback.print_exc()
            except Exception as e:
                tab.info("本地调用异常：[", fn.__name__, "]:", str(e))

        return showFault

    return decorator


def nowStr(fmt="%Y%m%d %H:%M:%S"):
    return time.strftime(fmt, time.localtime())


def timeStr(arg):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(arg))


def objInfo(obj):
    print("object Info:", 10 * '>')
    print(dir(obj))
    print(type(obj))


def getMacAdr():
    mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
    return "".join([mac[e:e + 2] for e in range(0, 11, 2)])


def lenUtf(s=''):
    l = len(s)
    l_utf = len(s.encode("utf-8"))
    return int((l_utf - l) / 2 + l)


def makeFileList(clientPath):  # 生成文件信息列表
    fileList = []
    if not  path.exists(clientPath):
        return  fileList
    fileNameList = os.listdir(clientPath)
    for name in fileNameList:
        info = fileInfo(name, clientPath)
        if info:
            fileList.append(info)

    return fileList


def upFolderPath(pathStr, sep=os.sep):  # 生成到上一级目录的路径
    if not pathStr.endswith(sep):
        pathStr += sep
    i = pathStr.rindex(sep, 0, len(pathStr) - 1)
    return pathStr[0:i + 1]


def setProgressBar(bar, sec, loc):  # 设置进度条，sec为运行秒数，loc会终点位置
    i = 1
    interval = 0.025
    print(nowStr())
    while i <= int(sec / interval):
        i += 1
        bar.step(interval * loc / sec)
        time.sleep(interval)
        bar.update()
    print(nowStr())



def fileInfo(filename, dirname=""):
    info = {}
    info["name"] = filename
    info["dirName"] = dirname
    info["folderName"] = getFolderName(dirname)


    info["path"] = path.join(dirname, filename)
    info["exists"] = path.exists(info["path"])

    if info["exists"]:
        info["isdir"] = path.isdir(info["path"])
        info["ext"] = path.splitext(info["path"])[1]
        if info["isdir"] or info["ext"] == '':
            info["ext"] = "目录"
        # else:
        #	info["ext"] = path.splitext(info["path"])[1]

        info["size"] = str(path.getsize(info["path"]) / 1000) + "Kb"
        info["mtime"] = timeStr(path.getmtime(info["path"]))
        info["mtime_int"] = path.getmtime(info["path"])

        info["ctime"] = timeStr(path.getctime(info["path"]))

        info["state"] = "本地文件"

        return info
    else:
        return None


def compareFile(mtime_int, filePath):  # 比较文件 mtime_int为远程文件最新修改时间 filePath为本地文件路径
    if not path.exists(filePath):
        return "尚未下载", 0, None
    else:
        mtime_int_local = path.getmtime(filePath)
        if mtime_int_local >= mtime_int:
            return "已有最新", 1, timeStr(mtime_int_local)
        else:
            return "已有旧版", 2, timeStr(mtime_int_local)


def rowTitle(titleDef):
    ''' 显示文件列表标题 titleDef为列表，元素为元组(中文名，两边宽度，变量名) '''

    col_len_l = []
    col_len = 0
    title_len = 0
    title = ""
    for col in titleDef:
        title_len = lenUtf(title)
        title += col[0] + " " * (col[1] * 2)
        col_len = lenUtf(title) - title_len
        col_len_l.append(col_len)
    return title + "\n", col_len_l


def rowShow(titleDef, col_len_l, info, localDir=None):
    """ 显示文件列表的每行内容 元素为元组(中文名，两边宽度，变量名) """
    if not info: return "未取到数据" + "\n"
    if localDir:
        info["state"] = compareFile(info["mtime_int"], path.join(localDir, info["name"]))[0]
    if info["isdir"]:
        info["state"] = "【目录】"

    col_num = 0
    col_data = ""
    try:
        for col in titleDef:
            col_width = col_len_l[col_num]
            col_info = showByWidth(info[col[2]], col_width)
            col_width -= lenUtf(col_info) - len(col_info)

            col_fmt = "{{:<{}}}".format(col_width)
            col_data += col_fmt.format(col_info)
            col_num += 1
    except Exception as e:
        print("col_inf:", col_info)
        print("e:",e)


    return col_data + "\n"


def getReDir(pathStr, headPath):  # 获得除去给定头部路径以后的路径
    if pathStr.startswith(headPath):
        return pathStr.replace(headPath, "")
    else:
        raise MyException("路径：{}中未包含头部目录：{}".format(pathStr, headPath))


def getFolderName(pathStr):  # 返回当前所在的文件夹名称

    sep = "\\"
    if pathStr.find("/") > -1:
        sep = "/"

    listP = pathStr.split(sep)

    if listP[len(listP) - 1] == "":
        return listP[len(listP) - 2]
    else:
        return listP[len(listP) - 1]


def showByWidth(str, width):  # 按指定长度显示字符串，最后三位用...
    d = lenUtf(str) - len(str)  # 处理中文占两个字符
    if lenUtf(str) < width:
        return str
    else:
        return str[0:width - 3 - d] + "..."


@deb
def test(a, b, d=None):
    c = 5
    print(a, b, d)
    return a + b


if __name__ == '__main__':
    ''' 
	test("1", "2")
	print(getMacAdr())
	print(lenUtf("大中肝因aaaa"))
	print(fileInfo("1ss.py"))
# for filename in os.listdir("AlexP2P"):
#	print(fileInfo(filename))
	'''
    print(upFolderPath("c:\\usr\\folder\\seq", "\\"))
