import requests
import sys
import time
#python3 -m pip install requests

class Sms:
    domain= "5sim.net"

    def __init__(self, api_key):
        self.api_key = api_key
        self.country = "any"
        self.app = "any" 
        self.id = []
        self.session = requests.Session()

        if(len(sys.argv) < 2):
            Sms.usage()
        elif(len(sys.argv) == 2):
            self.action = sys.argv[1]
            print("[+] low on args ...\n")
            print(self.preform(self.action))
            # print(self.avail())
        elif(len(sys.argv) == 3):
            self.action = sys.argv[1]
            self.app = sys.argv[2]
            print(self.preform(self.action))
        
        else:
            self.action= sys.argv[1]
            self.app = sys.argv[2] 
            self.country = sys.argv[3]

            # print(self.avail())
            if(self.getquote() < 2):
                print("Not enough credits \n")
                sys.exit(1)
            else: 
                if(self.preform(self.action)):
                    print("Success \n")
                else:
                    print("Failed \n")
                    sys.exit(1)
                
            
            
        
        
        

    def usage(): 
        print("Usage: python3 sms.py <action[available, buy, recieve] <app> <country>") #for others write others
        sys.exit(1)
    
    def getquote(self):
        url = f"https://{Sms.domain}/v1/user/profile"
        headers = {'Authorization': f'Bearer {self.api_key}', 'Accept': 'application/json'}
        response = self.session.get(url, headers=headers)
        return response.json().get('balance')
    
    def avail(self):
        country = str(self.country)
        app = self.app
        url = f"https://{Sms.domain}/v1/guest/products/{country}/any"
        headers = {'Accept': 'application/json'}
        response = self.session.get(url, headers=headers)
        
        if(app == 'any'):
            print(response.json())
            return True
        resp =response.json().get(app.lower())
        if(resp == None):
            print('Invalid App Name')
            return False
        print(f"{app} activation exists with price ~{resp['Price']} and you have {self.getquote()} credits")
        return True
        


    def purchase(self, service="activation", operator="any"):
        country = str(self.country)
        app = str(self.app)
        reuse = input("Reuse number? (y/n): ")
        if(reuse == 'y'):
            reuse = True
        else:
            reuse = False
        if(reuse):
            url = f"https://{Sms.domain}/v1/user/buy/{service}/{country}/{operator}/{app}?reuse=1"

        url = f"https://{Sms.domain}/v1/user/buy/{service}/{country}/{operator}/{app}"
        print(url)
        headers = {'Authorization': f'Bearer {self.api_key}', 'Accept': 'application/json'}
        print("[+] Buying activation number ...")
        response = self.session.get(url, headers=headers)
        if(response.status_code == 200):
            if response.text == "no free phones":
                print("No free phones")
                return False
            resp = response.json()
            self.id.append(resp.get('id'))
            print(f"[+] Purchased with ID  {self.id[0]}")
            print(f"\n number: {resp.get('phone')} \t  country: {resp.get('country')} \t costs {resp.get('price')}")

            return True
        return False
    

    def recv(self):
        if(self.app.isnumeric()):
            ioID= int(self.app)
            self.id.append(ioID)
        url = f"https://{Sms.domain}/v1/user/check/{self.id[0]}"
        headers = {'Authorization': f'Bearer {self.api_key}', 'Accept': 'application/json'}
        response = self.session.get(url, headers=headers)
        #print(response.status_code)
        if(response.status_code == 200):
            resp = response.json()
            if(resp.get('status') == 'CANCELED' or resp.get('status') == 'BANNED' or resp.get('status') == 'TIMEOUT'):
                print("Canceled or Banned or Timeout ..")
                print("Try again...")
                print("Exiting ...")
                sys.exit(1)
            if(resp.get('status') == 'PENDING'):
                print("Waiting for SMS")
                print("to cancel press ctrl+c")
            if(resp.get('status') == 'RECEIVED'):
                print(f"Got an SMS: {resp.get('sms')} \n\n")
                print(f"code is: {resp.get('sms')['code']}")
                return True
        else:
            print("Unknown status code")
            sys.exit(1)
        return False
       
    
    def preform(self, action):
        if(action == "available"):
            return self.avail()
        
        elif(action == "buy"):
            if(self.purchase()):
                print("[+] waiting for SMS ...")
                return self.recv()
            return False
        elif(action == "recieve"):

            while self.recv() == False:
                time.sleep(10)
                self.recv()
            return True
        else:
            print("Invalid action")
            Sms.usage()
            sys.exit(1)
    




def getBanner():
    print('''
8888888888             888   8888888b.                          .d8888b. 888b     d888 .d8888b.  
888                    888   888   Y88b                        d88P  Y88b8888b   d8888d88P  Y88b 
888                    888   888    888                        Y88b.     88888b.d88888Y88b.      
8888888 8888b. .d8888b 888888888   d88P .d88b.  .d8888b888  888 "Y888b.  888Y88888P888 "Y888b.   
888        "88b88K     888   8888888P" d8P  Y8bd88P"   888  888    "Y88b.888 Y888P 888    "Y88b. 
888    .d888888"Y8888b.888   888 T88b  88888888888     Y88  88P      "888888  Y8P  888      "888 
888    888  888     X88Y88b. 888  T88b Y8b.    Y88b.    Y8bd8P Y88b  d88P888   "   888Y88b  d88P 
888    "Y888888 88888P' "Y888888   T88b "Y8888  "Y8888P  Y88P   "Y8888P" 888       888 "Y8888P"  
                                                                                                 
                                                                                                 
                                                                                                 
                                                                         
    ''')

getBanner()


#enter your api key here
#you can get it from https://5sim.net/settings/security
cc = Sms("your_api_key")