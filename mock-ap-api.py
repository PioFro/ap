from flask import Flask

app = Flask(__name__)
@app.route("/autopolicy/<id>/")
def delete(id):
    print("Got the ap-requests for the subject "+id)
    if "of" in id and not "-" in id:
        return '''
        {
                "properties":
                        [
                          {
                            "subject": "DEVICE",
                            "name": "GEOLOCATION",
                            "value": "USA"
                          },
                          {
                            "subject": "DEVICE",
                            "name":"Current bytes per second",
                            "value": 100000
                          },
                          {
                            "subject": "DEVICE",
                            "name":"GEOLOCATION 2",
                            "value": "NOT_EU"
                          }
                        ]
        }
                  '''
    elif str(id).count(":")>1 and not "-" in id:
        return '''
        {
        "criteria manager":
                            [
                              {
                                "subject": "DEVICE",
                                "name": "GEOLOCATION",
                                "value": "USA"
                              },
                              {
                                "subject": "LINK",
                                "name":"CapacityMB",
                                "value": ">100"
                              },
                              {
                                "subject": "LINK",
                                "name":"Wireless",
                                "value": "NOT_wireless"
                              },
                              {
                                "subject": "DEVICE",
                                "name":"Software Version",
                                "value": ">230"
                              }
                            ],
        "autopolicy profile":
                {
                    "from device": 	
                                {
                                    "allow":["dst 10.0.1.1/24 tcp 80,443,8888 0.5", 
                                   "dst 10.0.1.2/24 udp 5015 0.1","dst 10.0.1.123/24 udp 5015 0.1","dst 8.8.8.8/24 tcp 55 100"]
                                    }
                },
        "autopolicy identity":
                {
                    "manufacturer": "ACME",
                    "device": "WRT-54GL",
                    "revision": "1_1"
                }
        }
        '''
    elif "-" in id:
        return '''
        {
                    "properties":
                            [
                              {
                                "subject": "LINK",
                                "name": "GEOLOCATION",
                                "value": "USA"
                              },
                              {
                                "subject": "LINK",
                                "name":"CapacityMB",
                                "value": 350
                              }
                            ]
        }
        
        '''

if __name__ == '__main__':
    app.run(host="0.0.0.0",port="4444")