class Entry:
	def __init__(self, value, db):
		super(type(self)).__init__(self)
		self.value = value
		self.db = db
	
	def __hash__(self):
		return hash(self.value)

class Bool(Entry): pass

class Number(Entry): pass

class String(Entry): pass

class Datetime(Entry): pass

class Executable(Entry): pass

class Object(Entry):
	def __hash__(self):
		return hash(tuple(self.value.items()))
	
	def get(self, x):
		return self.value[x]

class Array(Entry):
	def __hash__(self):
		return hash(tuple(self.value))
	
	def get(self, x):
		return self.value[x]

class Ref(Entry):
	def get(self, x):
		return self.db.get(self.value).get(x)

