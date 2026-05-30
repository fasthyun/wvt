#!/usr/bin/env python3 
# -*- coding: utf-8 -*-
"""
Created on Sat Apr 24 17:01:29 2020
@author: hyun

1.1 : new start 2025.5.3
    b. fmdet, amdet, power(n) 제대로 동작
    d. analytic concept
    e. typo (2024/02/16)
    
1.2 : change wvt to waveview
    
* 설명:  
  - signal 처리에 필요한 base함수들, waveview 기능 구현에 중점을 두고 작성  
  - waveview_periodgram: 
  - make_tone: 사인파형태의 톤신호 생성함수
  - make_gaussian_pulse: 책에 나온 가우시안 펄스(?) 생성함수

TODO:
  * resampler 
    
"""

import numpy as np
from scipy import signal
import matplotlib.pyplot as plt 

def plot_time(s,_title = None):
    plt.plot(s,linewidth=0.5)
    plt.xlabel('time [s]')
    plt.title(_title)
    plt.margins(x=0) # tight!
    plt.show()

def plot_power(f,pxx,_title):
    """      
     * for PowerSpectrum with semilog.
     * no time domain!
    """
    import matplotlib.pyplot as plt
    plt.semilogy(f,pxx,linewidth=0.5)
    plt.xlabel('frequency [Hz]')
    plt.title(_title)
    plt.margins(x=0) # tight!
    plt.show()
    
def getSamples(path,_count=1000,_type=">i2"):
    """
     _type:
         16t --->  >i2
    """
    global samples
    fd=open(path,'rb')
    samples=np.fromfile(fd, dtype=_type,count=int(_count))
    print("Sample File loaded!! = ",path)
    #print(samples)
    fd.close()
    #plt.plot(samples)
    #plt.show()
    norm_samples=samples #/32000 
    #plt.plot(norm_samples)
    #plt.show()
    return norm_samples

    
def waveview_filter(_samps,factor): # (60%,hyun)
    """
    - waveview내부에서 사용하는 filter 흉내내기 
    - 목적은 90%만 살리고 나머지 높은 고주파수 부분 죽여버림
    - waveview에서는 kiser를 사용했음
    - low pass filter with Kaiser, beta, attenuation (60db) 
    - waveview: /dew/ui/display/psd/alg/Upsample.java: 
    - 실습 필요!!!    
    """
    maxPassBandFreq= 0.4*2 # 복소수신호에 대해서!
    minStopBandFreq= 0.45*2
    
    att_db=60
    tr_width = minStopBandFreq - maxPassBandFreq
    N,beta=signal.kaiserord(att_db, tr_width)
    tabs=signal.firwin(N,maxPassBandFreq,width=tr_width,window=('kaiser',beta))    # 
    filt_samps=signal.lfilter(tabs,1.0,_samps)
    return filt_samps 

def periodgram(_samps,n=1024):    
    """
    real or complex will works!
    """
    n=n*2-1
    f,spec_den=signal.periodogram(_samps,fs=1,nfft=n,window="hamming") # no shift !!! nperseg=n,
    #fft_shift=np.fft.fftshift(spec_den) 
    log_fft=np.log10(spec_den)
    #abs_fft=np.abs(log_fft)
    return log_fft


def waveview_periodgram(samps,fs,fft_size=1024,_return_onesided=False):
    """ 
    waveview's power spectrum! 
    ==========================
    
    * 작성자 : hyun
    * 왜 periodgram 이라고 했는가????
    * 설명: 90% 성공. waveview의 파워스펙트럼 보여주기. 개발 중에 결과가 맞는지 파일저장 후 waveview로 확인해야할 경우가 있다. 
     그럴때 좀 더 편하게 볼 수 있게 만든 함수.     
     - waveview periodgram은 python periodgram과 같음 ???? , 아마도 matlab periodgram도 같을듯..    
     - 입력 샘플이  real일 경우 절반만 리턴(default!)   <--- 맞나??? 
     - real or complex will works!
    
    parameters
     - fs : samp_rate
     - fft_size: fft할때   
     - _return_onesided: True면 양의 주파수영역만, false면 음주파수 영역까지
    
    returns
     - f : 주파수 배열 
     - pxx: power결과 배열 
    """    
    global f,pxx,log_pxx
    #f, pxx=signal.welch(samps,fs,nfft=1024,window="hamming",return_onesided=_return_onesided) # no shfit !!! just return new frequency
    f, pxx=signal.welch(samps,fs,nperseg=fft_size,window="hamming",return_onesided=_return_onesided) # no shfit !!! just return new frequency
    #f, pxx=signal.periodogram(samps,fs,nfft=1024,window="hamming") #  nperseg=n 
    
    if _return_onesided == False:
        f=np.fft.fftshift(f)
        pxx=np.fft.fftshift(pxx)
        log_pxx=np.log10(pxx)
        
    if _return_onesided == True and (samps.dtype==np.complex128 or samps.dtype==np.complex64) :
        half_n = int(fft_size/2)
        f = f[0: half_n]
        pxx = pxx[0: half_n]
        #pass    
    return f,pxx

