import time
import uuid
import os.path as path
import os


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





def fileInfo(filename, dirname=""):
	info = {}
	info["name"] = filename
	info["path"] = path.join(dirname, filename)
	info["exists"] = path.exists(info["name"])

	if info["exists"]:
		info["isdir"] = path.isdir(info["name"])
		info["ext"] = path.splitext(info["name"])[1]
		if info["isdir"] or info["ext"] == '':
			info["ext"] = "目录"
		#else:
		#	info["ext"] = path.splitext(info["path"])[1]

		info["size"] = str(path.getsize(info["name"]) / 1000) + "Kb"
		info["mtime"] = timeStr(path.getmtime(info["name"]))
		info["ctime"] = timeStr(path.getctime(info["name"]))
		info["state"] = "状态比较"

		return info
	else:
		return None

def rowTitle(titleDef):
	''' 显示文件列表标题 titleDef为列表，元素为元组(中文名，两边宽度，变量名) '''

	col_len_l = []
	col_len = 0
	title_len = 0
	title = ""
	for col in titleDef:
		title_len = lenUtf(title)
		title += col[0] + " " * (col[1]*2)
		col_len = lenUtf(title) - title_len
		col_len_l.append(col_len)
	return title + "\n", col_len_l

def rowShow(titleDef, col_len_l, info):
	""" 显示文件列表的每行内容 元素为元组(中文名，两边宽度，变量名) """
	if not info: return "未取到数据" + "\n"
	col_num = 0
	col_data = ""

	for col in titleDef:
		col_width = col_len_l[col_num]
		col_info = info[col[2]]
		col_width -= lenUtf(col_info) - len(col_info)

		col_fmt = "{{:<{}}}".format(col_width)
		col_data += col_fmt.format(col_info)
		col_num += 1

	return col_data + "\n"


@deb
def test(a, b, d=None):
	c = 5
	print(a, b, d)
	return a + b


if __name__ == '__main__':
	test("1", "2")
	print(getMacAdr())
	print(lenUtf("大中肝因aaaa"))
	print(fileInfo("1ss.py"))
# for filename in os.listdir("AlexP2P"):
#	print(fileInfo(filename))
