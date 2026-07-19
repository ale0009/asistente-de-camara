import os
import time
import math
import logging

import cv2
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions, RunningMode

logger = logging.getLogger(__name__)

# Índices de landmarks de la mano (equivalentes a mp.solutions.hands.HandLandmark,
# que ya no está disponible en la API "Tasks" usada aquí para soportar Python 3.13).
THUMB_TIP, THUMB_IP = 4, 3
INDEX_TIP, INDEX_PIP = 8, 6
MIDDLE_TIP, MIDDLE_PIP = 12, 10
RING_TIP, RING_PIP = 16, 14
PINKY_TIP, PINKY_PIP = 20, 18

HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (0, 9), (9, 10), (10, 11), (11, 12),
    (0, 13), (13, 14), (14, 15), (15, 16),
    (0, 17), (17, 18), (18, 19), (19, 20),
    (5, 9), (9, 13), (13, 17),
]

MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "hand_landmarker.task"
)


class GestureEngine:
    """
    Motor de reconocimiento de gestos de manos con MediaPipe Tasks (HandLandmarker).
    Detecta la estructura de la mano sobre el frame UVC en tiempo real
    y dispara eventos (ej. "Palma Abierta", "Pellizco").
    """
    def __init__(self, config=None):
        self.config = config or {}
        self.enabled = False
        self.landmarker = None
        self._start_time = time.time()

        try:
            options = HandLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=MODEL_PATH),
                running_mode=RunningMode.VIDEO,
                num_hands=2,
                min_hand_detection_confidence=0.7,
                min_tracking_confidence=0.5,
            )
            self.landmarker = HandLandmarker.create_from_options(options)
            self.enabled = True
        except Exception as e:
            logger.warning(f"No se pudo inicializar MediaPipe HandLandmarker ({e}). Motor de gestos desactivado.")

        # Callbacks
        self.on_gesture_detected = None

        # Estado para evitar disparos múltiples rápidos (debounce)
        self.last_gesture = None
        self.frames_with_same_gesture = 0
        self.activation_frames = 15  # Aprox 0.5s a 30fps

    def process_frame(self, frame):
        """Procesa un frame BGR de OpenCV y busca manos."""
        if frame is None or not self.enabled:
            return frame

        # Convertir a RGB (MediaPipe usa RGB) y voltear para efecto espejo
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image_rgb = cv2.flip(image_rgb, 1)

        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
        timestamp_ms = int((time.time() - self._start_time) * 1000)
        result = self.landmarker.detect_for_video(mp_image, timestamp_ms)

        image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)

        detected_gesture = None
        if result.hand_landmarks:
            # Tomamos el gesto de la primera mano detectada por ahora
            landmarks = result.hand_landmarks[0]
            self._draw_landmarks(image_bgr, landmarks)
            detected_gesture = self._recognize_gesture(landmarks)

        self._debounce_gesture(detected_gesture)

        # Volver a voltear para que el usuario se vea bien
        return cv2.flip(image_bgr, 1)

    def _draw_landmarks(self, image, landmarks):
        """Dibuja el esqueleto de la mano y marca sutilmente el centro de encuadre."""
        h, w = image.shape[:2]
        points = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks]

        for start, end in HAND_CONNECTIONS:
            cv2.line(image, points[start], points[end], (255, 255, 255), 2)
        for point in points:
            cv2.circle(image, point, 4, (0, 255, 0), -1)

        # Guía de encuadre en el tercio superior
        guide_y = int(h * 0.33)
        cv2.line(image, (0, guide_y), (w, guide_y), (0, 229, 255), 1)

    def _recognize_gesture(self, landmarks):
        """
        Analiza las coordenadas (x,y,z) de los 21 puntos de la mano.
        """
        tips = [THUMB_TIP, INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP]
        pips = [THUMB_IP, INDEX_PIP, MIDDLE_PIP, RING_PIP, PINKY_PIP]

        fingers_up = []
        for i in range(1, 5):  # Ignoramos pulgar de momento para conteo simple
            if landmarks[tips[i]].y < landmarks[pips[i]].y:
                fingers_up.append(1)
            else:
                fingers_up.append(0)

        # Calcular distancia entre pulgar e índice (para el pellizco)
        thumb_tip = landmarks[THUMB_TIP]
        index_tip = landmarks[INDEX_TIP]

        pinch_dist = math.hypot(thumb_tip.x - index_tip.x, thumb_tip.y - index_tip.y)

        # 1. Palma Abierta (Todos arriba)
        if sum(fingers_up) == 4:
            return "palma_abierta"

        # 2. Pulgar Arriba (Like)
        if sum(fingers_up) == 0 and landmarks[THUMB_TIP].y < landmarks[THUMB_IP].y and pinch_dist > 0.08:
            return "pulgar_arriba"

        # 3. Puño (Todos abajo)
        if sum(fingers_up) == 0 and pinch_dist > 0.1:
            return "puno"

        # 4. Pellizco / Zoom continuo
        if sum(fingers_up) <= 1 and pinch_dist < 0.20:
            zoom_val = int(max(0, min(100, (pinch_dist - 0.03) / 0.15 * 100)))
            return f"zoom_{zoom_val}"

        # 5. Paz (V) - Índice y Medio arriba
        if fingers_up == [1, 1, 0, 0]:
            return "victoria"

        # 6. Apuntar (Solo índice arriba)
        if fingers_up == [1, 0, 0, 0]:
            return "apuntar"

        return None

    def _debounce_gesture(self, current_gesture):
        """Asegura que un gesto se mantenga unos frames antes de dispararlo."""
        if current_gesture and current_gesture.startswith("zoom_"):
            if self.on_gesture_detected:
                self.on_gesture_detected(current_gesture)
            return

        if current_gesture == self.last_gesture and current_gesture is not None:
            self.frames_with_same_gesture += 1

            # Disparar solo una vez cuando alcanza los frames
            if self.frames_with_same_gesture == self.activation_frames:
                logger.info(f"Gesto consolidado: {current_gesture}")
                if self.on_gesture_detected:
                    self.on_gesture_detected(current_gesture)
        else:
            # Gesto cambió o es None
            self.last_gesture = current_gesture
            self.frames_with_same_gesture = 0
