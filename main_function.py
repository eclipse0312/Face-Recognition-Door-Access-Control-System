import os, cv2, time, sys, sub_functions, mysql.connector, numpy as np, face_recognition as fr, pygame, smtplib, serial, binascii, string

from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel
from PyQt5.QtCore import QThread, pyqtSignal, QRect, QCoreApplication
from PyQt5.QtGui import QImage, QPixmap
from datetime import datetime, timedelta
from mysql.connector import Error
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders


class FaceRecognitionThread(QThread):
    recognitionResult = pyqtSignal(str)
    frameReady = pyqtSignal(np.ndarray)
    blinkCountReady = pyqtSignal(int)
    mouthOpenCountReady = pyqtSignal(int)
    loopCountReady = pyqtSignal(int)
    personRecognition = pyqtSignal(str)
    passRecognition = pyqtSignal(str)
    passTimeReady = pyqtSignal(str)
    violationEventDetected = pyqtSignal(str)  # 添加一个新的信号用于发出违规事件信息
    screenshotReady = pyqtSignal(str)
    passUserDetected = pyqtSignal(str)
    similarityReady = pyqtSignal(float)  # 新的信号，用于发送相似度信息######################################

    def __init__(self):
        super().__init__()
        self.is_running = True
        self.total_blinks = 0  # 眨眼总数
        self.total_mouth_open = 0  # 张嘴总数
        self.loop_count = 0  # 用于记录循环次数
        self.attempt_count = 0  # 添加一个尝试次数的计数器
        self.audio_path = "your_path"  # 音频文件路径


        # 初始化串口通信，如果没有继电器模块，那么可删除相关代码
        self.serialPort = "COM3"  # 串口号
        self.baudRate = 9600  # 波特率
        self.s = serial.Serial(self.serialPort, self.baudRate, timeout=0.5)
        print("串口已打开：", self.serialPort)
        self.control_door_lock("关门")

        try:
            # 建立数据库连接
            self.connection = mysql.connector.connect(
                host='localhost',
                database='user_database',
                user='your_user',
                password='your_password'
            )
            print("数据库连接已建立：", self.connection.is_connected())
            self.cursor = self.connection.cursor()
        except Error as e:
            print("数据库连接失败：", e)

    def run(self):
        print("人脸识别线程已启动")
        ear_threshold = 0.25  # 眼睛闭合的阈值
        mar_threshold = 0.65  # 嘴巴张开的阈值

        img_path = "your_avatars"  # 创建你的avatars文件——人脸照片的路径

        # 加载已知人脸的照片并进行编码
        known_faces_encodings, known_faces_names = sub_functions.load_known_persons(img_path)

        last_name = None
        last_person = None

        video_capture = cv2.VideoCapture(0)  # 打开摄像头
        print("视频捕获已打开")
        try:
            while self.is_running:
                ret, frame = video_capture.read()  # 读取视频流中的一帧
                print("已读取帧")
                if not ret:
                    break

                # 发射信号，将帧传递给主界面
                self.frameReady.emit(frame)

                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # 将BGR格式转换为RGB格式
                print("帧转换为RGB")
                gray_frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2GRAY)  # 灰度化
                equalized_frame = cv2.equalizeHist(gray_frame)  # 直方图均衡化
                rgb_frame = cv2.cvtColor(equalized_frame, cv2.COLOR_GRAY2RGB)  # 将灰度图转换回RGB格式，以便进行人脸识别

                face_locations = fr.face_locations(rgb_frame)  # 检测人脸位置
                print("已检测到人脸位置")

                if len(face_locations) == 0:  # 若未检测到人脸，则跳过本次循环
                    # 重置眨眼总数和张嘴总数
                    self.total_blinks = 0
                    self.total_mouth_open = 0
                    self.recognitionResult.emit("未检测到人脸")  # 发射识别结果信号，设置名字为未知
                    self.passRecognition.emit("未知")  # 发射放行信号，恢复为未知
                    self.blinkCountReady.emit(self.total_blinks)  # 发射眨眼总数信号
                    self.mouthOpenCountReady.emit(self.total_mouth_open)  # 发射张嘴总数信号
                    continue

                main_face_location = sub_functions.find_main_face(face_locations)  # 找出主要的人脸位置

                print("找到主要人脸位置")

                main_face_landmarks = fr.face_landmarks_2(rgb_frame, main_face_location)  # 获取主要人脸的特征点
                print("已检测到主要人脸的特征点")

                main_face_encoding = fr.face_encodings(rgb_frame, main_face_location)  # 获取主要人脸的编码
                if main_face_encoding:
                    face_distances = fr.face_distance(known_faces_encodings, main_face_encoding[0])
                    best_match_index = np.argmin(face_distances)
                    similarity = 1 - face_distances[best_match_index]
                    self.similarityReady.emit(similarity)

                    similarity_threshold = 0.4  # 设置合理的相似度阈值
                    if face_distances[best_match_index] < similarity_threshold:
                        name_student_id = known_faces_names[best_match_index]
                    else:
                        name_student_id = "未知"
                else:
                    name_student_id = "未知"
                    similarity = 0
                    self.similarityReady.emit(similarity)

                self.recognitionResult.emit(name_student_id)
                print("人脸识别完成:", name_student_id)

                # 如果识别到的人脸名字是未知，增加尝试次数
                if name_student_id == "未知":
                    self.attempt_count += 1
                else:
                    # 如果识别到的人脸名字不是未知，重置尝试次数
                    self.attempt_count = 0

                if self.attempt_count > 5:
                    print("违规事件：连续多次尝试通过门禁失败")
                    self.attempt_count = 0
                    screenshot_path = self.save_screenshot(frame)
                    if screenshot_path:
                        message = "警告！！！违规事件：连续多次尝试通过门禁失败。截屏已保存：{}".format(screenshot_path)
                        self.violationEventDetected.emit(message)
                        # 发送邮件并附带截屏照片
                        self.send_email(screenshot_path)
                        # 播放警报声音
                        pygame.mixer.init()
                        pygame.mixer.music.load(self.audio_path)  # 加载警报声音文件
                        pygame.mixer.music.play()

                # 活体检测
                if sub_functions.eye_close_detection(main_face_landmarks, ear_threshold):
                    self.total_blinks += 1  # 更新眨眼总数
                if sub_functions.mouth_open_detection(main_face_landmarks, mar_threshold):
                    self.total_mouth_open += 1  # 更新张嘴总数

                print("眨眼总数:", self.total_blinks)
                print("张嘴总数:", self.total_mouth_open)

                self.blinkCountReady.emit(self.total_blinks)  # 发射眨眼总数信号
                self.mouthOpenCountReady.emit(self.total_mouth_open)  # 发射张嘴总数信号

                # 活体检测结果
                if self.total_blinks >= 1 and self.total_mouth_open >= 1:
                    person = "真人"
                else:
                    person = "假人"

                print("活体检测结果:", person)

                if person == "真人" and person == last_person:
                    self.loop_count += 1  # 更新循环次数

                print("循环次数:", self.loop_count)

                last_person = person  # 更新上一次的活体检测结果

                if name_student_id != last_name:  # 如果新的人脸的名字和上一次识别到的人脸的名字不同
                    self.total_blinks = 0  # 重置眨眼次数
                    self.total_mouth_open = 0  # 重置张嘴次数
                    self.passRecognition.emit("未知")  # 发射放行信号，恢复为未知

                if name_student_id != last_name or name_student_id == "未知" or person == "假人":
                    self.loop_count = 0  # 重置循环次数

                last_name = name_student_id  # 更新上一次识别到的人脸的名字

                if self.loop_count == 4 and name_student_id != "未知" and person == "真人":
                    user_type = self.get_user_type(name_student_id)
                    print("用户类型:", user_type)
                    if user_type == "访客":
                        if self.check_recent_admin_pass():
                            self.passRecognition.emit("访客已通过，可以放行")
                            self.passUserDetected.emit(name_student_id)
                            self.control_door_lock("开锁")
                        else:
                            self.passRecognition.emit("访客未通过，等待负责人")
                            screenshot_path = self.save_screenshot(frame)
                            if screenshot_path:
                                message = "警告！！！违规事件：连续多次尝试通过门禁失败。截屏已保存：{}".format(screenshot_path)
                                self.violationEventDetected.emit(message)
                                self.send_email(screenshot_path)
                                pygame.mixer.init()
                                pygame.mixer.music.load(self.audio_path)
                                pygame.mixer.music.play()
                    else:
                        self.passRecognition.emit("已通过，可以放行")
                        self.passUserDetected.emit(name_student_id)
                        self.control_door_lock("开锁")

                # 如果循环次数达到5次，显示通过时间
                if self.loop_count == 5:
                    pass_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                    self.passTimeReady.emit(pass_time)

                # 更新循环次数的页面显示
                self.loopCountReady.emit(self.loop_count)

                # 更新界面显示活体检测结果
                self.personRecognition.emit(person)

        finally:
            video_capture.release()  # 释放摄像头资源
            cv2.destroyAllWindows()  # 关闭所有OpenCV窗口
            print("视频捕获已释放")

    def get_user_type(self, name_student_id):
        """
        获取用户类型的方法
        :param name_student_id: 姓名和学号的组合字符串
        :return: 用户类型，如果未找到用户则返回 None
        """
        self.ensure_db_connection()  # 确保数据库连接
        if hasattr(self, 'connection') and self.connection.is_connected():
            try:
                query = "SELECT type FROM user_data WHERE CONCAT(name, '_', student_id) = %s"
                self.cursor.execute(query, (name_student_id,))
                user_type = self.cursor.fetchone()
                if user_type:
                    return user_type[0]
                else:
                    return None
            except Exception as e:
                print("获取用户类型时出错：", e)
                return None
        else:
            print("数据库未连接或连接失败，无法获取用户类型")
            return None

    def check_recent_admin_pass(self):
        """
        检查最近3分钟内是否有负责人通过
        :return: 如果有负责人通过返回 True，否则返回 False
        """
        self.ensure_db_connection()  # 确保数据库连接
        if hasattr(self, 'connection') and self.connection.is_connected():
            try:
                query = """
                SELECT COUNT(*) FROM pass_users
                WHERE type = '负责人' AND pass_time >= NOW() - INTERVAL 3 MINUTE
                """
                self.cursor.execute(query)
                result = self.cursor.fetchone()
                if result and result[0] > 0:
                    return True
                else:
                    return False
            except Exception as e:
                print("检查最近负责人通过时出错：", e)
                return False
        else:
            print("数据库未连接或连接失败，无法检查最近负责人通过")
            return False


    def control_door_lock(self, command):
        """
        控制门锁开关状态
        """
        if command == "关门":
            data = [0xA0, 0x01, 0x01]
        elif command == "开锁":
            data = [0xA0, 0x01, 0x00]
        else:
            print("无效命令")
            return

        checksum = sum(data) & 0xFF
        data.append(checksum)
        d = bytes(data)
        self.s.write(d)
        print(f"发送指令: {binascii.hexlify(d)}")

        # 如果是开锁命令，延时5秒后发送关门命令
        if command == "开锁":
            time.sleep(5)
            self.control_door_lock("关门")

    def save_screenshot(self, frame):
        try:
            screenshot_path = "your_violation_events"   #建立你的violation_events文件，输入你的文件路径
            filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".jpg"
            full_path = os.path.join(screenshot_path, filename)

            cv2.imwrite(full_path, frame)
            print("截屏已保存：", full_path)  # 添加此行用于调试
            self.screenshotReady.emit(full_path)  # 发射截图路径信号
            return full_path
        except Exception as e:
            print("保存截屏时出错：", e)
            return None

    def send_email(self, screenshot_path):
        # 设置发件人、收件人、邮件内容
        sender_email = "accesscontrol_email"
        receiver_email = "your_email"
        password = "your_password"
        subject = "违规事件警报"
        body = "警告：门禁系统检测到异常行为。连续多次尝试通过门禁失败，请立即查看。"

        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        # 添加截屏照片作为附件
        if screenshot_path:
            try:
                with open(screenshot_path, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename= {os.path.basename(screenshot_path)}",
                )
                message.attach(part)
            except Exception as e:
                print("添加附件时出错:", e)

        server = None  # 初始化 server 变量

        # 连接到 SMTP 服务器并发送邮件
        try:
            server = smtplib.SMTP("smtp.126.com", 25)
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
            print("邮件发送成功")
        except Exception as e:
            print("邮件发送失败:", e)
        finally:
            if server:
                server.quit()


    def stop(self):
        self.is_running = False


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.title = 'PyQt5 Face Recognition'
        self.initUI()
        self.center()  # 将窗口放置在屏幕中央
        self.connect_to_database()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(10, 10, 1280, 720)

        self.label = QLabel(self)
        self.label.move(150, 20)
        self.label.setText("姓名: 未知             ")

        self.person_label = QLabel(self)
        self.person_label.move(150, 50)
        self.person_label.setText("识别: 未知")

        self.blink_label = QLabel(self)  # 添加用于显示眨眼次数的标签
        self.blink_label.move(150, 80)
        self.blink_label.setText("眨眼次数: 0")

        self.mouth_label = QLabel(self)  # 添加用于显示张嘴次数的标签
        self.mouth_label.move(150, 110)
        self.mouth_label.setText("张嘴次数: 0")

        self.pass_label = QLabel(self)  # 显示放行状态
        self.pass_label.move(300, 80)
        self.pass_label.setText("状态: 未知                 ")

        self.pass_time_label = QLabel(self)
        self.pass_time_label.move(300, 110)
        self.pass_time_label.setText("通过时间: 未知                  ")

        self.similarity_label = QLabel(
            self)  # 添加用于显示相似度的标签############################################################################
        self.similarity_label.move(300, 50)
        self.similarity_label.setText("相似度:                         ")

        self.violation_label = QLabel(self)  # 添加用于显示违规事件的标签
        self.violation_label.move(450, 110)  # 设置违规事件标签的位置
        self.violation_label.setText("                                          ")  # 设置初始文本
        self.violation_label.setStyleSheet("color: red")  # 设置文本颜色为红色

        self.video_label = QLabel(self)  # 添加用于显示视频的标签
        self.video_label.setGeometry(20, 140, 1200, 800)  # 设置视频标签的位置和大小

        start_button = QPushButton('开始人脸识别', self)
        start_button.setToolTip('点击开始人脸识别')
        start_button.setGeometry(800, 50, 250, 30)  # 设置按钮的位置和大小
        start_button.clicked.connect(self.on_click)

        self.stop_button = QPushButton('停止人脸识别', self)
        self.stop_button.setToolTip('点击停止人脸识别')
        self.stop_button.setGeometry(800, 90, 250, 30)  # 设置按钮的位置和大小
        self.stop_button.clicked.connect(self.stop_face_recognition)
        self.stop_button.setEnabled(False)  # 初始时，停止按钮是禁用的

        self.show()

    def on_click(self):
        self.face_recognition_thread = FaceRecognitionThread()
        self.face_recognition_thread.recognitionResult.connect(self.update_label)
        self.face_recognition_thread.personRecognition.connect(self.update_person_label)
        self.face_recognition_thread.frameReady.connect(self.update_video_label)  # 连接帧信号
        self.face_recognition_thread.blinkCountReady.connect(self.update_blink_label)  # 连接眨眼次数信号
        self.face_recognition_thread.mouthOpenCountReady.connect(self.update_mouth_label)  # 连接张嘴次数信号
        self.face_recognition_thread.passRecognition.connect(self.update_pass_label)  # 连接放行状态信号
        self.face_recognition_thread.passTimeReady.connect(self.update_pass_time_label)  # 连接人通过时间信号
        self.face_recognition_thread.passUserDetected.connect(self.save_pass_user_info)
        self.face_recognition_thread.violationEventDetected.connect(self.show_violation_event)  # 连接违规事件信号到显示违规事件的槽函数
        self.face_recognition_thread.screenshotReady.connect(self.save_violation_info_to_database)  # 连接截图路径信号
        self.face_recognition_thread.similarityReady.connect(
            self.update_similarity_label)  # 连接相似度信号并更新相似度标签##################
        #######################################

        self.face_recognition_thread.start()
        self.stop_button.setEnabled(True)  # 当人脸识别开始时，启用停止按钮

    def connect_to_database(self):
        try:
            self.connection = mysql.connector.connect(
                host='localhost',
                database='user_database',
                user='your_user',
                password='your_password'
            )
            if self.connection.is_connected():
                self.cursor = self.connection.cursor()
                print("数据库连接成功")
            else:
                print("数据库连接失败")
        except Error as e:
            print("数据库连接失败：", e)

    def update_pass_user_info(self, name_student_id, pass_time):
        if hasattr(self, 'connection') and self.connection.is_connected():
            try:
                # 查询符合条件的用户信息，并且离开时间为 "未离开"
                query = "SELECT * FROM pass_users WHERE CONCAT(name, '_', student_id) = %s AND DATE(pass_time) = CURDATE() AND leave_time = '未离开'"
                self.cursor.execute(query, (name_student_id,))
                user_data = self.cursor.fetchall()
                print("用户信息：", user_data)

                if user_data:  # 检查是否有符合条件的用户数据
                    # 获取用户信息中的第一条数据（通常只会有一条符合条件的数据）
                    user_info = user_data[0]
                    # 计算离开时间和停留时间
                    leave_time = pass_time
                    pass_time_dt = datetime.strptime(user_info[9], "%Y-%m-%d %H:%M:%S")
                    stay_time = leave_time - pass_time_dt

                    # 将 leave_time 和 stay_time 转换为字符串形式，只包含秒
                    leave_time_str = leave_time.strftime("%Y-%m-%d %H:%M:%S")

                    # 将 stay_time 转换为时分秒的形式
                    total_seconds = stay_time.total_seconds()
                    hours = int(total_seconds // 3600)
                    minutes = int((total_seconds % 3600) // 60)
                    seconds = int(total_seconds % 60)
                    stay_time_str = "{:02}时{:02}分{:02}秒".format(hours, minutes, seconds)

                    # 更新数据库中的 leave_time 和 stay_time 字段
                    update_query = "UPDATE pass_users SET leave_time = %s, stay_time = %s WHERE CONCAT(name, '_', student_id) = %s AND leave_time = '未离开'"
                    self.cursor.execute(update_query, (leave_time_str, stay_time_str, name_student_id))
                    self.connection.commit()

                    print("用户信息已更新：离开时间和停留时间")

                else:
                    # 如果没有符合条件的用户数据，则插入新的用户信息
                    user_query = "SELECT * FROM user_data WHERE CONCAT(name, '_', student_id) = %s"
                    self.cursor.execute(user_query, (name_student_id,))
                    user_data = self.cursor.fetchall()

                    if user_data:
                        insert_query = "INSERT INTO pass_users (name, gender, student_id, type, email, team, phone, college, grade, pass_time, leave_time, stay_time) " \
                                       "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                        pass_user_data = (user_data[0][1], user_data[0][2], user_data[0][3], user_data[0][4],
                                          user_data[0][5], user_data[0][6], user_data[0][7], user_data[0][8],
                                          user_data[0][9], pass_time.strftime("%Y-%m-%d %H:%M:%S"), "未离开", "未离开")
                        self.cursor.execute(insert_query, pass_user_data)
                        self.connection.commit()
                        print("新用户信息已保存到 pass_users 表格中")

            except Exception as e:
                print("更新用户信息时出错：", e)
        else:
            print("数据库未连接或连接失败，无法更新用户信息")

    def save_pass_user_info(self, name_student_id):
        if hasattr(self, 'connection') and self.connection.is_connected():
            try:
                query = "SELECT * FROM user_data WHERE CONCAT(name, '_', student_id) = %s"
                self.cursor.execute(query, (name_student_id,))
                user_data = self.cursor.fetchone()

                if user_data:
                    pass_time = datetime.now()  # 获取当前时间
                    self.update_pass_user_info(name_student_id, pass_time)  # 更新用户信息

            except Exception as e:
                print("保存通过用户信息时出错：", e)
        else:
            print("数据库未连接或连接失败，无法保存通过用户信息")

    def save_violation_info_to_database(self, screenshot_path):
        try:
            if hasattr(self, 'connection') and self.connection.is_connected():
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                query = "INSERT INTO violation_events (time, picture_path) VALUES (%s, %s)"
                self.cursor.execute(query, (current_time, screenshot_path))
                self.connection.commit()
                print("违规信息已保存到数据库")
            else:
                print("数据库未连接或连接失败，无法保存违规信息")
        except Error as e:
            print("保存违规信息到数据库时出错：", e)

    def stop_face_recognition(self):
        self.face_recognition_thread.stop()  # 停止人脸识别线程
        self.stop_button.setEnabled(False)  # 当人脸识别停止时，禁用停止按钮

    def update_label(self, name_student_id):
        self.label.setText("姓名：" + str(name_student_id))
        if name_student_id == "未检测到人脸" or "未知":
            self.pass_label.setText("状态: 未知")
            self.blink_label.setText("眨眼次数: 0")
            self.mouth_label.setText("张嘴次数: 0")
            self.pass_time_label.setText("通过时间：")
            self.violation_label.setText("")  # 清空违规事件标签的文本
        else:
            if self.face_recognition_thread.loop_count == 5:
                self.save_pass_user_info(name_student_id)  # 在识别到人脸后调用保存通过用户信息的方法
        QApplication.processEvents()

    def update_person_label(self, person):
        self.person_label.setText("识别：" + str(person))

    def update_blink_label(self, count):
        self.blink_label.setText("眨眼次数: " + str(count))

    def update_mouth_label(self, count):
        self.mouth_label.setText("张嘴次数: " + str(count))

    def update_pass_label(self, status):
        self.pass_label.setText("状态: " + status)  # 更新放行状态标签

    def update_pass_time_label(self, pass_time):
        self.pass_time_label.setText("通过时间：" + pass_time)

    def update_similarity_label(self, similarity):
        self.similarity_label.setText(
            "相似度: {:.2f}".format(similarity))  # 更新相似度标签的方法###################################################

    def show_violation_event(self, event_info):
        self.violation_label.setText(event_info)  # 更新违规事件标签的文本为触发的违规事件信息

    def update_video_label(self, frame):
        # 将帧转换为Qt格式的图像
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytesPerLine = ch * w
        convertToQtFormat = QImage(frame.data, w, h, bytesPerLine, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(convertToQtFormat)

        # 在视频标签上显示图像
        self.video_label.setPixmap(pixmap)
        self.video_label.setScaledContents(True)

    def center(self):
        screen = QCoreApplication.instance().desktop().screenGeometry()  # 获取屏幕的尺寸
        size = self.geometry()  # 获取窗口的尺寸
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)  # 将窗口移动到屏幕中央


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
