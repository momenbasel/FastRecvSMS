# FastRecvSMS
Python3 wrapper for 5sim.net
During pentesting, receive SMS messages for services requiring phone numbers. 

dependencies:
  <br />requests
  
 python3 -m pip install requests
 
 
 
 Usage:
 
  edit Sms("your_api_key") with your API key from https://5sim.net/settings/security on the object instance
  
  python3 sms.py buy [service]
  <br />
  python3 sms.py buy [service] [country]
  <br />
  python3 sms.py available [service]
  <br />
  python3 sms.py available [service] [country]
  <br />
  python3 sms.py recieve [order_id]
  <br /><br /><br />
  Example:<br />
   python3 sms.py available facebook
   <br />
   python3 sms.py available russia
   <br />
   python3 sms.py buy facebook
   <br />
   python3 sms.py buy facebook russia
   <br />
   python3 sms.py recieve 387141506
   
  
