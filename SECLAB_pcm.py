#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 11 16:13:19 2019

@author: hyun
  
 SECLAB_pcm.py   v0.3

 * 기능: 16t, 16tl , cplx.16t, cplx.16tl, 32f, complex64
 * wavetool's file naming conventions 지원
      -> foo.real.8000.16t, foo.real.8k.16t , foo.cplx.5M.32fl
  
  TODO:
   
   * 16t nomalize 하고 안할때 엄청난 차이... 왱??? samps/32000
   
   * K-10190524Z0004.pcm    
   
   * 이거 어디서 가져왔지?(hyun)
     dt : this is the data type of the signal; supported data types
       include: (from Magick5)       
          * 8o (16o) : 8-bit (16-bit) offset binary; e.g., AST Snapper
          * 8t (16t) : 8-bit (16-bit) two's complement
          * 8a : eight-bit A-law
          * 8u : eight-bit u-law

"""

import numpy as np
import os
    
def loadPCM_16t(path,_count=None):
    """
    load 16t (big-endian 16bit pcm)
    """
    #global samples
    fd=open(path,'rb')
    if _count == None :
        samples=np.fromfile(fd, dtype=">i2") # big-endian
    else :
        samples=np.fromfile(fd, dtype=">i2",count=int(_count)) # big-endian
    fd.close()
    norm_samples=samples/32000
    return norm_samples    

def loadPCM_complex_int32(path, _dtype="<i2",_count=-1, scale=32000.0):
    """    
    * numpy는   real(int16)+imag(int16)를 지원하지 않는다. 그래서 필요한 함수. 
    * wvt에서는 다음처럼 표기한다. cplx.16t, cplx.16tl
    * dtype=">i2" or "<i2"     
    * Return:
        numpy.complex64
     
    """
    fd=open(path,'rb')
    array_int16 = np.fromfile(fd, dtype=_dtype, count=_count*2)
    #print(array_i16[0:4])
    array_float32 = array_int16.astype(dtype=np.float32)/scale
    #print(array_f32[0:4])
    array_complex64= array_float32.view(dtype=np.complex64)
    #print(array_c64[0:2])
    return array_complex64


def loadPCM_cplx16t(path,_count=99999):
    """
    complex, int16(big-endian) ---> int16,int16    
    """
    return loadPCM_complex_int32(path,_count, dtype='>i2') # big-endian int16
    

def loadPCM_cplx16tl(path,_count=99999):
    """
    complex_int16(little_endian) --> int16(real),int16(imag)      
    """
    return loadPCM_complex_int32(path,_count, dtype='<i2') # little-endian int16
    

def loadPCM_complex64(path,_count=100):
    """
    Dont need !
    """
    fd=open(path,'rb')
    array_c64 = np.fromfile(fd, dtype=np.complex64, count=_count)
    return array_c64

def loadPCM_32f(path,_count=100):
    """
    Dont need !
    real float32 from little-endian
    """
    fd=open(path,'rb')
    array_f32 = np.fromfile(fd, dtype=np.float32, count=_count)    
    print(array_f32[0:4])
    return array_f32 


def parseWVTnaming(_path):
    """
    - 70%
    - WVT file naming conventions  ---> numpy.dtype      
    - examples 
        foo.real.8000.16t, foo.real.8k.16t , foo.cplx.5M.32fl     
        
    - return :
        [isComplex, samp_rate, dtye]
    """
    dtypes={'8a':np.int8,'8t':np.int8,
            '16t':'>i2','16tl': np.int16,
            '32fl':np.float32,'32f':'>f4'} 
    
    _split=_path.split(".")
    _wvt_dtype=_split[-1]
    _ok=False
    
    if _wvt_dtype in dtypes.keys():
        _dtype= dtypes[_wvt_dtype]
        _samp_rate= _split[-2]        
        if _split[-3] == 'cplx' :
            _cplx=True
        else: 
            _cplx=False
    else:
        print ("name not support :",_path)
        return [False,False,False]
                    
    return [_cplx,_samp_rate,_dtype]

def checkWVTnaming(_path):
    _result=parseWVTnaming(_path)
    if _result[2]==False:
        return False
    return True

def loadPCM(_path,dtype=None,_complex=False,_count=-1):
    _cplx_flag=False
    _samp_rate=0
    _dtype=None
    print("loacPCM(): "+_path)
    if os.path.exists(_path) == False:
        print("file not exists :" , _path)
        return None    
    
    if checkWVTnaming(_path)    :
        print("loadPCM(): wvt file naming not found...")
        ps=parseWVTnaming(_path)
        _samp_rate=ps[1]
        _cplx_flag=ps[0]
        _dtype=ps[2]
        #print("loadPCM_wvt=",ps)
    
    fd=open(_path,'rb')
    if _complex  :
        print(__name__,"complex") 
        if _dtype==">i2" or dtype=="<i2" or dtype==np.int16:
            samps=loadPCM_complex_int32(_path,_dtype)
        elif _dtype==">f32" or _dtype==np.float32 :
            if _dtype==np.float32 :
                _dtype=np.complex64
            if _dtype=='>f32':
                _dtype='>c64' #works?          
            samps=np.fromfile(fd, dtype=_dtype)
            print("complex : np.float32")
        elif _dtype==np.complex64 :
            samps=np.fromfile(fd, dtype=_dtype)
        else:
             print ("ERROR: [SECLAB_pcm] not support dtype=",dtype) 
             return None
    else:
        print("not complex")
        samps=np.fromfile(fd, dtype=dtype)
    fd.close()
    ##print(samps)
    return samps,_samp_rate,_dtype,_cplx_flag
    

def loadPCM_wvt(_path):
    if checkWVTnaming(_path)    :        
        ps=parseWVTnaming(_path)        
        samp_rate=ps[1]
        _cplx=ps[0]        
        _dtype=ps[2]
        print("loadPCM_wvt=",ps)
        samps=loadPCM(_path,_dtype,_cplx)
        return samps
    else:
        print("not wvt file naming..")
        return None
    
def test_parseWVTnaming():
    paths=['foo.real.8000.16t','foo.real.8k.16t','foo.cplx.5M.32fl']    
    for p in paths:
        _ok=checkWVTnaming(p)
        if _ok :
            fields=parseWVTnaming(p)
            print(p," ==> ",fields)
    #print(__package__,__file__,__name__)
    return 

if __name__ == "__main__":
    test_parseWVTnaming()
