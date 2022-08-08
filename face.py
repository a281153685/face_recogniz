import numpy as np
import cv2
import pandas as pd
import pymysql
from sqlalchemy import create_engine
from tensorflow.keras.models import Model, Sequential
from tensorflow.keras.layers import Input, Convolution2D, ZeroPadding2D, MaxPool2D, Flatten, Dense, Dropout, Activation, \
    MaxPooling2D
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from tensorflow.keras.applications.imagenet_utils import preprocess_input
from tensorflow.keras.preprocessing import image
import matplotlib.pyplot as plt
from os import listdir


def loadVggFaceModel():
    """Loads the VGGFace model defined in the function"""
    model = Sequential()
    model.add(ZeroPadding2D((1, 1), input_shape=(224, 224, 3)))
    model.add(Convolution2D(64, (3, 3), activation='relu'))
    model.add(ZeroPadding2D((1, 1)))
    model.add(Convolution2D(64, (3, 3), activation='relu'))
    model.add(MaxPooling2D((2, 2), strides=(2, 2)))

    model.add(ZeroPadding2D((1, 1)))
    model.add(Convolution2D(128, (3, 3), activation='relu'))
    model.add(ZeroPadding2D((1, 1)))
    model.add(Convolution2D(128, (3, 3), activation='relu'))
    model.add(MaxPooling2D((2, 2), strides=(2, 2)))

    model.add(ZeroPadding2D((1, 1)))
    model.add(Convolution2D(256, (3, 3), activation='relu'))
    model.add(ZeroPadding2D((1, 1)))
    model.add(Convolution2D(256, (3, 3), activation='relu'))
    model.add(ZeroPadding2D((1, 1)))
    model.add(Convolution2D(256, (3, 3), activation='relu'))
    model.add(MaxPooling2D((2, 2), strides=(2, 2)))

    model.add(ZeroPadding2D((1, 1)))
    model.add(Convolution2D(512, (3, 3), activation='relu'))
    model.add(ZeroPadding2D((1, 1)))
    model.add(Convolution2D(512, (3, 3), activation='relu'))
    model.add(ZeroPadding2D((1, 1)))
    model.add(Convolution2D(512, (3, 3), activation='relu'))
    model.add(MaxPooling2D((2, 2), strides=(2, 2)))

    model.add(ZeroPadding2D((1, 1)))
    model.add(Convolution2D(512, (3, 3), activation='relu'))
    model.add(ZeroPadding2D((1, 1)))
    model.add(Convolution2D(512, (3, 3), activation='relu'))
    model.add(ZeroPadding2D((1, 1)))
    model.add(Convolution2D(512, (3, 3), activation='relu'))
    model.add(MaxPooling2D((2, 2), strides=(2, 2)))

    model.add(Convolution2D(4096, (7, 7), activation='relu'))
    model.add(Dropout(0.5))
    model.add(Convolution2D(4096, (1, 1), activation='relu'))
    model.add(Dropout(0.5))
    model.add(Convolution2D(2622, (1, 1)))  # 该模型用 2622 个人进行训练
    model.add(Flatten())
    model.add(Activation('softmax'))

    model.load_weights('vgg_face_weights.h5')

    vgg_face_descriptor = Model(inputs=model.layers[0].input, outputs=model.layers[-2].output)

    return vgg_face_descriptor


# 读取图像函数
def preprocess_image(image_path):
    """Loads image from path and resizes it"""
    img = load_img(image_path, target_size=(224, 224))
    img = img_to_array(img)
    img = np.expand_dims(img, axis=0)
    img = preprocess_input(img)
    return img


engine = create_engine('mysql+pymysql://root:hzt123@localhost:3306/studentface')


# 从数据库读取信息，然后进行相应的人脸特征提取，并生成人脸特征
def create_face_mysql_dict():
    all_people_faces = dict()  # 人脸底库特征字典
    model = loadVggFaceModel()
    sql = 'select * from student'
    df = pd.read_sql(sql, engine)
    for i in range(len(df)):
        fileName = df.iloc[i, -2].split('/')[1]
        person_face, extension = fileName.split(".")
        all_people_faces[person_face] = model.predict(preprocess_image(df.iloc[i, -2]))[0, :]
    print("人脸特征底库从数据库保存到数据字典成功！！")
    return all_people_faces


# 生成人脸底库
def create_face_dict():
    people_pictures = "./face_map/"  # 人脸底库文件夹

    all_people_faces = dict()  # 人脸底库特征字典

    model = loadVggFaceModel()

    for file in listdir(people_pictures):
        person_face, extension = file.split(".")
        # 提取特征加入字典
        all_people_faces[person_face] = model.predict(preprocess_image(people_pictures + "/" + file))[0, :]

    print("人脸特征底库保存到数据字典！！")
    return all_people_faces


# 计算余弦相似性函数
def findCosineSimilarity(source_representation, test_representation):
    a = np.matmul(np.transpose(source_representation), test_representation)
    b = np.sum(np.multiply(source_representation, source_representation))
    c = np.sum(np.multiply(test_representation, test_representation))
    return (a / (np.sqrt(b) * np.sqrt(c)))


database = 'studentface'
password = 'hzt123'
conn = pymysql.connect(host='localhost',
                       user='root',
                       password=password,
                       database=database,
                       port=3306,
                       charset='utf8')


def queryPersonInfoMysql(name, df):
    data_info = ""
    for i in range(df.shape[0]):  # 查找满足条件的行
        if name == df["name"].iloc[i]:
            id_ = df['id'].iloc[i]
            balance = df["balance"].iloc[i]  # 查出这个人的余额
            balance_new = balance - 10
            cur = conn.cursor()
            sql_insert = "update student set balance = '" + str(balance_new) + "' where id ='" + str(id_) + "'"
            try:
                cur.execute(sql_insert)
                conn.commit()
            except:
                print('插入数据库错误，插入语句如下：', sql_insert)
            cur.close()
            data_info = "根据最新数据库信息，查询到如下信息\n姓名: " + name + "\n 更新前余额为: " + str(balance) + "\n  更新后余额为：" + str(
                balance_new)
            break
    return data_info
