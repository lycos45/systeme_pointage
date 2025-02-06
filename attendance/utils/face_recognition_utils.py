from mtcnn import MTCNN
from facenet_pytorch import InceptionResnetV1
import torch
from PIL import Image
import numpy as np
from scipy.spatial.distance import cosine

# Charger les modèles
mtcnn = MTCNN()
resnet = InceptionResnetV1(pretrained='vggface2').eval()

def detect_faces(image):
    """
    Détecte les visages dans une image.
    :param image: Image au format PIL ou numpy array.
    :return: Liste des visages détectés.
    """
    faces = mtcnn.detect(image)
    return faces

def extract_face_descriptor(image):
    """
    Extrait le descripteur facial d'une image.
    :param image: Image au format PIL ou numpy array.
    :return: Descripteur facial (vecteur numpy) ou None si aucun visage n'est détecté.
    """
    face = mtcnn(image)  # Détecter et aligner le visage
    if face is not None:
        face = face.unsqueeze(0)  # Ajouter une dimension de batch
        descriptor = resnet(face)  # Extraire le descripteur
        return descriptor.detach().numpy()
    return None

def compare_descriptors(desc1, desc2, threshold=0.5):
    """
    Compare deux descripteurs faciaux.
    :param desc1: Premier descripteur facial.
    :param desc2: Deuxième descripteur facial.
    :param threshold: Seuil de similarité (par défaut 0.5).
    :return: True si les descripteurs correspondent, False sinon.
    """
    distance = cosine(desc1, desc2)
    return distance < threshold