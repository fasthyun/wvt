# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

ver=0.1
from PyQt5.QtWidgets import QApplication,QMainWindow, QWidget, QPushButton, QVBoxLayout
from PyQt5.QtWidgets import QFrame, QMessageBox, QFileDialog, QListWidgetItem,QGraphicsRectItem
from PyQt5.QtGui import QPainter, QImage, QPen, QColor
from PyQt5.QtCore import QTimer ,QRect , Qt , pyqtSlot, QRectF
from PyQt5.QtCore import QMetaObject
from PyQt5 import uic
#from PyQt5 import rc
import pyqtgraph as pg
import qdarkstyle

from SECLAB_signal import waveview_power
from SECLAB_signal import waveview_periodgram
from SECLAB_pcm import loadPCM


#switchbox_widget, switchbox_widget_class = uic.loadUiType('switchbox.ui')
top_widget, widget_class = uic.loadUiType('main.ui')
plot_window, plot_widget_class = uic.loadUiType('form_wave.ui')
powerspectrum_window, powerspectrum_widget_class = uic.loadUiType('form_powerspectrum.ui')

#plot_window, plot_widget_class = uic.loadUiType('form_wave.ui')

import os

import numpy as np
from scipy.io import wavfile

def load_wav(_path):
    #wavfile.write("test.wav", 8000, s)
    # float64, int32, int16, uint8
    samp_rate, samp = wavfile.read(_path)
    return samp_rate , samp

class listitem(QListWidgetItem):
    def __init__(self,fname,fsize) :
        self.filename=fname
        self.file_size=fsize
        pass
    pass

#print("DEBUG: MainWindow")
_path_test = '/home/hyun/works/wvt'
class MainWindow_X(top_widget, widget_class) :
    def __init__(self) :
        print("DEBUG:Main.init() ",widget_class)
        super().__init__() # python3
        self.setupUi(self)
        _screen=self.screen()
        print("screen size=",_screen.size().width(),_screen.size().height())
        if _screen.size().width()==1024 :
            self.showFullScreen()
        
        
        self.update_list(_path_test)
        #self.pushButton_select_dir.clicked.connect(self.on_pushButton_select_dir_clickedx)
        self.pushButton_timedomaim.clicked.connect(self.on_pushButton_timedomain_clicked)
        # 2. 이름으로 슬롯 자동 연결 활성화
        QMetaObject.connectSlotsByName(self)
        
        
        
    def update_list(self,_path):
        it=os.scandir(_path)
        for i in it:
            if i.is_file() :
                st=os.stat(_path +'/'+ i.name)
                print(i.name, st.st_size)
                _str = i.name #  + ":" + str(st.st_size)
                self.listWidget.addItem(_str)

    @pyqtSlot()
    def on_pushButton_select_dir_clicked(self):
        print("clicked!")
        _path=QFileDialog.getExistingDirectory(self,"caption",".")
        self.update_list(_path)


def onAppQuit():
    print("on Quit()!!")
    #if server is not None:
    #    server.server_close()
    #    print("close server!!")
    if app is not None:
        print("close all windows!")
        app.closeAllWindows()
        #del app



class plotwidget(pg.PlotWidget):
    def __init__(self,_parent) :
        super().__init__() # python3
        self.vlines=[]
        self.parent=_parent
        self.getViewBox().setMouseEnabled(x=False, y=False) # panning Disable!
        
        # 방법 A: 단일 문자 (w: 흰색, k: 검은색, r: 빨간색, g: 초록색, b: 파란색 등)
        #plot_widget.setBackground('w')

        # 방법 B: RGB 또는 RGBA 튜플 (0-255 범위)
        self.setBackground((255, 255, 255)) # 흰색
        # plot_widget.setBackground((255, 255, 255, 100)) # 알파 채널을 통한 투명도 조절

        
    def on_vline_changed(self):
        self.parent.update_selected_region(self.vlines)
        #print("moved!")
        
    def mousePressEvent(self, event):        
        plt=self.getPlotItem()
        # Check for left click
        if event.button() == Qt.LeftButton:
            # Map the click position to scene coordinates
            #scene_pos = self.mapToScene(event.pos())
            scene_pos = plt.mapToScene(event.pos())
            ##vpos = self.mapToView(event.pos())     
            vpos=self.plotItem.vb.mapSceneToView(scene_pos)
            #print(f"Clicked at scene coordinates: {scene_pos} {vpos}")
            if len(self.vlines) < 2 :
                _vline=pg.InfiniteLine(vpos, movable=True, angle=90, label='vline',pen= pg.mkPen(color=(255,0,0), width=2)) #vertical 
                self.addItem(_vline)
                self.vlines.append(_vline) 
                _vline.sigPositionChanged.connect(self.on_vline_changed)
                self.parent.update_selected_region(self.vlines)
                
        # Call the base class implementation to keep standard behavior (like dragging)
        super().mousePressEvent(event)
    
    
