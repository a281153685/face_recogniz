# 人脸识别系统PyQt

> 这个版本是基于mysql数据库系统做的，里面含有一个dlib人脸识别库，还有一个基于vgg人脸分类的模型，其中人脸相似度比较是用余弦相似度计算的，
> 这里面的数据库结构很简单，使用的是student表-studentface库  

> 表结构含有：《id, name, img, balance》 

> balance字段是为了之前的一个项目，刷一次人脸就实现扣费操作这个之后可以做自由改动。

> vgg网络模型太大了，所以我把vgg的网络参数存在了阿里云盘，云盘链接为：
> https://www.aliyundrive.com/s/nJuMDJ7nT2n