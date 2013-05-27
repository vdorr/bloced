

import time
from collections import namedtuple
import struct
import binascii

import core
from utils import here


class DebugPort(object) :
	pass


probe_value_t = namedtuple("probe_value", ("value", "timestamp", "rx_timestamp"))


class ProbeData(object) :

	def __init__(self, probe_info) :
		self.info = probe_info
		self.timestamp = None
		self.rx_timestamp = None
		self.value = []


class ProbeType1(DebugPort) :

	def reset(self) :
		self.rx_cnt = 0
		self.probes = {}


	def read(self, n) :
		"""
		returns data going to target
		"""
		return n*"."


	def write(self, data) :
		"""
		accepts data coming from target
		"""

		if self.rx_cnt == 0 :
			self.frame_crc = 0
			self.frame_expected_size = None
			self.current_frame = []

		self.rx_cnt += len(data)

		for c in data :
			if not self.current_frame :
				if ord(c) == 0x10 :
					print here(), "start of frame"
#					self.frame_crc = self.crc8(c)
					self.current_frame.append(c)
				else :
					print here(), "state machine not in sync!"
					continue #first char must be start of frame
			elif len(self.current_frame) == 1 :
#				self.frame_crc = self.crc8(c, crc=self.frame_crc)
				self.frame_expected_size = ord(c)
				self.current_frame.append(c)
				print here(), "expected frame size", self.frame_expected_size
			elif len(self.current_frame) <= self.frame_expected_size :
#				self.frame_crc = self.crc8(c, crc=self.frame_crc)
				self.current_frame.append(c)
			else :
				print here(), "state machine is insane!"
				continue

			if len(self.current_frame) == self.frame_expected_size :
				print here(), binascii.hexlify("".join(self.current_frame)), "len:", len(self.current_frame), "crc:", self.crc8(self.current_frame)

				self.process_probes(self.current_frame[2:-1], time.time())

				self.frame_expected_size = None
				self.current_frame = []

#			if self.frame_crc == 0 :
#				pass

#			self.frame_crc = self.crc8(c, crc=self.frame_crc)



#		if 0 :
#			print here(), binascii.hexlify(data)
#			if len(data) and self.rx_cnt % 256 == 0 :
#				print here(), str(self.rx_cnt) + " bytes received"


	def update_probe_value(self, probe, value, timestamp, rx_timestamp) :
		v = probe_value_t(value, timestamp)
		if len(probe.value) >= self.historic_memory :
			probe.value.pop()
		probe.value.insert(0, v)


	def process_probes(self, blob, rx_timestamp) :

		print here(), [(hex(pbid), pb.info.value_data_type) for pbid, pb in self.probes.items()], binascii.hexlify("".join(blob))

		i = 0
		blob_length = len(blob)
		while i < blob_length :

			probe_id =  ord(blob[blob_length - i - 1])
			i += 1

			try :
				probe = self.probes[probe_id]
			except KeyError :
				print here(), "unknown probe id:", probe_id
				continue
				pass #XXX and now what?

			pb_type = core.KNOWN_TYPES[probe.info.value_data_type]
			print here(), "probe id:", probe_id

#			pb_type.size_in_bytes
#			value = struct.unpack()
#			timestamp = struct.unpack()

##TODO ...
#			self.update_probe_value(probe, value, timestamp, rx_timestamp)
			i += pb_type.size_in_bytes


	def set_probe_list(self, probe_list) :
		"""
		probe_list - probe info returned by implement.implement_workbench
		"""
#		print here(), probe_list
		self.probes = { pb.probe_id : ProbeData(pb) for pb in probe_list }
		print(here(), "got {} probes".format(len(self.probes)))


	def query(self, group, changed_since) :
		"""
		query current value, returns one value per probe
		"""
		pass


	def query_history(self, group, probe, from_date, to_date) :
		"""
		query historic values, returns range of values per probe
		"""
		pass


	def crc8(self, data, crc=0) :
		for c in data :
			crc = ProbeType1.CRC8_TABLE[crc ^ ord(c)]
		return crc


	CRC8_TABLE = [
		0, 94,188,226, 97, 63,221,131,194,156,126, 32,163,253, 31, 65,
		157,195, 33,127,252,162, 64, 30, 95,  1,227,189, 62, 96,130,220,
		35,125,159,193, 66, 28,254,160,225,191, 93,  3,128,222, 60, 98,
		190,224,  2, 92,223,129, 99, 61,124, 34,192,158, 29, 67,161,255,
		70, 24,250,164, 39,121,155,197,132,218, 56,102,229,187, 89,  7,
		219,133,103, 57,186,228,  6, 88, 25, 71,165,251,120, 38,196,154,
		101, 59,217,135,  4, 90,184,230,167,249, 27, 69,198,152,122, 36,
		248,166, 68, 26,153,199, 37,123, 58,100,134,216, 91,  5,231,185,
		140,210, 48,110,237,179, 81, 15, 78, 16,242,172, 47,113,147,205,
		17, 79,173,243,112, 46,204,146,211,141,111, 49,178,236, 14, 80,
		175,241, 19, 77,206,144,114, 44,109, 51,209,143, 12, 82,176,238,
		50,108,142,208, 83, 13,239,177,240,174, 76, 18,145,207, 45,115,
		202,148,118, 40,171,245, 23, 73,  8, 86,180,234,105, 55,213,139,
		87,  9,235,181, 54,104,138,212,149,203, 41,119,244,170, 72, 22,
		233,183, 85, 11,136,214, 52,106, 43,117,151,201, 74, 20,246,168,
		116, 42,200,150, 21, 75,169,247,182,232, 10, 84,215,137,107, 53
	]


	def __init__(self, historic_memory=16) :
#init struct format table (target endiannity)
		self.historic_memory = historic_memory
		self.rx_cnt = 0
		self.probes = {}


def create_probe(probe_type=None) :
	return ProbeType1()


if __name__ == "__main__" :
	pass


