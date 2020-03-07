
import time
import uuid

def deb(fn):#用于调试的装饰器函数
	def debugPrint(*args,**kwargs):
		print("function name:",fn.__name__,", start debug:",nowStr(),10*">")
		print("inner vars:",fn.__code__.co_varnames)

		#print(objInfo(fn.__code__))
		print("args:",*args)
		print("kwargs:",**kwargs)
		#print(locals())
		print("start execute ",10*'>')
		o = fn(*args,**kwargs)
		print("end execute ",nowStr(),10*'<')
		print("function return:",o)
	return debugPrint


def nowStr(fmt="%Y%m%d %H:%M:%S"):
	return time.strftime(fmt, time.localtime())


def objInfo(obj):
	print("object Info:",10*'>')
	print(dir(obj))
	print(type(obj))

def getMacAdr():
	mac=uuid.UUID(int = uuid.getnode()).hex[-12:] 
	return "".join([mac[e:e+2] for e in range(0,11,2)])


@deb
def test(a,b,d=None):
	c=5
	print(a,b,d)
	return a+b

if __name__ == '__main__':

	test("1","2")
	print(getMacAdr())

