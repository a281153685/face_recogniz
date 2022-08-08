# -*- coding: utf-8 -*-

"""
    @Author  : Mumu
    @Time    : 2022/8/6 14:35
    @Function:

"""
import sys
import pymysql
from PyQt5.QtWidgets import QApplication, QMainWindow
import mainWindow
from mainWindow import *
import pandas as pd
import cv2
import numpy as np
import dlib
from face import loadVggFaceModel, create_face_mysql_dict, findCosineSimilarity, queryPersonInfoMysql
from time import sleep
from sqlalchemy import create_engine

paths = []
result = []
engine = create_engine('mysql+pymysql://root:hzt123@localhost:3306/studentface')
conn = pymysql.connect(host='localhost',
                       user='root',
                       password='hzt123',
                       database='studentface',
                       port=3306,
                       charset='utf8')

# 定义面部正面探测器
detector = dlib.get_frontal_face_detector()
margin = 0.2  # 边距比例
face_h, face_w = 224, 224  # 模型输入的头像大小
mydb = pymysql.Connect(host="localhost", user="root", password="hzt123", database="studentface")


class MyWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent)
        self.setupUi(self)

    def add_info(self):
        studentid = ui.textEdit_1.toPlainText()
        name = ui.textEdit_2.toPlainText()
        major = ui.textEdit_3.toPlainText()
        roomNumber = ui.textEdit_4.toPlainText()
        personDir = ui.textEdit_5.toPlainText()
        sql_dict = {'studentid': studentid,
                    'name': name,
                    'major': major,
                    'roomNumber': roomNumber,
                    'personDir': personDir,
                    }
        sql_df = pd.DataFrame(sql_dict, index=[0])
        pd.io.sql.to_sql(sql_df, 'student', if_exists='append', con=engine, index=False)
        print('ok')

    def del_info(self):
        name = ui.textEdit_6.toPlainText()
        mycursor = mydb.cursor()
        sql = "DELETE FROM student WHERE name = '{}'".format(name)
        try:
            mycursor.execute(sql)
            mydb.commit()
            print('del ok')
        except:
            print('数据库错误')
            mydb.rollback()

    def run_exe(self, is_camera=False):
        self.textEdit.setHtml("<font color='red' size='5'><red>{}</font>".format("系统初始化中...请稍等!"))
        QtWidgets.QApplication.processEvents()  # 刷新
        model = loadVggFaceModel()  # 加载人脸识别模型
        all_people_faces = create_face_mysql_dict()  # 获取人脸底库
        sql = 'select * from student'
        df = pd.read_sql(sql, engine)
        capture = cv2.VideoCapture(0)
        fps = 0.0
        num = 0
        pre_name = ""
        while (True):
            # 读取某一帧
            ref, frame = capture.read()  # ref是判断摄像头的是否被打开，frame表示摄像头读取的图像矩阵mat类型
            if frame is None:
                break
            data_info = ""
            found = 0
            num = num + 1
            if num % 10 == 0:
                input_img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_h, frame_w, _ = np.shape(input_img)  # 帧图像大小
                detected = detector(input_img, 1)  # 对当前帧检测
                if len(detected) > 0:  # 提取当前帧探测的所有脸部图像，构建预测数据集
                    for i, d in enumerate(detected):  # 枚举脸部对象
                        # 脸部坐标
                        x1, y1, x2, y2, w, h = d.left(), d.top(), d.right() + 1, d.bottom() + 1, d.width(), d.height()
                        # 带边距的坐标
                        xw1 = max(int(x1 - margin * w), 0)
                        yw1 = max(int(y1 - margin * h), 0)
                        xw2 = min(int(x2 + margin * w), frame_w - 1)
                        yw2 = min(int(y2 + margin * h), frame_h - 1)
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)  # 绘制边界框
                        face = input_img[yw1:yw2 + 1, xw1:xw2 + 1, :]  # 脸部的边界（含边距）
                        face = cv2.resize(face, (face_h, face_w))  # 脸部缩放，以适合模型需要的输入维度
                        face = face.astype("float") / 255.0  # 图像归一化
                        face = np.expand_dims(face, axis=0)  # 扩充维度，变为四维（1，face_h,face_w,3）
                        captured_representation = model.predict(face)[0]
                        # 与人脸底库进行对比
                        for i in all_people_faces:
                            person_name = i.rsplit("_", 1)[0]
                            representation = all_people_faces[i]
                            similarity = findCosineSimilarity(representation, captured_representation)
                            print(similarity)
                            if (similarity > 0.7):
                                if pre_name != person_name:  # 两次识别出同一个人
                                    pre_name = person_name
                                    # break
                                else:
                                    pre_name = person_name
                                print('识别出来的人为：', pre_name)
                                text_people = 'people'
                                cv2.putText(frame, text_people, (d.left(), d.top() - 10), cv2.FONT_HERSHEY_SIMPLEX,
                                            1.2,
                                            (255, 255, 0), 3)
                                data_info = queryPersonInfoMysql(person_name, df)
                                # print(data_info)
                                found = 1
                                # break
                                if (found == 0):  # 识别失败
                                    cv2.putText(frame, 'unknown', (d.left(), d.top() - 10), cv2.FONT_HERSHEY_SIMPLEX,
                                                1.2,
                                                (255, 255, 0), 3)

            # 显示结果到主界面
            self.textEdit.setHtml(
                "<font color='red' size='5'><red>{}</font>".format(data_info))  # 显示人员信息
            # self.textEdit.setPlainText(data_info)

            show = cv2.resize(frame, (640, 480))
            show = cv2.cvtColor(show, cv2.COLOR_BGR2RGB)
            showImage = QtGui.QImage(show.data, show.shape[1], show.shape[0], show.shape[1] * 3,
                                     QtGui.QImage.Format_RGB888)
            self.label_show.setPixmap(QtGui.QPixmap.fromImage(showImage))
            QtWidgets.QApplication.processEvents()  # 刷新

            if (found == 1):
                sleep(3)  # 识别出人员之后，等待10秒再进行后续识别

        capture.release()
        cv2.destroyAllWindows()

    def faceadd(self):
        import addface  # 这个是可以单独运行的窗口
        self.addface = addface.Ui_MainWindow()
        self.addface.show()
        self.photoIs = False  # 拍照关键词
        self.addface.pushButton_3.clicked.connect(self.openCamera)
        self.addface.pushButton_4.clicked.connect(self.changePhotoStatus)

    def changePhotoStatus(self):
        self.photoIs = True

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
                name = self.addface.textEdit_1.toPlainText()
                balance = self.addface.textEdit_2.toPlainText()
                img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                filename = 'face_map/' + name + '.jpg'
                print('保存路径为：', filename)
                # cv2.imwrite(filename, img)
                cv2.imencode('.jpg', img)[1].tofile(filename)
                cur = conn.cursor()
                sql_insert = "insert into student(name, img, balance) values('" + name + "', '" + filename + "', '" + balance + "');"
                try:
                    cur.execute(sql_insert)
                    conn.commit()
                except:
                    print('插入数据库错误，插入语句如下：', sql_insert)
                cur.close()
                self.addface.label_7.setText('添加成功')
                break

        capture.release()
        cv2.destroyAllWindows()

    # 管理人脸信息界面
    def facemanage(self):
            import manageface  # 这个是可以单独运行的窗口
            self.manageface = manageface.Ui_MainWindow()
            self.manageface.show()

