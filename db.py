import database_protobuf as dbf

class File:
	def __init__(self, path):
		self.path = path

class Exec:
	def __init__(self, code):
		self.code = code

def boxvalue(v):
	any = dbf.Any()
	
	if v is None:
		any.null = dbf.Void()
	if type(v) is bool:
		any.bool = dbf.true if v else dbf.false
	elif type(v) is int:
		any.int = v
	elif type(v) is float:
		any.real = v
	elif type(v) is str:
		any.str = v
	elif type(v) is bytes:
		any.blob = v
	elif type(v) is list:
		arr = dbf.Array()
		
		for a in v:
			arr.add(boxvalue(a))
		
		any.array = arr
	elif type(v) is set:
		arr = dbf.Array()
		
		for a in v:
			arr.add(boxvalue(a))
		
		any.set = arr
	elif type(v) is dict:
		obj = dbf.Object()
		
		for k, d in v:
			obj[str(k)] = boxvalue(d)
		
		any.object = obj
	elif type(v) is Link:
		ref = dbf.Ref()
		ref.to = '/' + '/'.join(v.path)
		
		any.ref = ref
	elif type(v) is File:
		f = dbf.File()
		f.path = v.path
		
		any.file = f
	elif type(v) is Exec:
		e = dbf.Exec()
		e.code = v.code
		
		any.exec = e
	else:
		any.null = dbf.Void()
	
	return any

class Entry:
	def __init__(self, db, data):
		self.db = db
		self.data = data
	
	# Doesn't work for now
	def refs(self):
		def entry_visit(pre, x):
			d = x.WhichOneOf('data')
	
			if type(x) is dbf.Array or type(x) is dbf.Set:
				it = enumerate(d.data)
			elif type(x) is dbf.Object:
				it = d.items()
			elif type(x) is dbf.Ref:
				yield pre
				return
	
			for k, v in it:
				# Unpack the any value
				v = getattr(v, v.WhichOneof('data'))
				#yield from
				for z in entry_visit("{}/{}".format(pre, k), v):
					yield z
		
		# Iterate over the databaes
		for k, v in self.db.items():
			for r in entry_visit('/' + k, v):
				yield r
	
	def __getitem__(self, key):
		if key not in self.data:
			return None
		
		val = self.data[key]
		
		if type(val) is dbf.Ref:
			return db[val.to]
		else:
			return Entry(db, val)
	
	def __setitem__(self, key, val):
		self.data[key] = boxvalue(val)

class Database:
	def __init__(self, fp):
		self.data = dbf.Object()
		if fp:
			self.data.ParseFromString(fp.read())
	
	def commit(self, fp):
		fp.write(self.data.SerializeToString())
	
	def __getitem__(self, key):
		if key not in self.data:
			return None
		return Entry(self.data[key])
	
	def __setitem__(self, key, val):
		self.data[key] = boxvalue(val)

class BadLinkError(RuntimeError): pass

class Link:
	def __init__(self, path):
		v = []
		while path and path != "/":
			path, tail = os.path.split(path)
			
			v.append(tail)
		
		if len(v[-1]) == 0:
			v.pop()
		
		v.reverse()
		self.path = v
		# Is this necessary?
		self.relative = (head == "")
	
	def resolve(self, db):
		cur = db
		for x, p in enumerate(self.path):
			cur = cur[p]
			
			if cur is None:
				raise BadLinkError(
					"Link {} does not exist".format(self.path[:x])
				)
		
		return cur
	
	def touch(self, db):
		cur = db
		for x, p in enumerate(self.path):
			next = cur[p]
			
			if next is None:
				cur[p] = dbf.Object()
			
			cur = next
		
		return cur
	
	def remove(self, db):
		cur = db
		for x, p in enumerate(self.path[:-1]):
			cur = cur[p]
			
			if cur is None:
				raise BadLinkError(
					"Link {} does not exist".format(self.path[:x])
				)
		
		del cur[self.path[-1]]