class PowerSpectrumWindow(powerspectrum_window, powerspectrum_widget_class) :
    def __init__(self) :
        print("DEBUG:PowerSpectrumWindow.init() ",widget_class)
        super().__init__() # python3        
        self.setupUi(self)
        self.setWindowTitle("PowerSpectrum Window")
        self.rows_n = 1
        self.width  = 200
        self.start_pos=0
        self.end_pos=-1
        self.samprate =0 
        self.total_samples_n=0
        self.samples=np.ndarray(1)
        self.path=None 
        l=self.frame_plot.layout()
        self.plot = plotwidget(self)
        l.addWidget(self.plot)
        self.plot.show()     
        
    def update_selected_region(self, vlines):
        pass
        
    def set_samplerate(self, _rate):
        self.samprate= _rate
        
    #def set_samples(self, _samps):
    #    self.samps=_samps
        
    def update_powerspectrum(self, _n=1):
        _samps = self.samples[self.start_pos:self.end_pos]
        _N=int(self.lineEdit_power_N.text())
        _samps,_samp_rate=waveview_power(_samps,self.samprate,_N)
        f,pxx=waveview_periodgram(_samps,_samp_rate,1024,True)
        self.plot.clear()
        self.plot.setLogMode(x=False, y=True)
        self.plot.plot(x=f,y=pxx)
        
    def set_samples(self, _samp, _samprate=None):
        self.samples=_samp
        self.samprate=_samprate
        self.total_samples_n=len(_samp)
        self.update_ui()
        self.update_powerspectrum()
        self.plot.show()        
        
    def update_ui(self):        
        self.lineEdit_start_pos.setText(str(self.start_pos))
        self.lineEdit_end_pos.setText(str(self.end_pos))
        #self.lineEdit_width.setText(str(self.width))
        self.lineEdit_samprate.setText(str(self.samprate))
        self.lineEdit_total_samples_n.setText(str(self.total_samples_n))
        pass               
    
    @pyqtSlot()
    def on_pushButton_power1_clicked(self):
        #self.plot_powerspectrum(1)
        print("clicked!")
    
    @pyqtSlot()
    def on_lineEdit_power_N_editingFinished(self):
        _N=int(self.lineEdit_power_N.text())
        self.update_powerspectrum(_N)
        print("power N updated", _N)
        