def waveview_power(samps,samp_rate,power_n=2):
    """ 
     waveview: power(n)
     - 순서: analytic(hilbert) -->  filter(kizer) --->  resample(upsample)   --> power(n)
     - 구현 :97% 
     - 이해도: 90%
     - 미리 업샘플하는 이유: ok
    TODO:
      - if complex input!
      - signal.resample_poly(samps, n, 1)
    """
    if power_n != 1 :
        #print("samps=",samps)
        samps=signal.hilbert(samps) # 90% if real than, convert to analytic
        samps=waveview_filter(samps,power_n) # upsample 전 필터링, -0.45 ~ 0.45 만 살림
        samps=signal.resample(samps,len(samps)*power_n) # upsample
        samp_rate *= power_n # upsample결과 샘플레이트가 power_n만큼 커짐!
        samps=np.power(samps,power_n) # 99% ok !!
    return samps,samp_rate
    #f,pxx=waveview_periodgram(samps,samp_rate,fft_size,half)
    #return f,pxx
    
def waveview_AM_DET(samps,samp_rate,fft_size=1024,half=True):
    """
    참고: 
     AM_DETECT()    
       Floats real = MagnitudeSquared.create(outComplexFloats);
       outComplexFloats = ComplexFloatsFromFloats.create(real, null);
    """
    samps=signal.hilbert(samps)  
    m=np.abs(samps) # MagnitudeSquared 
    return m    

def rotator(samps,deg):
    """
    frequency shift 주파수 이동 (hyun)
    ------------------------
    회전각을 증가시켜줌(즉 페이져 누적) 
    복소수 곱셈이 Phaser덧셈이라는 아이디어 사용 
    각속도 증가, 결국 주파수 이동 발생
    정말 신기하게도 samp_rate 와 상관없다는거
    (이미 샘플링되면서 위상과 회전 각 크기가 정해졌기 때문)
    
    *이름문제점: 각도가 추가 회전하는게 아니라 가속도가 붙기때문에 이름이 rotator가 맞지않는다. 가속기라고 바꿔야할듯
    
    TODO
     - 느림...
    
    """
    # type(samps) == complex!!!
    _rad=(2*np.pi)*(deg/360.0)  # py2에서 0이될 수 있음 그래서 360.0사용
    _c=np.cos(_rad) + 1j*np.sin(_rad)     
    #print("_rad=",_rad)
    d_phase=(1+0j)
    out=np.zeros(len(samps),dtype=np.complex64)
    #_angle=np.angle(_c,deg=True)
    #print("angle=",_angle)
    m=np.ones(len(samps),dtype=np.complex128)
    for i,x in enumerate(m):
        m[i]=d_phase
        d_phase*=_c
    
    for i,x in enumerate(samps):
        out[i]=samps[i]*m[i]
        #samps[i]=d_phase
        #d_phase*=_c
    return out

def get_anglespeed_wns(_samps):
    """ tmp """
    tmp=_samps[0:-1] * _samps[1:].conj()    
    x=np.arctan2(tmp.imag, tmp.real) 
    return x

