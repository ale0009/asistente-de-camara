from unittest.mock import Mock
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.gesture_engine import GestureEngine, THUMB_TIP, THUMB_IP, INDEX_TIP, INDEX_PIP, MIDDLE_TIP, MIDDLE_PIP, RING_TIP, RING_PIP, PINKY_TIP, PINKY_PIP

def make_dummy_landmarks():
    # 21 puntos dummy
    landmarks = [Mock(x=0.5, y=0.5, z=0.0) for _ in range(21)]
    return landmarks

def test_gesture_engine_recognize_apuntar():
    engine = GestureEngine.__new__(GestureEngine)
    landmarks = make_dummy_landmarks()
    
    # Índice arriba (y menor que pip)
    landmarks[INDEX_TIP].y = 0.2
    landmarks[INDEX_PIP].y = 0.4
    
    # Los otros abajo (y mayor que pip)
    landmarks[MIDDLE_TIP].y = 0.6
    landmarks[MIDDLE_PIP].y = 0.4
    landmarks[RING_TIP].y = 0.6
    landmarks[RING_PIP].y = 0.4
    landmarks[PINKY_TIP].y = 0.6
    landmarks[PINKY_PIP].y = 0.4
    
    assert engine._recognize_gesture(landmarks) == "apuntar"

def test_gesture_engine_recognize_pulgar_arriba():
    engine = GestureEngine.__new__(GestureEngine)
    landmarks = make_dummy_landmarks()
    
    # Todos los dedos abajo
    for tip, pip in [(INDEX_TIP, INDEX_PIP), (MIDDLE_TIP, MIDDLE_PIP), (RING_TIP, RING_PIP), (PINKY_TIP, PINKY_PIP)]:
        landmarks[tip].y = 0.6
        landmarks[pip].y = 0.4
        
    # Pulgar arriba (y de tip menor que IP)
    landmarks[THUMB_TIP].x = 0.5
    landmarks[THUMB_TIP].y = 0.1
    landmarks[THUMB_IP].y = 0.3
    
    # Distancia pinch razonable (> 0.08)
    landmarks[INDEX_TIP].x = 0.7
    landmarks[INDEX_TIP].y = 0.6
    
    assert engine._recognize_gesture(landmarks) == "pulgar_arriba"
