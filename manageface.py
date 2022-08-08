# -*- coding: utf-8 -*-

"""
    @Author  : Mumu
    @Time    : 2022/8/6 14:35
    @Function:

"""
import cv2
import pymysql
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
database = 'studentface'
password = 'hzt123'
engine = create_engine('mysql+pymysql://root:hzt123@localhost:3306/studentface')
conn = pymysql.connect(host='localhost',
                       user='root',
                       password=password,
                       database=database,
                       port=3306,
                       charset='utf8')


class Ui_MainWindow(QMainWindow):

    def __init__(self):
        super(QtWidgets.QMainWindow, self).__init__()
        self.setupUi(self)
        self.retranslateUi(self)

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(700, 488)
        self.centralWidget = QtWidgets.QWidget(MainWindow)
        self.centralWidget.setObjectName("centralWidget")
        self.retranslateUi(MainWindow)

        self.tableWidget = QtWidgets.QTableWidget(self.centralWidget)
        self.tableWidget.setGeometry(QtCore.QRect(0, 60, 460, 400))
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(0)
        self.tableWidget.setRowCount(0)
        self.tableWidget.setStyleSheet("selection-background-color:pink")
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # self.tableWidget.setEditTriggers(QAbstractItemView.DoubleClicked)
        self.tableWidget.raise_()

        self.pushButton = QtWidgets.QPushButton(self.centralWidget)
        self.pushButton.setGeometry(QtCore.QRect(90, 20, 75, 23))
        self.pushButton.setObjectName("pushButton")
        self.pushButton.setText("加载数据")

        # ----------- 修改人脸信息模块
        self.pushButton_edit = QtWidgets.QPushButton(self.centralWidget)
        self.pushButton_edit.setGeometry(QtCore.QRect(500, 350, 90, 43))
        self.pushButton_edit.setObjectName("pushButton")
        self.pushButton_edit.setText("修改人脸信息")

        self.label_1 = QtWidgets.QLabel(self.centralWidget)
        self.label_1.setGeometry(QtCore.QRect(500, 200, 150, 40))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setItalic(False)
        font.setWeight(40)
        self.label_1.setFont(font)
        self.label_1.setObjectName("label")
        self.label_1.setText('请输入需要修改信息的id')

        self.textEdit_1 = QtWidgets.QTextEdit(self.centralWidget)
        self.textEdit_1.setGeometry(QtCore.QRect(500, 300, 100, 30))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.textEdit_1.setFont(font)
        self.textEdit_1.setObjectName("textEdit_1")

        MainWindow.setCentralWidget(self.centralWidget)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        self.pushButton.clicked.connect(self.reload_date_mysql)
        self.pushButton_edit.clicked.connect(self.faceadd)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "管理人脸数据"))

    def reload_date_mysql(self):
        sql = 'select * from student'
        input_table = pd.read_sql(sql, engine)
        input_table_rows = input_table.shape[0]
        input_table_colunms = input_table.shape[1]
        input_table_header = input_table.columns.values.tolist()
        self.tableWidget.setColumnCount(input_table_colunms)
        self.tableWidget.setRowCount(input_table_rows)
        self.tableWidget.setHorizontalHeaderLabels(input_table_header)
        for i in range(input_table_rows):
            input_table_rows_values = input_table.iloc[[i]]
            input_table_rows_values_array = np.array(input_table_rows_values)
            input_table_rows_values_list = input_table_rows_values_array.tolist()[0]
            for j in range(input_table_colunms):
                input_table_items_list = input_table_rows_values_list[j]
                ###==============将遍历的元素添加到tablewidget中并显示=======================

                input_table_items = str(input_table_items_list)
                newItem = QTableWidgetItem(input_table_items)
                newItem.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
                self.tableWidget.setItem(i, j, newItem)
                ###================遍历表格每个元素，同时添加到tablewidget中========================

    def faceadd(self):
        self.id_adm = self.textEdit_1.toPlainText()
        sql = "select * from student where id='" + str(self.id_adm) + "'"
        input_table = pd.read_sql(sql, engine)
        self.namepre = input_table.iloc[0, 1]
        self.imgpre = input_table.iloc[0, 2]
        self.balancepre = input_table.iloc[0, 3]

        import addface  # 这个是可以单独运行的窗口
        self.addface = addface.Ui_MainWindow()
        self.addface.show()
        self.photoIs = False  # 拍照关键词
        self.addface.textEdit_1.setText(self.namepre)
        self.addface.textEdit_2.setText(str(self.balancepre))
        self.addface.pushButton_3.clicked.connect(self.openCamera)
        self.addface.pushButton_4.clicked.connect(self.changePhotoStatus)

    def changePhotoStatus(self):
        self.photoIs = True

    # 拍照
    def openCamera(self):
        QtWidgets.QApplication.processEvents()  # 刷新
        capture = cv2.VideoCapture(0)

        while (True):
            # 读取某一帧
            ref, frame = capture.read()  # ref是判断摄像头的是否被打开，frame表示摄像头读取的图像矩阵mat类型
            show = cv2.resize(frame, (640, 480))
            show = cv2.cvtColor(show, cv2.COLOR_BGR2RGB)
            showImage = QtGui.QImage(show.data, show.shape[1], show.shape[0], show.shape[1] * 3,
                                     QtGui.QImage.Format_RGB888)
            self.addface.label_show.setPixmap(QtGui.QPixmap.fromImage(showImage))

            QtWidgets.QApplication.processEvents()  # 刷新
            if self.photoIs:
                nameNew = self.addface.textEdit_1.toPlainText()
                balanceNew = self.addface.textEdit_2.toPlainText()
                img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                filename = 'face_map/' + nameNew + '.jpg'
                # cv2.imwrite(filename, img)
                cv2.imencode('.jpg', img)[1].tofile(filename)  # 解决中文乱码问题
                cur = conn.cursor()
                ql_up1 = "update student set balance = '" + str(balanceNew) + "' where id ='" + str(self.id_adm) + "'"
                ql_up2 = "update student set name = '" + str(nameNew) + "' where id ='" + str(self.id_adm) + "'"
                ql_up3 = "update student set img = '" + filename + "' where id ='" + str(self.id_adm) + "'"
                try:
                    cur.execute(ql_up1)
                    cur.execute(ql_up2)
                    cur.execute(ql_up3)
                    conn.commit()
                except:
                    print('插入数据库错误，插入语句如下：', ql_up3)
                cur.close()
                self.addface.label_7.setText('修改个人成功！！！')
                break

        capture.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