def get_angle_wns(samps): 
    """ 
    FM detect, Quadrature demod(GNURadio) 
    get angle with next sample
    목적: 현재 샘플과 다음 샘플과의 각(phasor)을 구하는 것
     - waveview에서는 FM DETECT라고 하고 있다
     - GNURadio에서는 quadrature demod라고 불림 
     - 복소수 각을 구하려면 나눗셈 또는 conj의 곱 사용(복소수곱특성)
    """
    c=samps[1:]*samps[0:-1].conj() # ****
    x=c.real
    y=c.imag
    theta=np.arctan2(y, x)  # theta
    return theta 
    # 다음은 배열방식 접근
    #for i in samps: 
    #    x=i.real 
    #    y=i.imag 
    #    th=math.atan2(y,x)
    #    a.append(th)
    #return a
def waveview_analytic(samps):
    return signal.hilbert(samps)
    
def waveview_power2_FM(samps,samp_rate,half=True):
    """
    waveview: power(2)(FM)  aka FM_DET 
    ------------------------------
    - 구현: 90% 
    - 이해도: 50% 
    - 순서: analytic -->  angle  --> medianFilter --> - 평균   ---> power(2)
    
    TODO: 
       - medianFilter 이해(90%) ----> median으로 변경 가능한가? ---> 힘듬 구간(세그먼트) 구분해야되서!!
       - medianFilter 는 중간값을 중심으로 잡아서 나머지 값들을 옮겨준다!!!
       - waveview_power(2)
    """
    samps= signal.hilbert(samps) # 95% # analytic # waveview_analytic(samps)    
    samps_real=get_angle_wns(samps) * samp_rate/(np.pi*2)  # 99%      
    samps_real=signal.medfilt(samps_real,7) # apply median 
    _m=samps_real.mean()  # 필요함!!
    samps_real = samps_real - _m #   idea: 자동으로 중심주파수 잡는걸 가능하게 함(hyun)
    samps = samps_real + 0j # 내말이~~~
    samps = np.power(samps,2) # 99% ok !!
    samp_rate*=1    # 맞나???
    return samps    

def test_periodgram(chunk,_fs=8e3):
    f, pxx = signal.periodogram(chunk, fs=_fs, window="flattop", scaling="spectrum")
    print( f[pxx.argmax()], pxx.argmax() )
    #plt.plot(f, 20*np.log10(np.abs(Pxx_den)))
    plt.semilogy(f, pxx)
    #plt.ylim([1, 1e7])
    plt.xlabel("Frequency")
    plt.ylabel("PSD")
    plt.show()
    
def test_compare_periodgram(samps,fs=1000):
    """ 
      welch 와 periodgram 함수 비교
      1. 똑 같은거 같음
      2. periodgram() 내부적으로 welch 사용했음!
      3. 
    """
    _nfft=1024
    #global f,pxx,log_pxx
    f, pxx=signal.welch(samps,fs,nfft=_nfft,nperseg=1024,window="hamming",average="mean") 
    plt.semilogy(f,pxx,linewidth=0.5)#,title="welch")
    plt.show()    
    
    #f, Pxx_den  = signal.periodogram(chunk, fs=_fs, window="flattop", scaling="spectrum")
    f, pxx=signal.periodogram(samps,fs,nfft=_nfft,window="hamming") # nperseg 없음!!
    #plt.plot(f,pxx)    
    plt.semilogy(f,pxx,linewidth=0.5)#,title="")
    plt.show()    
    return 
    

