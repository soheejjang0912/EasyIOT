from flask import Flask, render_template, request, url_for
from urllib.request import urlopen, Request
from picamera import PiCamera
import bs4          #네이버 날씨, 실제 데이터 가져오기위함 url파싱
import urllib       #네이버 날씨,실제 데이터 가져오기위함 bs4사용
import time
import RPi.GPIO as GPIO 

app = Flask(__name__)
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)  

#도어락(모터)핀 번호 선언하기 & 초기화 
GPIO.setup(18, GPIO.OUT)
svoFreq = GPIO.PWM(18, 50)
svoFreq.start(0)

#조명(LED)사용 핀 번호 선언하기 & 초기화
#ROOM1 = 23 ROOM2 = 24 ROOM3 = 25 
#GPIO.setup(ROOM1, GPIO.OUT, initial = GPIO.LOW)
#위 처럼 선언도 가능하지만 아래처럼 한번에 하는것도 가능함
pins={
    23:{'name':'거실', 'state':GPIO.LOW},
    24:{'name':'안방', 'state':GPIO.LOW},
    25:{'name':'작은방', 'state':GPIO.LOW}
}  

for pin in pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)
      
@app.route("/")
def home():  
    return render_template("index.html")
 
#조명 끄고 켜기
@app.route("/lightState.html")
def lightmain():
    for pin in pins:
        pins[pin]['state']=GPIO.input(pin)  
       #pins[0]['state']
       #GPIO.input(pin)->GPIO.HIGH가 출력되는지, GPIO.LOW가 출력되는지 알아보는 용도
    templateData = {
        'pins':pins 
    } 
    return render_template('lightState.html',**templateData)


@app.route("/lightState.html/<changePin>/<action>") #<>다이나믹 라운딩 선택적으로
def lightaction(changePin, action):
    changePin = int(changePin)
    deviceName = pins[changePin]['name']

    if action == "on":
        GPIO.output(changePin, GPIO.HIGH)
    if action == "off":
        GPIO.output(changePin, GPIO.LOW)

    pins[changePin]['state'] = GPIO.input(changePin)
    
    templateData = {'pins':pins}
    return render_template('lightState.html', **templateData)


 
#문
@app.route("/doorState.html")
def doormain(): 
    return render_template('doorState.html')

@app.route("/doorState.html/<action>") #<>다이나믹 라운딩 선택적으로
def dooraction(action):

    if action == "on":
        svoFreq.ChangeDutyCycle(2.5)
        time.sleep(2)
        svoFreq.stop()  

    if action == "off":
        svoFreq.ChangeDutyCycle(9.5) 
        time.sleep(2)
        svoFreq.stop()  
 
    return render_template('doorState.html')

#날씨
@app.route("/weatherState.html")
def weathermain():  
    location = '가산동'
    enc_location = urllib.parse.quote(location + '+날씨') 
    url = 'https://search.naver.com/search.naver?ie=utf8&query='+ enc_location
    
    req = Request(url)
    page = urlopen(req)
    html = page.read()
    soup = bs4.BeautifulSoup(html,'html5lib') 
    templateData = soup.find('p', class_='info_temperature').find('span', class_='todaytemp').text
    castData = soup.find('p', class_='cast_txt').text
    weatherInformation=[templateData,castData]
    return render_template('weatherState.html',data = weatherInformation)
 
@app.route("/gpio/cleanup")
def gpio_cleanup():
    GPIO_cleanup()
    return "GPIO CLEANUP"


if __name__ == "__main__":
    app.run(host="192.168.137.84")
