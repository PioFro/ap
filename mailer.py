import yagmail
def sendMail(to, topic, msg):
    file = open("password","r")
    pswd = file.readline()
    file.close()
    yag = yagmail.SMTP(user='autopolicysdn@gmail.com', password=pswd)
    yag.send(to=to,subject=topic,contents=msg)
    print(msg + " to: "+ to)

