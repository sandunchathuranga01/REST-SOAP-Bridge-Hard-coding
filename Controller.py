Soap_url = "http://127.0.0.1:8000"
Headers = {'Content-Type': 'text/xml;charset=UTF-8'}
Attrib = {'xmlns:soapenv': 'http://schemas.xmlsoap.org/soap/envelope/', 'xmlns:ns': 'soap_app.ItemService'}
WSDL = ""


#BRIDGE CALLING API
# API :- <loopback address>:<port number>/<REST API>

REST_API= '/convert-rest-to-soap'
METHOD = 'POST'