# Face Recognition System

This repository contains a face recognition system built using MTCNN for face detection and InceptionResnetV1 for face encoding. The system can detect and recognize faces from a live video stream, comparing them against a set of known faces stored in a specified folder.

## Requirements

- Python 3.6+
- OpenCV
- PyTorch
- NumPy
- facenet-pytorch

## Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/yourusername/face-recognition.git
    cd face-recognition
    ```

2. **Install the required packages:**

    ```bash
    pip install -r requirements.txt
    ```

## Usage

1. **Prepare the folder with known faces:**

    Create a folder named `Images` in the project directory. Add images of known faces to this folder. The filename (without extension) will be used as the person's name.

2. **Run the face recognition system:**

    ```bash
    python face_recognition.py
    ```

## Code Explanation

### Face Detection and Encoding

```python
import os
import cv2
import numpy as np
import torch
from facenet_pytorch import InceptionResnetV1, MTCNN

# Initialize MTCNN and InceptionResnetV1
mtcnn = MTCNN(keep_all=True)
resnet = InceptionResnetV1(pretrained='vggface2').eval()

# Function to detect and encode faces
def detect_and_encode(image):
    with torch.no_grad():
        boxes, probs = mtcnn.detect(image)
        if boxes is not None:
            faces = []
            for box in boxes:
                face = image[int(box[1]):int(box[3]), int(box[0]):int(box[2])]
                if face.size == 0:
                    continue
                face = cv2.resize(face, (160, 160))
                face = np.transpose(face, (2, 0, 1)).astype(np.float32) / 255.0
                face_tensor = torch.tensor(face).unsqueeze(0)
                encoding = resnet(face_tensor).detach().numpy().flatten()
                faces.append(encoding)
            return faces
    return []
```

### Encode Known Faces from a Folder

```python
# Function to encode all images in a folder
def encode_images_in_folder(folder_path):
    known_face_encodings = []
    known_face_names = []

    for filename in os.listdir(folder_path):
        if filename.endswith('.jpg') or filename.endswith('.png'):
            image_path = os.path.join(folder_path, filename)
            known_image = cv2.imread(image_path)
            known_image_rgb = cv2.cvtColor(known_image, cv2.COLOR_BGR2RGB)
            encodings = detect_and_encode(known_image_rgb)
            if encodings:
                known_face_encodings.extend(encodings)
                known_face_names.append(os.path.splitext(filename)[0])  # Use filename as the name

    return known_face_encodings, known_face_names
```

### Recognize Faces in a Video Stream

```python
# Path to your folder containing images
folder_path = 'E:\\Face-recognition\\Face-recognition\\Images'

# Encode known faces from the folder
known_face_encodings, known_face_names = encode_images_in_folder(folder_path)

# Function to recognize faces
def recognize_faces(known_encodings, known_names, test_encodings, threshold=0.6):
    recognized_names = []
    for test_encoding in test_encodings:
        distances = np.linalg.norm(np.array(known_encodings) - test_encoding, axis=1)
        min_distance_idx = np.argmin(distances)
        if distances[min_distance_idx] < threshold:
            recognized_names.append(known_names[min_distance_idx])
        else:
            recognized_names.append('Not Recognized')
    return recognized_names

# Start video capture
cap = cv2.VideoCapture(0)
threshold = 0.6

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    test_face_encodings = detect_and_encode(frame_rgb)

    if test_face_encodings and known_face_encodings:
        names = recognize_faces(known_face_encodings, known_face_names, test_face_encodings, threshold)
        for name, box in zip(names, mtcnn.detect(frame_rgb)[0]):
            if box is not None:
                (x1, y1, x2, y2) = map(int, box)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, name, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

    cv2.imshow('Face Recognition', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
```

### Folder Structure

```
face-recognition/
├── Images/  # Place known face images here
├── face_recognition.py
├── requirements.txt
└── README.md
```

### Notes

- Ensure the `Images` folder is correctly set with the paths to your known face images.
- Adjust the `threshold` value in the `recognize_faces` function for better recognition accuracy based on your specific use case.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- The implementation utilizes the [facenet-pytorch](https://github.com/timesler/facenet-pytorch) library for face detection and recognition.
