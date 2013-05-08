
from utils import here


class DebugPort(object) :

	def reset(self) :
		pass


	def read(self, n) :
		return n*"."


	def write(self, data) :
		self.rx_cnt += len(data)
#		print here(), hexlify(data)
		if len(data) and self.rx_cnt % 30 == 0 :
			print here(), str(self.rx_cnt) + " bytes received"
		pass

	def __init__(self) :
		self.rx_cnt = 0


def create_probe(probe_type=None) :
	return DebugPort()


if __name__ == "__main__" :
	pass


