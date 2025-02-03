import face_recognition
import cv2

def capture_face():
    # Capture une image depuis la caméra
    video_capture = cv2.VideoCapture(0)
    ret, frame = video_capture.read()
    video_capture.release()

    # Détection des visages
    face_locations = face_recognition.face_locations(frame)
    if len(face_locations) == 0:
        raise ValueError("Aucun visage détecté.")
    
    # Générer un encodage
    face_encoding = face_recognition.face_encodings(frame, face_locations)[0]
    return face_encoding
