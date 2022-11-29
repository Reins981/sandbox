import httplib, os, socket
from QA_Logger import QA_Logger

class QA_HTTP(QA_Logger):
	"""nice tools to automate http tests"""
	
	"""my global wars - just to know they are there ;) """
	proxy_ip=None		#proxy ip
	proxy_port=None		#proxy port
	conn=None			#current connection
	response=None		#last response



	def __init__(self,proxy_ip="10.0.66.252",proxy_port=3128,do_connect=True,useSSL=False,
									name='QA_HTTP',
									loglevel=None,
									logline_format=None,
									logfile=None,
									logfile_level=None,
									print_stats_on_exit=False,
				):
		super(self.__class__,self).__init__(name=name,
									loglevel=loglevel,
									logline_format=logline_format,
									logfile=logfile,
									logfile_level=logfile_level,
									print_stats_on_exit=print_stats_on_exit,
									)
		
		#logger from superclass
		self.log(1000,"entering init")
		self.log(3,"AUDIT Proxy %s:%i"%(proxy_ip,proxy_port))
					#reset lognumber
		self.proxy_ip=proxy_ip
		self.proxy_port=proxy_port
		
		if do_connect: self.connect(useSSL=useSSL)	#auto connect
		return
	
	def __del__(self):
		super(self.__class__,self).__del__()

		
	
	'''proxy stuff'''	
	def set_proxy(self,ip,port):
		self.log(1000,"entering set_proxy")
		self.proxy_ip=ip
		self.proxy_port=port
		self.log("proxy: %s:%s"(self.proxy_ip,self.proxy_port))
		return
	
	def get_proxy(self):
		return ("%s:%s"%(self.proxy_ip,self.proxy_port))
	
	'''connection / state stuff '''
	def is_connected(self):
		self.log(1000,"entering is_connected")
		if self.conn==None:
			self.log(10,"is_connected: FALSE")
			return False
		else:
			self.log(10,"is_connected: TRUE")
			return True
	
	def connect(self,useSSL=False):
		self.log(1000,"entering connect")
		self.log(3,"AUDIT Proxy %s:%i"%(self.proxy_ip,self.proxy_port))
		if not self.is_connected():
			if useSSL==True:
				if socket.ssl: self.log("SSL present: %s"%socket.ssl)
				self.log(5,"SSL on")
				self.conn = httplib.HTTPSConnection(self.proxy_ip, self.proxy_port)
			else:
				self.log(5,"SSL off")
				self.conn = httplib.HTTPConnection(self.proxy_ip, self.proxy_port)
			self.log(10,"connect: new: %s"%(self.conn))
			return self.conn
		return False
		


	
	''' request stuff '''
	def doRequest(self,method,url,header={},params=None,followRedirect=False):
		self.log(1000,"entering doRequest")
		if self.is_connected():
			self.log(15,"doRequest: %s %s"%(method,url))
			self.conn.request(method, url,params,header)
			self.log(15,"get response: ")
			self.response = self.conn.getresponse()
			#self.response = self.handleResponseStatus(self.response,method,url,header,params) 
			return self.response
		return False
		
	def doGet(self,url):
		self.log(1000,"entering doGet")
		if self.is_connected():
			return self.doRequest("GET",url)
		return False
	
	def doPost(self,url):
		self.log(1000,"entering doPost")
		if self.is_connected():
			return self.doRequest("POST",url)
		return False
		
	''' all in one requests .. request+response'''
	def executeRequest(self,method,url,header={},params=None,checkResponseBody=None,testcase_title=None,testcase_number_autoincrement=True,checkResponseReason=None,checkResponseStatus=None,checkResponseMessage=None,followRedirect=False):
		self.log(1000,"entering executeRequest")
		self.doRequest(method,url,header,params,followRedirect)
		
		
		r_data =self.getResponse()
		r_msg = self.getResponseMessage()
		r_reason = self.getResponseReason()
		r_status = str(self.getResponseStatus())
		
		if testcase_title==None: testcase_title=" "
		if testcase_number_autoincrement==True: testcase_title="%s) %s"%(self.testcase_number,testcase_title)
		self.testcase_number=self.testcase_number+1
		
		self.log(5,"%s: URL=%s %s  ==> ResponseStatus=%s"%(testcase_title,method,url,self.getResponseStatus()))
		
		#just return data
		if checkResponseBody==None and checkResponseStatus==None and checkResponseMessage==None and checkResponseReason==None:
			self.log(3,"%s: checkResponseBody=%s [%s]"%(testcase_title,checkResponseBody,"DATA"))
			return r_data 
		
		##---- check response! ----				
		#check_ResponseReason
		if self.checkResponseAND(r_data,checkResponseBody,testcase_title)==False: return False		
		#check_ResponseReason
		if self.checkResponseAND(r_msg,checkResponseMessage,testcase_title)==False: return False			
		#check_ResponseReason
		if self.checkResponseAND(r_reason,checkResponseReason,testcase_title)==False: return False	
		#check_ResponseStatus
		if self.checkResponseAND(r_status,checkResponseStatus,testcase_title)==False: return False
		
		return True
				
		
			
		

		
	
	def executeGet(self,url,header={},params=None,checkResponseBody=None,testcase_title=None,testcase_number_autoincrement=True,checkResponseReason=None,checkResponseStatus=None,checkResponseMessage=None,followRedirect=False):
		self.log(1000,"entering executeGet")
		return self.executeRequest("GET", url,
								header=header,
								params=params,
								checkResponseBody=checkResponseBody,
								testcase_title=testcase_title,
								testcase_number_autoincrement=testcase_number_autoincrement,
								checkResponseReason=checkResponseReason,
								checkResponseStatus=checkResponseStatus,
								checkResponseMessage=checkResponseMessage,
								followRedirect=followRedirect
								);

	def executePOST(self,url,header={},params=None,checkResponseBody=None,testcase_title=None,testcase_number_autoincrement=True,checkResponseReason=None,checkResponseStatus=None,checkResponseMessage=None,followRedirect=False):
		self.log(1000,"entering executePost")
		return self.executeRequest("POST", url,
								header=header,
								params=params,
								checkResponseBody=checkResponseBody,
								testcase_title=testcase_title,
								testcase_number_autoincrement=testcase_number_autoincrement,
								checkResponseReason=checkResponseReason,
								checkResponseStatus=checkResponseStatus,
								checkResponseMessage=checkResponseMessage,
								followRedirect=followRedirect
								);

	''' Response handling '''	
	def getResponse(self):
		self.log(1000,"entering getResponse")
		if self.is_connected():
			self.log(15,"getResponse: Status= %s"%(self.getResponseStatus()))
			self.log(10,"getResponse: Message= %s"%(self.getResponseMessage()))
			self.log(15,"getResponse: Reason=%s"%(self.getResponseReason()))
			
			data_all=""
			'''
			while 1:
				data = self.response.read(16)
				data_all=("%s%s")%(data_all,data)
				if len(data) < 16: break
			'''
			data_all=self.response.read()
			self.log(8,"getResponse: DATA_LEN=%s"%(len(data_all)))
			self.log(10000,"getResponse: DATA=[len=%s]\n%s"%(len(data_all),data_all))
			return data_all
		return False
	
	'''response handling'''
	def getResponseStatus(self):
		self.log(1000,"entering getResponseStatus")
		if self.is_connected():
			return self.response.status#
		return False
			
	def getResponseMessage(self):
		self.log(1000,"entering getResponseMessage")
		if self.is_connected():
			return self.response.msg#
		return False
	
	def getResponseReason(self):
		self.log(1000,"entering getResponseReason")
		if self.is_connected():
			return self.response.reason
		return False
	
	
	'''example testrun'''
	def selftest(self):
		self.log(1000,"entering selftest")
		self.log(self.is_connected())
		self.log( self.connect())
		self.log( self.doGet("http://www.python.org/index.html"))
		self.log( self.getResponse())
		
		
		
	def upload_encode (self,file_path,header_filename=None, header_content_type="text/plain", fields=[]):
		BOUNDARY = '----------bundary------'
		CRLF = '\r\n'
		body = []
		# Add the metadata about the upload first
		for key, value in fields:
			body.extend(
		  ['--' + BOUNDARY,
		   'Content-Disposition: form-data; name="%s"' % key,
		   '',
		   value,
		   ])
		# Now add the file itself
		if header_filename==None: header_filename = os.path.basename(file_path)
		f = open(file_path, 'rb')
		file_content = f.read()
		f.close()
		body.extend(
		  ['--' + BOUNDARY,
		   'Content-Disposition: form-data; name="file"; filename="%s"'
		   % header_filename,
		   # The upload server determines the mime-type, no need to set it.
		   'Content-Type: %s'%header_content_type,
		   '',
		   file_content,
		   ])
		# Finalize the form body
		body.extend(['--' + BOUNDARY + '--', ''])
		return 'multipart/form-data; boundary=%s' % BOUNDARY, CRLF.join(body)


	def executeUpload(self,url,file_path,header_filename=None,header_content_type=None,checkResponseBody=False,testcase_title=None,testcase_number_autoincrement=True):	
		self.log(1000,"doUpload")
		if os.path.exists(file_path):
			content_type, body = self.upload_encode(file_path,header_filename,header_content_type)
			header = { 'Content-Type': content_type }
			#u = urlparse.urlparse(url)
			self.log(20,"headers: %s"%(header))
			self.log(20,"body: %s"%(body))
			return self.executeRequest("PUT",url,header,body,checkResponseBody,testcase_title,testcase_number_autoincrement=testcase_number_autoincrement)
		else:
			self.log(4,"doUpload - File not found! (%s)"%file_path)
		self.log("[%s] %s"%("FAIL",testcase_title))
		self.numFailed=self.numFailed+1
		return None

	
	def handleResponseStatus(self,response,method,url,header={},params=None):
		if response.status==302:		##redirect
			'''
			message = str(response.msg)
			start=message.find("Location: ")+10
			end=message.find(" ",start)
			message=message[start:end]
			return self.doRequest(method, message, header, params)
			'''
			pass
		return response
	