class MainWindow(plot_window, plot_widget_class) :
    def __init__(self) :
        print("DEBUG:MainWindow.init() ",widget_class)
        super().__init__() # python3
        self.setupUi(self)
        self.rows_n = 1
        self.width  = 2000
        self.start_pos=0
        self.samprate =0 
        self.total_samples_n=0
        self.samples=np.ndarray(1)
        self.path=None
        self.plot_mode=0 # 0:time 1:sptectorgram
        #rect = QGraphicsRectItem(QRectF(0, 0, 1, 5e-11))
        #rect.setPen(pg.mkPen(100, 200, 100))
        #self.plot.addItem(rect)
        l=self.frame_plot.layout()
        self.powerspectrum_window=PowerSpectrumWindow()
        self.powerspectrum_window.hide()
        self.plots=[]
        for i in range(10):
            #plt= pg.PlotWidget()
            plt= plotwidget(self)
            self.plots.append(plt)
            l.addWidget(plt)
            #plt.hide()
            
        #self.plot.setLabel('left', 'Value', units='V')
        #self.plot.setLabel('bottom', 'Time', units='s')
        #self.plot.setXRange(0, 2)
        #self.plot.setYRange(0, 1e-10)
        #self.update_plot_samples(samp, samp_rate)
        self.load_file("/home/hyun/works/wvt/psk8_8k_16t.pcm")
        #self.load_file("/home/hyun/works/wvt/test.wav")
        
    def load_file(self, _path):
        #samp_rate, samp = load_wav(_path)
        samps,samp_rate,_dtype,_cplx_flag = loadPCM(_path,dtype=">i2")
        if samp_rate ==0 :
            samp_rate = 8000
        
        self.total_samples_n=len(samps)
        self.width = samp_rate # default witdh_sample_n
        
        self.update_samples(samps, samp_rate)
        self.update_plots()
        self.powerspectrum_window.set_samples(samps,samp_rate)        
        self.path=_path
        print("len=",len(samps))
        
    def set_samplerate(self, _rate):
        self.samprate= _rate
        
    def set_samples(self, _samps):
        self.samps=_samps
    
    def update_samples(self, _samp, _samprate):
        self.samples=_samp
        self.samprate=_samprate       
        self.total_samples_n=len(_samp)                
        
    def update_plots(self):
        self.rows_n = int(self.total_samples_n / self.width)        
        self.update_ui()
        start_i=0
        for i, plt in enumerate(self.plots):
            if i < self.rows_n:                
                plt.clear()
                if self.plot_mode == 0 :
                    plt.plot(self.samples[start_i:start_i+self.width],pen="k")
                else:
                    plt.plot(self.samples[start_i:start_i+self.width],pen="k")
                    pass
                start_i += self.width
                print("start_i=",start_i)
                plt.show()
            else:
                plt.hide()
            pass
        
    def update_selected_region(self, vlines):
        _values=[]
        for line in vlines:
            _values.append(int(line.value()))
            #print(line.value())
        _values.sort()        
        print(_values)
        if len(_values) == 2:
            self.powerspectrum_window.start_pos=_values[0]
            self.powerspectrum_window.end_pos=_values[1]
            self.powerspectrum_window.update_ui() 
            self.powerspectrum_window.update_powerspectrum()
    
    def update_ui(self):
        #self.setWindowTitle(self.path)
        if self.plot_mode ==0 :
            self.radioButton_time_domain.setChecked(True)
        else:            
            self.radioButton_spectrogram.setChecked(True)
        self.lineEdit_width.setText(str(self.width))
        self.lineEdit_samprate.setText(str(self.samprate))
        self.lineEdit_total_samples_n.setText(str(self.total_samples_n))
        self.lineEdit_row.setText(str(self.rows_n))
        self.lineEdit_filepath.setText(self.path)
        page_n=self.total_samples_n/self.width/self.rows_n
        self.horizontalScrollBar.setMaximum(int(page_n))
        self.horizontalScrollBar.setMinimum(0)
        pass
    
    
    @pyqtSlot()    
    def on_radioButton_time_domain_clicked(self):                   
        print("clicked")
        self.plot_mode = 0
        self.update_plots()
        
    @pyqtSlot()    
    def on_radioButton_spectrogram_clicked(self):                   
        print("clicked")
        self.plot_mode = 1 
        self.update_plots()
        #image_item = pg.ImageItem(image_data)
        #plot_widget = pg.PlotWidget()
        #plot_widget.addItem(image_item)
        #plot_widget.show()
        
    @pyqtSlot()    
    def on_lineEdit_width_textEdited(self, _txt):                   
        print(_txt)
    
    @pyqtSlot()    
    def on_lineEdit_width_editingFinished(self):        
        self.width = int(self.lineEdit_width.text())
        
        self.update_plots()
        #print("value",self.width)
        
        
    @pyqtSlot()
    def on_pushButton_powerspectrum_clicked(self):
        print("clicked!")    
        
        self.powerspectrum_window.show()
        
    @pyqtSlot()
    def on_pushButton_timedomain_clicked(self):
        print("clicked!")        
    
    @pyqtSlot()
    def on_pushButton_filepath_clicked(self):
        print("clicked!")
        _path,__=QFileDialog.getOpenFileName(self,"caption",".")
        self.lineEdit_filepath.setText(_path)
        print(_path)
    
        
print("DEBUG: before QApplication()")
app = QApplication([])  # why ? hang here????

#app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

#pw = pg.PlotWidget(name='Plot1')  ## giving the plots names allows us to link their axes together
#l.addWidget(pw)

## Add in some extra graphics

#app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))
print("DEBUG: before Mainwindow()")
#window = MainWindow()
#cw=window.centralWidget()
#l=cw.layout()
#l.addWidget(pw)
#window.show()
window_plot = MainWindow()
window_plot.show()

def test_polt():
    pass


print("DEBUG: after show()")
app.aboutToQuit.connect(onAppQuit)
#app.aboutToQuit.connect(window.sock_client.close)

print("DEBUG: before app.exec()")
app.exec()
