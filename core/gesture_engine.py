import os
import time
import math
import logging
from typing import Optional, Tuple

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
                running_mode=RunningMode.IMAGE,
                num_hands=1,
                min_hand_detection_confidence=0.7,
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
        self.activation_frames = 5  # Aprox 0.5s a 10fps de inferencia
        self._frame_count = 0
        self._last_landmarks = None
        self._last_action_time = 0.0

    def process_frame(self, frame):
        """Procesa un frame BGR de OpenCV y busca manos de forma optimizada."""
        if frame is None:
            return None
        if not self.enabled:
            return frame

        self._frame_count += 1
        # Espejo en BGR para vista natural tipo selfie
        mirrored = cv2.flip(frame, 1)

        # Muestreo cada 3 frames (~10 FPS para MediaPipe): reduce drásticamente el uso de CPU
        if self._frame_count % 3 == 0:
            image_rgb = cv2.cvtColor(mirrored, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
            try:
                result = self.landmarker.detect(mp_image)
                if result.hand_landmarks:
                    self._last_landmarks = result.hand_landmarks[0]
                    detected_gesture = self._recognize_gesture(self._last_landmarks)
                else:
                    self._last_landmarks = None
                    detected_gesture = None
                self._debounce_gesture(detected_gesture)
            except Exception as e:
                logger.debug(f"MediaPipe frame skip: {e}")

        # Dibujar landmarks sobre el frame actual si existen
        if self._last_landmarks:
            self._draw_landmarks(mirrored, self._last_landmarks)

        return mirrored

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

    def get_pointed_coordinates(self) -> Optional[tuple]:
        """Devuelve las coordenadas normalizadas (x, y) de la punta del índice si hay una mano detectada."""
        if self._last_landmarks and len(self._last_landmarks) > INDEX_TIP:
            lm = self._last_landmarks[INDEX_TIP]
            # lm.x está en el frame 'mirrored', por lo que invertimos x para mapear al frame original de cámara
            orig_x = 1.0 - lm.x
            orig_y = lm.y
            return (orig_x, orig_y)
        return None

    def get_foveated_crop(self, frame, crop_size: int = 448):
        """
        Extrae un recorte centrado en la punta del dedo que señala (Visión Foveada).
        Si no se está señalando activamente, devuelve el frame completo o recorte central.
        """
        if frame is None:
            return None

        h, w = frame.shape[:2]
        coords = self.get_pointed_coordinates()
        
        if coords:
            cx = int(coords[0] * w)
            cy = int(coords[1] * h)
        else:
            cx, cy = w // 2, h // 2

        half = crop_size // 2
        x1 = max(0, min(w - crop_size, cx - half))
        y1 = max(0, min(h - crop_size, cy - half))
        x2 = min(w, x1 + crop_size)
        y2 = min(h, y1 + crop_size)

        return frame[y1:y2, x1:x2]

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

        # Distancia entre pulgar e índice tip (para pellizco) y pulgar e índice PIP (para extensión del pulgar)
        thumb_tip = landmarks[THUMB_TIP]
        index_tip = landmarks[INDEX_TIP]
        index_pip = landmarks[INDEX_PIP]

        pinch_dist = math.hypot(thumb_tip.x - index_tip.x, thumb_tip.y - index_tip.y)
        thumb_pip_dist = math.hypot(thumb_tip.x - index_pip.x, thumb_tip.y - index_pip.y)

        # 1. Palma Abierta vs Cuatro Dedos (según extensión del pulgar)
        if sum(fingers_up) == 4:
            if thumb_pip_dist < 0.12:
                return "cuatro_dedos"
            return "palma_abierta"

        # 2. Pulgar Arriba (Like)
        if sum(fingers_up) == 0 and landmarks[THUMB_TIP].y < landmarks[THUMB_IP].y and pinch_dist > 0.08:
            return "pulgar_arriba"

        # Pulgar Abajo (Dislike)
        if sum(fingers_up) == 0 and landmarks[THUMB_TIP].y > landmarks[THUMB_IP].y and pinch_dist > 0.08:
            return "pulgar_abajo"

        # OK (Pellizco de pulgar e índice, otros tres dedos arriba)
        if fingers_up == [0, 1, 1, 1] and pinch_dist < 0.06:
            return "ok"

        # 3. Puño (Todos abajo)
        if sum(fingers_up) == 0 and pinch_dist > 0.1:
            return "puno"

        # 4. Tres Dedos (Índice, Medio y Anular arriba, Meñique abajo)
        if fingers_up == [1, 1, 1, 0]:
            return "tres_dedos"

        # 5. Rock / Cuernos (Índice y Meñique arriba)
        if fingers_up == [1, 0, 0, 1]:
            return "rock"

        # 6. Pellizco / Zoom continuo
        if sum(fingers_up) <= 1 and pinch_dist < 0.20:
            zoom_val = int(max(0, min(100, (pinch_dist - 0.03) / 0.15 * 100)))
            return f"zoom_{zoom_val}"

        # 7. Paz / Victoria (V) - Índice y Medio arriba
        if fingers_up == [1, 1, 0, 0]:
            return "victoria"

        # 8. Apuntar vs Mano L (Índice arriba con pulgar guardado o extendido)
        if fingers_up == [1, 0, 0, 0]:
            if thumb_pip_dist > 0.18:
                return "mano_l"
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

            # Disparar solo una vez cuando alcanza los frames y respeta el cooldown de 2s
            if self.frames_with_same_gesture == self.activation_frames:
                now = time.time()
                if now - self._last_action_time > 2.0:
                    self._last_action_time = now
                    logger.info(f"Gesto consolidado: {current_gesture}")
                    if self.on_gesture_detected:
                        self.on_gesture_detected(current_gesture)
        else:
            # Gesto cambió o es None
            self.last_gesture = current_gesture
            self.frames_with_same_gesture = 0
