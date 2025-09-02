

import os
import cv2
import numpy as np
import torch
from facenet_pytorch import InceptionResnetV1, MTCNN

def detect_and_encode(image, mtcnn, resnet):
    """
    Detect faces in an image and return their encodings.
    """
    with torch.no_grad():
        boxes, _ = mtcnn.detect(image)
        encodings = []
        if boxes is not None:
            for box in boxes:
                x1, y1, x2, y2 = map(int, box)
                face = image[y1:y2, x1:x2]
                if face.size == 0:
                    continue
                try:
                    face = cv2.resize(face, (160, 160))
                except Exception:
                    continue
                face = np.transpose(face, (2, 0, 1)).astype(np.float32) / 255.0
                face_tensor = torch.tensor(face).unsqueeze(0)
                encoding = resnet(face_tensor).detach().numpy().flatten()
                encodings.append(encoding)
        return encodings, boxes

def encode_images_in_folder(folder_path, mtcnn, resnet):
    """
    Encode all faces in images from a folder. Each face gets its own encoding and name.
    """
    known_face_encodings = []
    known_face_names = []

    for filename in os.listdir(folder_path):
        if filename.lower().endswith(('.jpg', '.png')):
            image_path = os.path.join(folder_path, filename)
            known_image = cv2.imread(image_path)
            if known_image is None:
                print(f"Warning: Could not load image {image_path}")
                continue
            known_image_rgb = cv2.cvtColor(known_image, cv2.COLOR_BGR2RGB)
            encodings, _ = detect_and_encode(known_image_rgb, mtcnn, resnet)
            for encoding in encodings:
                known_face_encodings.append(encoding)
                known_face_names.append(os.path.splitext(filename)[0])
    return known_face_encodings, known_face_names

def recognize_faces(known_encodings, known_names, test_encodings, threshold=0.6):
    """
    Recognize faces by comparing encodings to known faces.
    """
    recognized_names = []
    for test_encoding in test_encodings:
        if not known_encodings:
            recognized_names.append('Not Recognized')
            continue
        distances = np.linalg.norm(np.array(known_encodings) - test_encoding, axis=1)
        min_distance_idx = np.argmin(distances)
        if distances[min_distance_idx] < threshold:
            recognized_names.append(known_names[min_distance_idx])
        else:
            recognized_names.append('Not Recognized')
    return recognized_names

def main():
    # Initialize models
    mtcnn = MTCNN(keep_all=True)
    resnet = InceptionResnetV1(pretrained='vggface2').eval()

    # Path to your folder containing images
    folder_path = r'E:\MY PROJECTS\Published\Face-Recognition\Images'

    # Encode known faces from the folder
    known_face_encodings, known_face_names = encode_images_in_folder(folder_path, mtcnn, resnet)

    # Start video capture
    cap = cv2.VideoCapture(0)
    threshold = 0.6

    print("Press 'q' to quit.")
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        test_face_encodings, boxes = detect_and_encode(frame_rgb, mtcnn, resnet)

        if test_face_encodings and known_face_encodings and boxes is not None:
            names = recognize_faces(known_face_encodings, known_face_names, test_face_encodings, threshold)
            for name, box in zip(names, boxes):
                if box is not None:
                    x1, y1, x2, y2 = map(int, box)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, name, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

        cv2.imshow('Face Recognition', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
