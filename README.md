# FastRecvSMS
Python3 wrapper for 5sim.net
During pentesting, receive SMS messages for services requiring phone numbers. 

dependencies:
  requests
  
  
 python3 -m pip install requests
 
 
 
 Usage:
 
  edit Sms("your_api_key") with your API key from https://5sim.net/settings/security on the object instance
  
  python3 sms.py buy [service]
  python3 sms.py buy [service] [country]
  python3 sms.py available [service]
  python3 sms.py available [service] [country]
  python3 sms.py recieve [order_id]
  
  Example:
   python3 sms.py available facebook
   python3 sms.py available russia
   python3 sms.py buy facebook
   python3 sms.py buy facebook russia
   python3 sms.py recieve 387141506
   
  