def analytic_signal(x):
    """
    from book(viswanathan)     
      * 목적: 음의 주파수를 제거한다,  numpy.hilbert() 함수랑 같은 목적
      * 제곱을 하지 않는 경우에는 불필요하다. 음의주파수영역이 넘치지 않기떄문에! (hyun) 
      * 목표 신호를 제곱/세제곱하는 경우에는 꼭 필요 (hyun) 
    """
    from scipy.fftpack import fft, ifft
    N=len(x)
    X=fft(x,N)
    Z=np.hstack((X[0],2*X[1:N//2],X[N//2],np.zeros(N//2-1)))
    """
    음의주파수 영역을 그냥 zero으로 채워넣어도 되는데.. (이거 틀린듯.. 허수부를 말한듯)
    
    """
    z=ifft(Z,N)
    return z

def make_tone(sample_rate, freq, duration=1):
    """ 
    cos() 함수를 이용해서 톤신호 생성  
     - real 톤 신호 발생기
     - make tone samples with linesapce()    
      
    다음 코드는 톤신호 발생시키는 다른 방법들 
    
    a=[] # python's list()
    for i in range(samp_len):
        y=math.sin(i*math.pi*2*freq/samp_rate)
        a.append(y)
    
    samp_len=samp_rate*duration
    n  = (2*np.pi * freq) / samp_rate
    na = np.arange(samp_len) * n
    a  = np.sin(na)    
    return a

    def make_cos(samp_rate,freq, duration=1): 
        x = np.linspace(0, 2*np.pi*freq, int(samp_rate*duration),dtype=np.complex64)
        y = np.cos(x)
        return y
    """
    x       = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)
    samps   = np.cos(x * 2 * np.pi * freq)
    return samps

"""
def make_sin_sample():
    sin() 함수를 이용해서 톤신호 생성 
    왜 sin함수의 2*np.pi*fs*t  값이 커질수록 더 많은 사인파가 생성되는지에 대한 아이디어 고민!   
    x = np.linspace(0, 2*np.pi,1000)
    samps = np.sin(x) # y
    return samps
"""

def make_exp1j(samp_rate,freq, duration=1): 
    """ 
    양(positive)의 주파수 복소수 톤신호 생성(CCW)          
     - return complex 
     - 시계방향은 음의 주파수 , 반시계방향이 양의 주파수
    """    
    x = np.linspace(0, duration, int(samp_rate*duration),dtype=np.complex64)  # default: complex128
    y = np.exp(1j*(x * 2 * np.pi * freq ))  
    return y

        
#def make_tone_complex(samp_rate,freq, duration=1): 
#    return make_ext1j(samp_rate,freq,duration)    

def make_special_signal() :
    
    return 

def make_fsk_samples(samp_rate,data):    
    return

   
def make_gaussian_pulse(samp_rate,sigma):
    """
    parameters:
        sigma : pulse with in seconds    
    returns:
        (t,g) : time and signal g(t)     
    """
    t= np.arange(-0.5,0.5 , 1/samp_rate)
    g= 1/(np.sqrt(2*np.pi)*sigma) * (np.exp(-t**2/(2*sigma**2)))
    return (t,g)

#import random
def add_noise(_samps):    
    """ 
      numpy.random.rand(99) 
    """
    _len=len(_samps)
    _rand=np.random.rand(_len)/30    
    #print(len(_rand),_len)
    return _rand + _samps
  
def resample(_samps, n=2):
    """
     * n: 몇배 업샘플링할껀지 배수 (정수)
     * 작성중 (4시간)
     * 
    """    
    _len=len(_samps)
    _buffer = np.zeros(_len * n)    
    for i,v in enumerate(_samps):
        _buffer[i]=v
        _buffer[i+1]=v
        pass

def resample_with_fft(_samps, n=2):
    """
     * n: 몇배 업샘플링할껀지 배수 (정수)
     * 작성중 (4시간)     
    """    
    
    return 

def test_spectrogram(chunk):
    """ signal.스펙트로그램 함수는 대체 뭘까 ? (hyun)  """
    f, t, Sxx   = signal.spectrogram(chunk, fs=10000, mode="magnitude")
    plt.pcolormesh(t, f, Sxx)
    plt.ylabel("Frequency")
    plt.xlabel("Time")
    plt.show()

from scipy import fftpack

def test_plot_powerspectrogram(chunk):
    """  
    np.fft 이거 왜...
    """
    abs_data    = np.abs(chunk)
    raw_fft     = fftpack.fft(abs_data)
    data_fft    = fftpack.fftshift(raw_fft)
    plt.plot(np.log(data_fft))
    plt.show()


def test_triangle_wave():
    """ triangle파랑 sine파랑 결국 같음(100%) """
    samps=make_tone(8e3,2e3,1) # 8k,2k, 0.1 sec    
    samps=make_exp1j(8e3,2e3,1) # 8k,2k, 0.1 sec
    
    f,pxx = waveview_periodgram(samps,8e3)
    plot_power(f,pxx,"exp1j, 2kHz")
    plt.plot(samps[0:10].real)
    plt.show()    
    return 

def test_resample():
    """ slow resampler() 실습 (1%) """
    
    return 


def test_resample_with_fft():
    """  fft를 사용해서 resample하는거 실습 (1%) """
    #samps=make_exp1j(8e3,2e3,0.1) # 8k,2k, 0.1 sec
    samps=make_tone(8e3,2e3,0.1) # 8k,2k, 0.1 sec
    #samps=add_noise(samps)
    f,pxx=waveview_periodgram(samps,8e3)
    plot_power(f,pxx,"exp1j, 2kHz")
    plt.plot(samps[0:10])
    plt.show()   
    pass

def test_hilbert(): 
    """
    결과: ok 99%
      - real신호는 좌우 미러 발생
      - hilbert()함수는 좌측(음의 주파수) 신호 제거함!!
    """
    samp_rate=8e3
    samps=make_tone(samp_rate,2e3,1)
    f,pxx=waveview_periodgram(samps,samp_rate,1024,False) # 
    plot_power(f,pxx,"without hilbert()")
    hilbert_chunk   = signal.hilbert(samps)
    f,pxx=waveview_periodgram(hilbert_chunk,samp_rate,1024,False) # 
    plot_power(f,pxx,"with hilbert()")   
    '''
    if (1295.5 <= result and result < 1296.5):
        continue
    else:
        plt.plot(frequency[length//2:], log_fft[length//2:])        
    '''

def make_signal():    
    a=range(4000)
    
    
def test_fft_shifting():
    """ 
    이해: 95%
    1.신호의 FFT를 +10 shift한 후 iFFT하면? ★★★
      →  주파수가 증가하게 된거여서 더 빠른 회전을 보일 것임 (ok)
      →  real(mirror) 존재하는 경우 생각해 보삼
    
    2.신호가 1khz인데 shift해서 0hz되면 시간영역에서는 어떻게 보일까?  ★★★
      이거 구현했는데...tutor_rotator.py 참고바람!
    
    3. 시간영역에서의 회전은 주파수영역에서 어떻게 보일까???? → 아...
    
    4. rotator() 와 비교!
    """    
    #2k 사인파(complex) 생성 
    samps=make_exp1j(8e3,1e3,0.1) # 8k,2k, 0.1 sec
    #print(len(samps))
    #samps=add_noise(samps)    
    
    fft_samps=np.fft.fft(samps)
    fft_samps=np.roll(fft_samps,10)
    #shift_fft_samps=np.fft.fftshift(fft_samps) # ifft할때는 shift할 필요없음!!!
    samps=np.fft.ifft(fft_samps)
    
    f,pxx=waveview_periodgram(samps,8e3)
    plot_power(f,pxx,"exp1j, 2kHz")
    ang=get_angle_wns(samps)            
    #print("angle=",ang)
    #plt.plot(ang)
    #plt.show()
    ang=ang*360/(2*np.pi)    
    print(ang.mean(),ang.std())
    return ang
    
def test_rotator():    
    """
     * 주파수 이동 테스트 : rotator()를 이용 (hyun)
    """
    
    import SECLAB_pcm
    path="/home/sdr/data/Documents/presetation/K-10191116H0005_G126Z_467.500_0130_0131_16t_160k.pcm.real.160k.16t"
    samp_rate=160e3
    samps=SECLAB_pcm.loadPCM_16t(path,20000) #
    samps=samps[5000:9000]
    #samps=samps.astype(np.complex128)
    samps=signal.hilbert(samps)
    #samps=signal.resample(samps,len(samps)*2)
    f,pxx=waveview_periodgram(samps,samp_rate,1024,False)
    abs_pxx=np.abs(pxx)
    plot_power(f,abs_pxx,'before rotator ')
    #print(samps)
    samps=rotator(samps,-90) # 
    f,pxx=waveview_periodgram(samps,samp_rate,1024,False)
    abs_pxx=np.abs(pxx)
    plot_power(f,abs_pxx,'after rotator ')
    return

import numpy
def test_cplx2real():
    """
     * 다음 예제는 real신호를 복소수로 변환하는 과정 실행
     * convert: complex를 real로... 
     * 샘플갯수가 2배가 되네...와....진짜 깬다....(hyun) 
    """
    import SECLAB_wave
    _path="/home/signal/ddc/K7906/220526_i0085var-235MHz_22-05-11_09'26'56_80k.ddc" # complex, samp_rate= 100k,
    
    _parser= SECLAB_wave.parseHeader(_path)
    samp_rate= _parser['sample_rate']
    _samps=_parser['samples']
    #print("xxxxx")
    debug = True
    _samps= _samps[831302: 831302 + 1024*8]
    if debug :
        f,pxx=waveview_periodgram(_samps ,samp_rate,1024,False)
        abs_pxx=np.abs(pxx)
        plot_power(f,abs_pxx,'original')
      
    _samps=signal.resample(_samps,len(_samps)*2) # upsample 2배 --> complex128
    
    if debug:
        f,pxx=waveview_periodgram(_samps,samp_rate*2,1024,False)
        abs_pxx=np.abs(pxx)
        plot_power(f,abs_pxx,'resampling x2 ')
        print("dtype=",_samps.dtype)    
        
    _samps=rotator(_samps, 90) # 90도 rotate ==> 중심주파수 이동 (0hz ==> 양의주파수 samp_rate/2),

    if debug :
        f,pxx=waveview_periodgram(_samps,samp_rate*2,1024,False)
        abs_pxx=np.abs(pxx)
        plot_power(f,abs_pxx,'after rotator')
        print(" dtype=",_samps.dtype)
    
    
    _samps_real=_samps.real # _samps[::2] 
    
    _samps= _samps*32700  # 위험!!! 노말라이즈 먼저 해야하는데...
    _samps_real_int16 = _samps_real.astype(numpy.int16)
    #_samps_real_int16.tofile(fd)
    return _samps_real_int16

def test_fftfreq():    
    """
     * fftshift()와  fftfreq() 설명을 위한 예제 (hyun)
     * fftshift는 쉽다.근데 fftfreq는 첫번째인자 샘플갯수, 두번째인자가 timestep    
    """
    import SECLAB_wave
    global _samps
    _path="/home/signal/ddc/K7906/220526_i0085var-235MHz_22-05-11_09'26'56_80k.ddc" # complex, samp_rate= 100k,    
    
    _parser= SECLAB_wave.parseHeader(_path)
    samp_rate= _parser['sample_rate']
    _samps=_parser['samples']
    print("samp_rate")
    debug = True
    _samps= _samps[831302: 831302 + 1024*8]
    _samps= _samps[0:1024]
    
    if debug :
        f,pxx=waveview_periodgram(_samps ,samp_rate,1024,False)
        abs_pxx=np.abs(pxx)
        plot_power(f,abs_pxx,'original'+"(samprate= " +str(samp_rate) +"Hz)")
        
    _fft=np.fft.fft(_samps)
    _fft=np.fft.fftshift(_fft)
    _abs_fft=np.abs(_fft)
    _log_abs_fft=np.log10(_abs_fft)    
    plt.plot(_log_abs_fft)

def test_waveview () :
    """
    - waveview 주요기능을 그대로 구현 (hyun)
    """        
    import SECLAB_pcm
    #path="230.30Mhz.pcm.real.160k.16t"
    path="/home/hyun/psk8_8k_16t.pcm" # samp 8k
    #path="/home/hyun/works/QPSK/test.pcm"
    samps=SECLAB_pcm.loadPCM_16t(path,8000*10)/32700 #+0j
    #samps=SECLAB_pcm.loadPCM(path,dtype=np.int16,_count=8000*10)/32000 #+0j
    
    samp_rate=8000
    #samps=samps[5000:9900]
    samps=samps[50:]
    print("samps len=",len(samps))
    return_onesided = True
    plot_time(samps[50:400],'waveview time: ')
    
    f,pxx=waveview_periodgram(samps,samp_rate,1024,return_onesided)
    plot_power(f,pxx,'waveview power(periodgram): ')
    
    _samps,tpm_samp_rate=waveview_power(samps,samp_rate,2)
    f,pxx=waveview_periodgram(_samps,tpm_samp_rate,1024*2,return_onesided)
    plot_power(f,pxx,'waveview power(periodgram): '+"power(2)")

    _samps,tpm_samp_rate=waveview_power(samps,samp_rate,4)
    f,pxx=waveview_periodgram(_samps,tpm_samp_rate,1024*2,return_onesided)
    plot_power(f,pxx,'waveview power(periodgram): '+"power(4)")    
    
    _samps,tpm_samp_rate=waveview_power(samps,samp_rate,8)
    f,pxx=waveview_periodgram(_samps,tpm_samp_rate,1024*2,return_onesided)
    plot_power(f,pxx,'waveview power(periodgram): '+"power(8)")

    _samps=waveview_power2_FM(samps,samp_rate)
    f,pxx=waveview_periodgram(_samps,samp_rate,1024,True)
    plot_power(f,pxx,'waveview power2 FMDET')

    _samps=waveview_AM_DET(samps,samp_rate)
    f,pxx=waveview_periodgram(_samps,samp_rate,1024,True)
    plot_power(f,pxx,'waveview AMDET')
    #plot_power(y,'waveview AM DET') 
    
    f, t, Sxx = signal.spectrogram(samps, samp_rate)#, return_onesided=True)
    plt.pcolormesh(t, f, Sxx, shading='gouraud')
    plt.show()
    

def test_compare_periodgram(samps)     :
    """
     periodgram() 함수 비교 
    """    
    samp_rate=160000
    #samps=getSamples(path,1024)
    #test_compare_periodgram(samps)
    return     

def test_gaussian_pulse():
    """ 가우시안 펄스 생성 """
    a=make_gaussian_pulse(80,0.1)
    plt.plot(a[0],a[1])
    plt.title("Gausian pulse")
    plt.show()    
    return 

def test_sine_wave():
    """ 
     2k 사인파(real), cplx 2가지 생성 
        1. 바로 real 넣을 경우 
        2. analytic_ 통해서 복소수 신호로 만들고 
      ---              
    TODO:
        1.fft 입력값이  평균 크기가 다를때 어떤 현상이 있는가????
        2. 
    """
    samp_rate= 8e3
    samps=make_tone(8e3,2e3,1) # 8k,2k, 1 sec
    samps=add_noise(samps)
    #samps=analytic_signal(samps)
    f,pxx=waveview_periodgram(samps,8e3,1024,True)
    plot_power(f,pxx,"sin wave (real) 8k, 2000Hz with Noise")

    """ 사인파(complex) 생성 """
    samps=make_exp1j(8e3,1e3,1) # 8k,2k, 1 sec
    #b=make_exp1j(8e3,2e3,0.1) # 8k,2k, 0.1 sec
    #samps=samps**2
    #samps=signal.resample(samps,len(samps)*2)
    #samps=a+b
    samps=add_noise(samps)
    f,pxx=waveview_periodgram(samps,8e3)
    #plot_power(f,pxx,"exp1j, 2kHz")
    plot_power(f,pxx,"sine wave (cplx) 8k, 1k with noise") 
    

def make_bit2pulse(bits, symbrate): 
    samps = np.arange(symbrate*bits.length,dtype=np.complex64)
    for i,b in enumerate(bits):
        if b == True : 
            samps[i]=1.0 
    return


def test_bit2pulse():
    from bitstring import Bits, BitArray, BitStream

    ba1  = BitArray(r"0xDEADBEEF")
    make_bit2pulse(ba1, 300)
    
#from PyQt5 import QtMultimediaWidgets # sound 안됨!!!
import sys
#### __main__
if __name__ == "__main__": 
    #test_bit2pulse()       
    test_waveview()
    #test_triangle_wave()
    #test_cplx2real()
    #test_fftfreq()  # ?
    #test_hilbert() # hilbert 동작 확인!    
    #test_rotator()  # rotator 동작 확인!    
    #test_resample_with_fft() # 
    #test_fft_shifting()
    #test_sine_wave()
    #samps=make_exp1j(8e3,3,10) # 8k,2k, 1s
    #fig = plt.figure()
    #ax = fig.add_subplot(111, projection='3d') #Axes3D
    #ax. plot(samps.real,samps.imag)    
    # pass
       
    #samp_rand=random.random(1024)/100
    ### Time domain
    #tone_a = make_tone2(samp_rate,4e3)
    #tone_b = make_tone2(samp_rate,10)
    
    #samps=tone_a[0:1024] #+  tone_b[0:1024] +0j 
    #samps=tone_a[0:1024]# + 0j#+  tone_b[0:1024] +0j 
    #plot_power(tone_a," tone_a :time domain")
    #plot_power(samps,"time domain")
    #samps=samps + samp_rand
    #xplot(samps[0:100],"time domain")
    #plot_power(samps[0:100],"time domain")
    pass
    

