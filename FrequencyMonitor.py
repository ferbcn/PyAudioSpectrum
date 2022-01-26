import sys
from AudioIn import AudioIn
import numpy as np

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QLabel, QComboBox, QSlider
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

#CHUNK = 44100 #1024
SAMPLE_RATE = 44100

class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super(MplCanvas, self).__init__(self.fig)
        self.fig.set_facecolor('#595959')
        self.bx = self.fig.add_subplot(111)
        self.fig.tight_layout(h_pad=3)

        self.init_plot(chunk=44100)


    def init_plot(self, chunk=44100):

        self.chunk = chunk
        self.bx.set(xlabel='Frequency [Hz]', facecolor='#3a3a3a')
        self.bx.xaxis.label.set_fontsize('small')
        self.bx.set(facecolor='#3a3a3a')
        self.bx.set_title('Frequency Domain', color='#000000', size='medium')
        self.bx.tick_params(axis='both', which='major', labelsize=6, labelcolor='#000000')
        self.bx.set_ylim([0, 2000])
        self.bx.set_xlim([0, 5000])

        x = np.arange(0, SAMPLE_RATE/2, SAMPLE_RATE/chunk)
        y = [0 for x in range(int(chunk/2))]
        self.bar1, = self.bx.plot(x, y, 'r-')

    def update_plot(self, data):
        # update frequency plot
        # define spectrogram
        # t = np.linspace(0, 1, len(data))
        #print(len(data))
        # s = data
        # T = t[1] - t[0]  # sampling interval
        N = data.size
        fft = np.fft.fft(data)
        # 1/T = frequency
        # f = np.linspace(0, 1 / T, N)
        abs_data = np.abs(fft)
        bar_data = abs_data[:N // 2] * 1 / N
        #print(len(bar_data))

        hz = bar_data.argmax(axis=0) * SAMPLE_RATE/self.chunk
        self.bar1.set_ydata(bar_data)

        # update figure
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

        return hz


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.title = 'Frequency Monitor and Analyzer'
        self.setWindowTitle(self.title)

        self.width = 800
        self.height = 600
        self.left = 10
        self.top = 10

        self.monitor_on = False
        self.fast_mode_on = False

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.refresh_rate = 10

        self.chunk=44100
        self.myaudio = AudioIn(chunk=self.chunk)
        #print(self.myaudio.get_input_devices_info())
        self.hz = 0
        self.input_device_id = None

        self.initUI()
        self.show()

    def initUI(self):

        page_layout = QVBoxLayout()
        page_widget = QWidget()
        page_widget.setLayout(page_layout)

        self.setStyleSheet("background-color: #595959")
        self.setGeometry(self.left, self.top, self.width, self.height)

        # Drop down menu for input selection
        input_layout = QHBoxLayout()
        input_devices = self.myaudio.get_input_devices_info()
        self.input_device_id = self.myaudio.get_default_input_device().get('index')
        comboBox = QComboBox(self)
        comboBox.setMaximumWidth(200)
        for device in input_devices:
            comboBox.addItem(device.get('name'))
        comboBox.activated[str].connect(self.input_choice)
        input_layout.addWidget(comboBox)

        # ON-OFF Monitor
        self.button_on = QPushButton('MONITOR - OFF', self)
        self.button_on.setToolTip('Turn Line-In/Mic  On / Off')
        self.button_on.setStyleSheet("background-color: #777777")
        self.button_on.setMinimumHeight(50)
        self.button_on.setMinimumWidth(100)
        self.button_on.setMaximumWidth(200)
        self.button_on.clicked.connect(self.on_click)
        input_layout.addWidget(self.button_on)

        self.button_fast = QPushButton('FAST MODE - OFF', self)
        self.button_fast.setToolTip('Turn Fast Mode On / Off')
        self.button_fast.setStyleSheet("background-color: #777777")
        self.button_fast.setMinimumHeight(50)
        self.button_fast.setMinimumWidth(100)
        self.button_fast.setMaximumWidth(200)
        self.button_fast.clicked.connect(self.on_fast)
        input_layout.addWidget(self.button_fast)

        input_widget = QWidget()
        input_widget.setMaximumHeight(50)
        input_widget.setLayout(input_layout)

        # Create the maptlotlib FigureCanvas object,
        self.mpl_canvas = MplCanvas(self, width=5, height=4, dpi=100)

        plot_layout = QVBoxLayout()
        plot_layout.addWidget(self.mpl_canvas)
        plot_widget = QWidget()
        plot_widget.setMinimumHeight(400)
        plot_widget.setLayout(plot_layout)

        info_layout = QHBoxLayout()
        self.hz_label = QLabel()
        self.hz_label.setAlignment(Qt.AlignRight)
        #self.hz_label.setMaximumWidth(100)
        self.hz_label.setFixedHeight(30)
        #self.hz_label.setMargin(20)
        #self.hz_label.setStyleSheet("background-color: #3a3a3a;  color : red")
        self.hz_label.setStyleSheet("color : red; font-size:20px")
        info_layout.addWidget(self.hz_label)

        self.hz_txt_label = QLabel("Hz")
        self.hz_txt_label.setAlignment(Qt.AlignLeft)
        #self.hz_txt_label.setMaximumWidth(100)
        self.hz_txt_label.setFixedHeight(30)
        #self.hz_txt_label.setMargin(20)
        #self.hz_txt_label.setStyleSheet("background-color: #3a3a3a;  color : red")
        self.hz_txt_label.setStyleSheet("color : red; font-size:20px;")
        info_layout.addWidget(self.hz_txt_label)

        control_layout = QHBoxLayout()
        slider0 = QSlider(Qt.Horizontal)
        slider0.setMinimum(1000)
        slider0.setMaximum(10000)
        slider0.setValue(5000)
        slider0.setMaximumWidth(300)
        slider0.setStyleSheet(
            "QSlider::handle:horizontal {background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #b4b4b4, stop:1 #3a3a3a); border: 1px solid #5c5c5c; width: 10px; border-radius: 3px; margin: -7px 0;} \
             QSlider::groove:horizontal {border: 1px solid #777777;height: 5px; background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #b22222, stop:1 #777777); margin: 0px 0;}")
        slider0.valueChanged.connect(self.slider_change)
        slider0.setTickInterval(1000)
        slider0.setTickPosition(QtWidgets.QSlider.TicksBothSides)

        slider1 = QSlider(Qt.Horizontal)
        slider1.setMinimum(100)
        slider1.setMaximum(2000)
        slider1.setValue(5000)
        slider1.setMaximumWidth(300)
        slider1.setStyleSheet(
            "QSlider::handle:horizontal {background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #b4b4b4, stop:1 #3a3a3a); border: 1px solid #5c5c5c; width: 10px; border-radius: 3px; margin: -7px 0;} \
             QSlider::groove:horizontal {border: 1px solid #777777;height: 5px; background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #b22222, stop:1 #777777); margin: 0px 0;}")
        slider1.valueChanged.connect(self.amplitude_change)
        slider1.setTickInterval(1000)
        slider1.setTickPosition(QtWidgets.QSlider.TicksBothSides)

        control_layout.addWidget(slider0)
        control_layout.addWidget(slider1)
        control_widget = QWidget()
        control_widget.setFixedHeight(50)
        control_widget.setLayout(control_layout)


        info_widget = QWidget()
        info_widget.setLayout(info_layout)

        page_layout.addWidget(input_widget)
        #page_layout.addWidget(button_widget)
        page_layout.addWidget(plot_widget)
        page_layout.addWidget(control_widget)
        page_layout.addWidget(info_widget)

        self.setCentralWidget(page_widget)


    def on_click(self):
        if not self.monitor_on:
            self.myaudio.start_stream(chunk=self.chunk, device=self.input_device_id)
            self.monitor_on = True
            self.button_on.setText('MONITOR - ON')
            self.button_on.setStyleSheet ("background-color: #3a3a3a; color: green")
            self.timer.start(self.refresh_rate)
        else:
            self.myaudio.stop_stream()
            self.monitor_on = False
            self.button_on.setText('MONITOR - OFF')
            self.button_on.setStyleSheet ("background-color: #777777")
            self.timer.stop()

    def on_fast(self):
        if not self.fast_mode_on:
            self.fast_mode_on = True
            self.chunk=4100
            self.restart_stream()
            self.button_fast.setText('FAST MODE - ON')
            self.button_fast.setStyleSheet("background-color: #3a3a3a; color: green")
        else:
            self.fast_mode_on = False
            self.chunk = 41000
            self.restart_stream()
            self.button_fast.setText('FAST MODE - OFF')
            self.button_fast.setStyleSheet("background-color: #777777")

    def restart_stream(self):
        self.myaudio.stop_stream()
        self.mpl_canvas.bx.clear()
        self.mpl_canvas.init_plot(chunk=self.chunk)
        self.myaudio = AudioIn(chunk=self.chunk)
        self.myaudio.start_stream(chunk=self.chunk, device=self.input_device_id)
        self.monitor_on = True

    def update_data(self):
        self.hz = self.mpl_canvas.update_plot(self.myaudio.audio)
        self.hz_label.setText(str(int(self.hz)))

    def input_choice(self, choice):
        self.input_device_id = self.get_device_index_by_name(choice)
        if self.monitor_on:
            self.myaudio.stop_stream()
            self.myaudio.start_stream(chunk=self.chunk, device=self.input_device_id)

    def get_device_index_by_name(self, choice):
        input_devices = self.myaudio.get_input_devices_info()
        device_id = 0
        for device in input_devices:
            if device.get('name') == choice:
                device_id = device.get('index')
        return device_id

    def slider_change(self, value):
        self.mpl_canvas.bx.set_xlim([0, value])
        # self.mpl_canvas.ax.set_xlim([0, 1000-value/10])
        self.mpl_canvas.draw()

    def amplitude_change(self, value):
        self.mpl_canvas.bx.set_ylim([0, value])
        # self.mpl_canvas.ax.set_xlim([0, 1000-value/10])
        self.mpl_canvas.draw()


app = QtWidgets.QApplication(sys.argv)
w = MainWindow()
app.exec_()