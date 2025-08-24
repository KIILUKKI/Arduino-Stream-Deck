import sys
from PyQt5 import QtWidgets
from mainwindow import MainWindow
from worker import SerialWorker

def main():
    app = QtWidgets.QApplication(sys.argv)
    worker = SerialWorker()
    window = MainWindow(worker,num_buttons=6)
    worker.dataReceived.connect(window.updateIndicators)
    window.startWorkerReq.connect(worker.start)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
