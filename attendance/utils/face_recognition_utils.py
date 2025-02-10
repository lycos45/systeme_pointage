from deepface import DeepFace
import numpy as np
from scipy.spatial.distance import cosine

def detect_faces(image):
    """
    Détecte les visages dans une image.
    :param image: Image au format PIL.
    :return: Liste des coordonnées des visages détectés.
    """
    # Convertir l'image PIL en tableau numpy
    image_np = np.array(image)
    
    # Détecter les visages avec DeepFace
    try:
        faces = DeepFace.extract_faces(img_path=image_np, detector_backend='mtcnn')
        return [face['facial_area'] for face in faces]
    except ValueError:
        return []

def extract_face_descriptor(image):
    """
    Extrait le descripteur facial d'une image.
    :param image: Image au format PIL.
    :return: Descripteur facial (vecteur numpy) ou None si aucun visage n'est détecté.
    """
    # Convertir l'image PIL en tableau numpy
    image_np = np.array(image)
    
    # Extraire le descripteur facial avec DeepFace
    try:
        descriptor = DeepFace.represent(img_path=image_np, model_name='Facenet', detector_backend='mtcnn')
        return np.array(descriptor[0]['embedding'])
    except ValueError:
        return None

def compare_descriptors(desc1, desc2, threshold=0.5):
    """
    Compare deux descripteurs faciaux.
    :param desc1: Premier descripteur facial.
    :param desc2: Deuxième descripteur facial.
    :param threshold: Seuil de similarité (par défaut 0.5).
    :return: True si les descripteurs correspondent, False sinon.
    """
    if desc1 is None or desc2 is None:
        return False
    distance = cosine(desc1, desc2)
    return distance < threshold