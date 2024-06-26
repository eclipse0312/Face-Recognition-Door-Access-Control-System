import face_recognition
from scipy.spatial import distance as dist
import os

def eye_close_detection(face_landmarks, ear_threshold):
    # 获取左眼和右眼的坐标
    left_eye = face_landmarks[0]['left_eye']
    right_eye = face_landmarks[0]['right_eye']
    # 计算左眼和右眼的眼睛纵横比
    ear_left = get_ear(left_eye)
    ear_right = get_ear(right_eye)
    # 判断眼睛是否闭合
    if ear_left <= ear_threshold and ear_right <= ear_threshold:
        return True
    else:
        return False

def get_ear(eye):
    # 计算眼睛纵横比
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

def find_main_face(face_locations):
    # 找到图像中面积最大的脸
    max_area = 0
    max_face = face_locations[0]
    max_face_location = []
    for face in face_locations:
        area = abs((face[0] - face[2]) * (face[1] - face[3]))
        if area > max_area:
            max_area = area
            max_face = face
    max_face_location.append(max_face)
    return max_face_location

def recognition(known_face_encodings, main_face_encoding):
    # 人脸匹配，返回对应的名字的下标
    matches = face_recognition.compare_faces(known_face_encodings, main_face_encoding[0])
    if True in matches:
        index = matches.index(True)
        return index
    else:
        return None

def mouth_open_detection(face_landmarks, mar_threshold):
    # 获取嘴巴的坐标
    mouth = face_landmarks[0]['mouth']
    # 计算嘴巴纵横比
    mouth_mar = get_mar(mouth)
    # 判断嘴巴是否张开
    if mouth_mar >= mar_threshold:
        return True
    else:
        return False

def get_mar(mouth):
    # 计算嘴巴纵横比
    A = dist.euclidean(mouth[2], mouth[10])
    B = dist.euclidean(mouth[4], mouth[8])
    C = dist.euclidean(mouth[0], mouth[6])
    mar = (A + B) / (2.0 * C)
    return mar

def load_known_persons(path):
    # 从文件夹中加载图片
    known_faces_encodings = []
    known_faces_names = []
    for roots, dirs, files in os.walk(path):
        for file in files:
            file_fullname = os.path.join(roots, file)
            img = face_recognition.load_image_file(file_fullname)
            face_encoding = face_recognition.face_encodings(img)[0]
            known_faces_encodings.append(face_encoding)
            name = file.split('.')[0]
            known_faces_names.append(name)
    return known_faces_encodings, known_faces_names