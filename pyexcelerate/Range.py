from . import DataTypes

class Range(object):
	A = ord('A')
	Z = ord('Z')
	def __init__(self, start, end, worksheet):
		self._start = Range.to_coordinate(start)
		self._end = Range.to_coordinate(end)
		self._parent = worksheet
		if self.is_cell():
			# Report the column as active so the worksheet knows
			self.worksheet.report_column(self.y)
	
	@property
	def width(self):
		return self._end[0] - self._start[0] + 1
	
	@property
	def height(self):
		return self._end[1] - self._start[1] + 1

	@property
	def x(self):
		if self.is_row():
			return self._start[0]
		else:
			return self.coordinate[0]
	
	@property
	def y(self):
		if self.is_column():
			return self._start[1]
		else:
			return self.coordinate[1]
	
	@property
	def coordinate(self):
		if self.is_cell():
			return self._start
		else:
			raise Exception("Non-singleton range selected")
	
	@property
	def value(self):
		if self.is_cell():
			for merge in self.worksheet.merges:
				if self in merge:
					return self.worksheet.get_cell_value(merge._start[0], merge._start[1])
			return self.worksheet.get_cell_value(self.x, self.y)
		else:
			raise Exception("Not a cell")

	@value.setter
	def value(self, data):
		if self.is_cell():
			for merge in self.worksheet.merges:
				if self in merge:
					self.worksheet.set_cell_value(merge._start[0], merge._start[1], data)
					return
			self.worksheet.set_cell_value(self.x, self.y, data)
		else:
			if len(data) <= self.height:
				for row in data:
					if len(data) > self.width:
						raise Exception("Row too large for range")
				for x, row in enumerate(data):
					for y, value in enumerate(row):
						self.worksheet.set_cell_value(x + self._start[0], y + self._start[1], value)
			else:
				raise Exception("Too many rows for range")

	@property
	def worksheet(self):
		return self._parent
	
	def is_cell(self):
		return self._start == self._end

	def is_row(self):
		return self._start[0] == self._end[0] \
			and self._start[1] == 1 \
			and self._end[1] == float('inf')

	def is_column(self):
		return self._start[1] == self._end[1] \
			and self._start[0] == 1 \
			and self._end[1] == float('inf') \
	
	def intersection(self, range):
		"""
		Calculates the intersection with another range object
		"""
		if self.worksheet != range.worksheet:
			# Different worksheet
			return None
		start = (max(self._start[0], range._start[0]), max(self._start[1], range._start[1]))
		end = (min(self._end[0], range._end[0]), min(self._end[1], range._end[1]))
		return Range(start, end, self.worksheet)
		
	def intersects(self, range):
		return intersection(range) == None
	
	def merge(self):
		self.worksheet.add_merge(self)

	def __contains__(self, item):
		return self.intersection(item) == item

	def __hash__(self):
		def hash(val):
			return val[0] << 8 + val[1]
		return hash(self._start) << 24 + hash(self._end)

	def __str__(self):
		return Range.coordinate_to_string(self._start) + ":" + Range.coordinate_to_string(self._end)

	def __len__(self):
		if self._start[0] == self._end[0]:
			return self.width
		else:
			return self.height

	def __eq__(self, other):
		return self._start == other._start and self._end == other._end
	
	def __ne__(self, other):
		return not (self == other)
	
	def __getitem__(self, key):
		if self.is_row():
			# return the key'th column
			newStart = (self.x, key)
			newEnd = (self.x, key)
			return Range(newStart, newEnd, self.worksheet)
		elif self.is_column():
			#return the key'th row
			newStart = (key, self.y)
			newEnd = (key, self.y)
			return Range(newStart, newEnd, self.worksheet)			
		else:
			raise Exception("Selection not valid")
	
	def __setitem__(self, key, value):
		if self.is_row():
			self.worksheet.set_cell_value(self.x, key, value)
		else:
			raise Exception("Couldn't set that")
	
	@staticmethod
	def string_to_coordinate(s):
		# Convert a base-26 name to integer
		y = 0
		for i in range(len(s)):
			if ord(s[i]) < Range.A or ord(s[i]) > Range.Z:
				s = s[i:]
				break
			y *= 26
			y += ord(s[i]) - Range.A + 1
		return (int(s), y)

	_cts_cache = {}
	@staticmethod
	def coordinate_to_string(coord):
		# convert an integer to base-26 name
		y = coord[1] - 1
		if y not in Range._cts_cache:
			s = ""	
			while y >= 0:
				s = chr((y % 26) + Range.A) + s
				y /= 26
				y -= 1
			Range._cts_cache[y] = s
		return Range._cts_cache[y] + str(coord[0])
	
	@staticmethod
	def to_coordinate(value):
		if isinstance(value, basestring):
			value = Range.string_to_coordinate(value)
		if (value[0] < 1 or value[0] > 65536) and value[1] != float('inf'):
			raise Exception("Row index out of bounds")
		if (value[1] < 1 or value[1] > 256) and value[1] != float('inf'):
			raise Exception("Column index out of bounds")
		return value
