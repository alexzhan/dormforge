# -*- coding:utf-8 -*-
from base64 import b64encode,b64decode  
  
key = "alexzhang==juliewong"

def encode(unicodeString):  
    strorg=unicodeString.encode('utf-8')  
    strlength=len(strorg)  
    baselength=len(key)  
    hh=[]  
    for i in range(strlength):  
        hh.append(chr((ord(strorg[i])+ord(key[i % baselength]))%256))  
    return b64encode(''.join(hh)).encode("hex")
  
def decode(orig):  
    strorg = b64decode(orig.decode("hex").encode('utf-8'))  
    strlength=len(strorg)  
    keylength=len(key)  
    mystr=' '*strlength  
    hh=[]  
    for i in range(strlength):  
        hh.append((ord(strorg[i])-ord(key[i%keylength]))%256)  
    return ''.join(chr(i) for i in hh).decode('utf-8')  
  
if __name__=='__main__':  
    print encode('4')
    print len(encode('4'))
    print decode('6b7032577161755a')  