# def print_hi(name):
#     # 人脸识别模型提取特征
#     # t1 = time.time()
#     captured_representation = model.predict(face)[0]
#     # print("rec:{}".format(time.time() - t1))
#
#     # 与人脸底库进行对比
#     for i in all_people_faces:
#         person_name = i.rsplit("_", 1)[0]
#         representation = all_people_faces[i]
#         similarity = findCosineSimilarity(representation, captured_representation)
#         print(similarity)
#         if (similarity > 0.7):
#             if pre_name != person_name:  # 两次识别出同一个人
#                 pre_name = person_name
#                 # break
#             else:
#                 pre_name = person_name
#             print('识别出来的人为：', pre_name)
#             cv2.putText(frame, person_name[:], (d.left(), d.top() - 10), cv2.FONT_HERSHEY_SIMPLEX,
#                         1.2,
#                         (255, 255, 0), 3)
#             data_info = queryPersonInfoMysql(person_name, df)
#             # print(data_info)
#             found = 1
#             # break
#
#     if (found == 0):  # 识别失败
#         cv2.putText(frame, 'unknown', (d.left(), d.top() - 10), cv2.FONT_HERSHEY_SIMPLEX, 1.2,
#                     (255, 255, 0), 3)
#
#     # 显示结果到主界面
#     self.textEdit.setHtml("<font color='red' size='5'><red>{}</font>".format(data_info))  # 显示人员信息
#     # self.textEdit.setPlainText(data_info)
#
#     show = cv2.resize(frame, (640, 480))
#     show = cv2.cvtColor(show, cv2.COLOR_BGR2RGB)
#     showImage = QtGui.QImage(show.data, show.shape[1], show.shape[0], show.shape[1] * 3,
#                              QtGui.QImage.Format_RGB888)
#     self.label_show.setPixmap(QtGui.QPixmap.fromImage(showImage))
#     QtWidgets.QApplication.processEvents()  # 刷新
#
#     if (found == 1):
#         sleep(10)  # 识别出人员之后，等待10秒再进行后续识别
#
#     capture.release()
#     cv2.destroyAllWindows()
#
#     def faceadd(self):
#         import addface  # 这个是可以单独运行的窗口
#         self.addface = addface.Ui_MainWindow()
#         self.addface.show()
#         self.photoIs = False   # 拍照关键词
#         self.addface.pushButton_3.clicked.connect(self.openCamera)
#         self.addface.pushButton_4.clicked.connect(self.changePhotoStatus)
#
#     def changePhotoStatus(self):
#         self.photoIs = True
#
#     def openCamera(self):
#         QtWidgets.QApplication.processEvents()  # 刷新
#         capture = cv2.VideoCapture(0)
#         while (True):
#         # 读取某一帧
#             ref, frame = capture.read()  # ref是判断摄像头的是否被打开，frame表示摄像头读取的图像矩阵mat类型
#             show = cv2.resize(frame, (640, 480))
#             show = cv2.cvtColor(show, cv2.COLOR_BGR2RGB)
#             showImage = QtGui.QImage(show.data, show.shape[1], show.shape[0], show.shape[1] * 3, QtGui.QImage.Format_RGB888)
#             self.addface.label_show.setPixmap(QtGui.QPixmap.fromImage(showImage))
#             QtWidgets.QApplication.processEvents()  # 刷新
#
#             if self.photoIs:
#                 name = self.addface.textEdit_1.toPlainText()
#                 balance = self.addface.textEdit_2.toPlainText()
#                 img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#                 filename = 'face_map/' + name + '.jpg'
#                 print('保存路径为：', filename)
#                 # cv2.imwrite(filename, img)
#                 cv2.imencode('.jpg', img)[1].tofile(filename)
#                 cur = conn.cursor()
#                 sql_insert = "insert into student(name, img, balance) values('" + name + "', '" + filename + "', '" + balance + "');"
#                 try:
#                     cur.execute(sql_insert)
#                     conn.commit()
#                 except:
#                     print('插入数据库错误，插入语句如下：', sql_insert)
#                 cur.close()
#                 self.addface.label_7.setText('添加成功')
#                 break
#
#         capture.release()
#         cv2.destroyAllWindows()
#
#     # 管理人脸信息界面
#     def facemanage(self):
#         import manageface  # 这个是可以单独运行的窗口
#         self.manageface = manageface.Ui_MainWindow()
#         self.manageface.show()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    app = QApplication(sys.argv)
    MainWindow = QMainWindow()
    ui = MyWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    ui.pushButton_2.clicked.connect(ui.run_exe)
    ui.pushButton_3.clicked.connect(ui.faceadd)
    ui.pushButton_4.clicked.connect(ui.facemanage)
    sys.exit(app.exec_())

# See PyCharm help at https://www.jetbrains.com/help/pycharm/

