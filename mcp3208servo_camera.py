#!/usr/bin/env python



import RPi.GPIO as GPIO
import time
import subprocess
from time import sleep
import signal
import sys
picnum =1   #保存する写真する名前の数字の初期値
#servo configuration
maxaz =10
minaz =2
step =2
GPIO.setmode(GPIO.BCM)
# GPIO 12番を使用 (PWM 0)
GPIO.setup(14, GPIO.OUT)
# 20ms / 50Hzに設定、らしい
servo = GPIO.PWM(14, 50)
# 初期化
servo.start(0.0)


GPIO.setmode(GPIO.BCM)
GPIO.setup(23, GPIO.OUT)
GPIO.setup(24, GPIO.OUT)
#(0, sclk, mosi, miso, ce0)sclk = 11,miso = 9,mosi = 10,ce0 = 8
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
        subprocess.call(camera,shell = True)
        subprocess.call(updatedb,shell = True)
        print('check to exist a picture_data_2nd')
        ret  =  subprocess.call(confirm,shell = True)

        if ret == 0: #cmdの結果はcatコマンドで画像があれば0を返し、なければ1を返す
            print ret == 0   #File is existed
            print('picture_data is existed.Upload!')
        else:
            print "we can't take a picture" #File is not existed
            print('one more take a picture')
            print('Waitig for 10 sec ')
            GPIO.output(4, GPIO.HIGH)
            time.sleep(10)
            GPIO.output(4, GPIO.LOW)
            time.sleep(10)
            continue
        subprocess.call(dropbox,shell = True) # upload
        print "dropbox upload success"
        print 'count=' + str(count)
        break 
          
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

try:
    while True:
        data = read(0, sclk, mosi, miso, ce0) #ドアが開いたことを確認するデータを取得
        print('data = %s'% data)
        if data > 900: 
            while True:
                data2 = read(0, sclk, mosi, miso, ce0) #ドアが開いたことを確認するデータを取得ドアが閉じたことを確認するデータを取得
                print('data2 = %s'% data2)
                sleep(0.2)
                if data2 <500:
                    for dc in range(minaz, maxaz, step):
                        GPIO.setup(14, GPIO.OUT)
                        # 20ms / 50Hzに設定、らしい
                        servo = GPIO.PWM(14, 50)
                        # 初期化
                        servo.start(0.0)
                        servo.ChangeDutyCycle(dc)
                        servo.ChangeDutyCycle(dc)
                        servo.ChangeDutyCycle(dc)
                        servo.ChangeDutyCycle(dc)
                        servo.ChangeDutyCycle(dc)
                        time.sleep(0.5)
                        servo.stop()
                        print('refgirator door check closed!')
                        GPIO.output(14, GPIO.HIGH)
                        time.sleep(10)
                        #GPIO.output(25, GPIO.HIGH)
                        take_a_picture(picnum)    #保存する写真する名前の数字を新しくする
                        picnum = picnum +1
                
                else:
                    GPIO.output(14, GPIO.LOW)
                    print "Refgirator door left open"
        else:
            GPIO.output(14, GPIO.LOW)
            sleep(0.2) 
except KeyboardInterrupt:
    pass

GPIO.cleanup()
sys.exit(0)
servo.stop()
