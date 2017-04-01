#!/usr/bin/env python
# -*- coding: utf-8 -*-
import RPi.GPIO as GPIO
from time import sleep
import wiringpi
import subprocess
from time import sleep
import signal
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

from email.Header import Header 
from email.Utils import formatdate
import smtplib
picnum =1   #保存する写真する名前の数字の初期値
js = ['test1.jpg']
pwm_out_pin = 18

GPIO.setmode(GPIO.BCM)
sclk = 11
miso = 9
mosi = 10
ce0 = 8

GPIO.setup(sclk, GPIO.OUT)
GPIO.setup(miso, GPIO.IN)
GPIO.setup(mosi, GPIO.OUT)
GPIO.setup(ce0, GPIO.OUT)
GPIO.setup(14, GPIO.OUT)

def read(adcnum, sclk, mosi, miso, ce0): #cdsによって光を検出する関数を定義
      
    if adcnum > 7 or adcnum < 0:
        return -1
  
    GPIO.output(ce0, GPIO.HIGH)
    GPIO.output(sclk, GPIO.LOW)
    GPIO.output(ce0, GPIO.LOW)
  
    commandout = adcnum
    commandout |= 0x18
    commandout <<= 3
  
    for i in range(5):
        if commandout & 0x80:
            GPIO.output(mosi, GPIO.HIGH)
        else:
            GPIO.output(mosi, GPIO.LOW)
        commandout <<= 1
  
        GPIO.output(sclk, GPIO.HIGH)
        GPIO.output(sclk, GPIO.LOW)
    adcout = 0
  
    for i in range(13):
        GPIO.output(sclk, GPIO.HIGH)
        GPIO.output(sclk, GPIO.LOW)
        adcout <<= 1
        if i>0 and GPIO.input(miso) == GPIO.HIGH:
            adcout |= 0x1
    GPIO.output(ce0, GPIO.HIGH)
    return adcout


def take_a_picture(count): # 写真を撮影する関数を定義
    confirm = "locate test1.jpg"
    updatedb = "sudo updatedb"
    delete = "rm test1.jpg"
    dropbox = "sudo dropbox_uploader.sh upload /home/pi/test1.jpg test1.jpg"
    camera = "fswebcam -F 100 --no-timestamp --no-banner /home/pi/test1.jpg"
    led = 12;  #ピン番号
    GPIO.setup(led, GPIO.OUT)
    confirm = confirm.replace('test1','test'+str(count)) #保存する写真する名前の数字を変更
    delete = delete.replace('test1','test'+str(count)) #保存する写真する名前の数字を変更
    dropbox = dropbox.replace('test1','test'+str(count)) #保存する写真する名前の数字を変更
    camera = camera.replace('test1','test'+str(count)) #保存する写真する名前の数字を変更

    while True:
        print('check to exist a picture_data')
        ret  =  subprocess.call(confirm,shell = True)
        if ret == 0: #cmdの結果はcatコマンドで画像があれば0を返し、なければ1を返す
            print ret == 0   #File is existed
            print('picture_data is existed.Delete!')
            subprocess.call(delete,shell = True) #file delete
            break
        else:
            #print "non file" #File is not existed
            break
    while True:
        print('Take a picture')
        GPIO.output(led, GPIO.HIGH)
        subprocess.call(camera,shell = True)
        subprocess.call(updatedb,shell = True)
        GPIO.output(led, GPIO.LOW)
        print('check to exist a picture_data_2nd')
        ret  =  subprocess.call(confirm,shell = True)

        if ret == 0: #cmdの結果はcatコマンドで画像があれば0を返し、なければ1を返す
            print ret == 0   #File is existed
            print('picture_data is existed.Upload!')
        else:
            print "we can't take a picture" #File is not existed
            print('one more take a picture')
            print('Waitig for 10 sec ')
            #GPIO.output(4, GPIO.HIGH)
            #time.sleep(10)
            #GPIO.output(4, GPIO.LOW)
            time.sleep(10)
            continue
        #subprocess.call(dropbox,shell = True) # upload
        #print "dropbox upload success"
        #print 'count=' + str(count)
        break
    return count
         

def send_email_with_jpeg(from_addr, to_addr, subject, body, jpegs=[], server='smtp.gmail.com', port=587):
    encoding='utf-8'
    msg = MIMEMultipart()
    mt = MIMEText(body.encode(encoding), 'plain', encoding)

    if jpegs:
        for fn in jpegs:
            img = open(fn, 'rb').read()
            mj = MIMEImage(img, 'jpeg', filename=fn)
            mj.add_header("Content-Disposition", "attachment", filename=fn)
            msg.attach(mj)
        msg.attach(mt)
    else:
        msg = mt

    msg['Subject'] = Header(subject, encoding)
    msg['From'] = from_addr
    msg['To'] = to_addr
    msg['Date'] = formatdate()
 
    _user = "kurosefujii@gmail.com"
    _pass = "bluetruth"

    smtp = smtplib.SMTP(server, port)
    smtp.ehlo()
    smtp.starttls()
    smtp.ehlo()
    smtp.login(_user, _pass)
    smtp.sendmail(from_addr, [to_addr], msg.as_string())
    smtp.close()

wiringpi.wiringPiSetupGpio() # GPIO名で番号を指定する
wiringpi.pinMode(18, wiringpi.GPIO.PWM_OUTPUT) # PWM出力を指定
wiringpi.pwmSetMode(wiringpi.GPIO.PWM_MODE_MS) # 周波数を固定するための設定
wiringpi.pwmSetClock(375) # 50 Hz。ここには 18750/(周波数) の計算値に近い整数を入れる
# PWMのピン番号18とデフォルトのパルス幅をデューティ100%を1024として指定。
# ここでは6.75%に対応する69を指定
wiringpi.pwmWrite(pwm_out_pin, 69) 

adc_pin0 = 0
minduty =40
maxduty=120
step =20  #step間隔を変化させれば撮影する間隔を変えられる
try:
    while True:
        data = read(0, sclk, mosi, miso, ce0) #ドアが開いたことを確認するデータを取得
        print('照度(door close)= %s'% data)
        if data > 150:
            while True:
                data2 = read(0, sclk, mosi, miso, ce0) #ドアが開いたことを確認するデータを取得ドアが閉じたことを確認するデータを取得
                print('照度(door open)= %s'% data2)
                if data2 <400:
                    for duty  in range(minduty,maxduty+step,step):
                        print(duty)
                        wiringpi.pwmWrite(18, duty)
                        sleep(0.2)
                        countnum =  take_a_picture(picnum)    #保存する写真する名前の数字を新しくする
                        picnum = picnum +1
                        js = js + ['test'+str(countnum) + '.jpg']
                        if duty >= maxduty:
                            if __name__ == '__main__':
                                body = u'\n%s\n    --- %s\n' % (u'海軍に入るくらいなら、海賊になったほうがいい。', u'スティーブ・ジョブズ')
                                print('mail send!')
                                send_email_with_jpeg('kurosefujii@gmail.com', 'rakuten765@gmail.com', u'今日の名言', body, js)
                        print("'duty")
                        sleep(0.2)
                    break
                else:
                    print "Refgirator door left open"
                    sleep(0.2)
        else:
            sleep(0.2) 

except KeyboardInterrupt:
    pass

GPIO.cleanup()
sys.exit(0)
