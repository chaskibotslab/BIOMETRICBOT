"""
Servicio de Reconocimiento Facial PROFESIONAL
Usa InsightFace (ArcFace) - El mismo modelo usado en bancos y seguridad
Precision: 99.8% en LFW benchmark
"""
import numpy as np
import cv2
import io
import base64
from typing import Optional, Tuple, List
from dataclasses import dataclass
import re


@dataclass
class FaceResult:
    success: bool
    encoding: Optional[np.ndarray] = None
    face_location: Optional[Tuple[int, int, int, int]] = None
    quality_score: float = 0.0
    message: str = ""
    face_count: int = 0


@dataclass
class MatchResult:
    matched: bool
    confidence: float = 0.0
    empleado_id: Optional[str] = None
    message: str = ""


class FaceRecognitionService:
    def __init__(self):
        print("=" * 50)
        print("CARGANDO MODELO INSIGHTFACE (ArcFace)")
        print("Modelo de nivel bancario - 99.8% precision")
        print("=" * 50)

        self.model_loaded = False
        self.app = None

        try:
            from insightface.app import FaceAnalysis

            self.app = FaceAnalysis(
                name='buffalo_l',
                providers=['CPUExecutionProvider']
            )
            self.app.prepare(ctx_id=0, det_size=(640, 640))

            self.model_loaded = True
            print("[OK] Modelo InsightFace cargado correctamente")

        except Exception as e:
            print(f"[ERROR] No se pudo cargar InsightFace: {e}")
            print("[INFO] Usando modelo de respaldo...")
            self._init_backup()

        self.similarity_threshold = 0.45
        self.min_quality = 40.0

        print(f"[CONFIG] Umbral de similitud: {self.similarity_threshold}")
        print("=" * 50)

    def _init_backup(self):
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )

    def decode_base64_image(self, base64_string: str) -> np.ndarray:
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]

        base64_string = re.sub(r'\s+', '', base64_string)
        image_bytes = base64.b64decode(base64_string)

        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            raise ValueError("No se pudo decodificar la imagen")

        return image

    def detect_and_encode(self, image_base64: str) -> FaceResult:
        try:
            image = self.decode_base64_image(image_base64)
            print(f"[OK] Imagen: {image.shape}")

            if self.model_loaded and self.app:
                return self._insightface_detect(image)
            else:
                return self._backup_detect(image)

        except Exception as e:
            print(f"[ERROR] {str(e)}")
            return FaceResult(success=False, message=f"Error: {str(e)}")

    def _insightface_detect(self, image: np.ndarray) -> FaceResult:
        print("[...] Analizando con InsightFace...")
        faces = self.app.get(image)

        print(f"[OK] Rostros: {len(faces)}")

        if len(faces) == 0:
            return FaceResult(
                success=False,
                message="No se detecto rostro. Mira a la camara.",
                face_count=0
            )

        if len(faces) > 1:
            return FaceResult(
                success=False,
                message=f"Se detectaron {len(faces)} rostros. Solo uno permitido.",
                face_count=len(faces)
            )

        face = faces[0]
        quality = float(face.det_score) * 100 if hasattr(face, 'det_score') else 70.0

        print(f"[OK] Calidad: {quality:.1f}%")

        if quality < self.min_quality:
            return FaceResult(
                success=False,
                message=f"Calidad baja: {quality:.1f}%. Mejora iluminacion.",
                quality_score=quality,
                face_count=1
            )

        embedding = face.embedding
        if embedding is None:
            return FaceResult(success=False, message="No se pudo generar encoding", face_count=1)

        embedding = embedding / np.linalg.norm(embedding)

        bbox = face.bbox.astype(int)
        face_location = (bbox[1], bbox[2], bbox[3], bbox[0])

        print(f"[OK] Embedding: {embedding.shape}")

        return FaceResult(
            success=True,
            encoding=embedding,
            face_location=face_location,
            quality_score=quality,
            message="Rostro detectado",
            face_count=1
        )

    def _backup_detect(self, image: np.ndarray) -> FaceResult:
        print("[...] Usando modelo de respaldo...")
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(80, 80))

        if len(faces) == 0:
            return FaceResult(success=False, message="No se detecto rostro", face_count=0)

        if len(faces) > 1:
            return FaceResult(success=False, message="Multiples rostros", face_count=len(faces))

        x, y, w, h = faces[0]
        face_img = image[y:y + h, x:x + w]
        face_resized = cv2.resize(face_img, (112, 112))

        gray_face = cv2.cvtColor(face_resized, cv2.COLOR_BGR2GRAY)
        hsv_face = cv2.cvtColor(face_resized, cv2.COLOR_BGR2HSV)

        features = []

        hist_gray = cv2.calcHist([gray_face], [0], None, [64], [0, 256]).flatten()
        hist_h = cv2.calcHist([hsv_face], [0], None, [32], [0, 180]).flatten()
        hist_s = cv2.calcHist([hsv_face], [1], None, [32], [0, 256]).flatten()

        features.extend(hist_gray / (hist_gray.sum() + 1e-7))
        features.extend(hist_h / (hist_h.sum() + 1e-7))
        features.extend(hist_s / (hist_s.sum() + 1e-7))

        for i in range(0, 112, 14):
            for j in range(0, 112, 14):
                region = gray_face[i:i + 14, j:j + 14]
                features.append(np.mean(region) / 255)
                features.append(np.std(region) / 128)

        embedding = np.array(features, dtype=np.float32)
        embedding = embedding / (np.linalg.norm(embedding) + 1e-7)

        return FaceResult(
            success=True,
            encoding=embedding,
            face_location=(y, x + w, y + h, x),
            quality_score=70.0,
            message="Rostro detectado (respaldo)",
            face_count=1
        )

    def cosine_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        emb1_norm = emb1 / (np.linalg.norm(emb1) + 1e-7)
        emb2_norm = emb2 / (np.linalg.norm(emb2) + 1e-7)
        return float(np.dot(emb1_norm, emb2_norm))

    def compare_faces(self, known_encoding: np.ndarray, unknown_image_base64: str) -> MatchResult:
        result = self.detect_and_encode(unknown_image_base64)

        if not result.success:
            return MatchResult(matched=False, message=result.message)

        similarity = self.cosine_similarity(known_encoding, result.encoding)
        confidence = similarity * 100

        matched = similarity >= self.similarity_threshold

        print(f"[MATCH] Similitud: {similarity:.4f} ({confidence:.1f}%)")
        print(f"[MATCH] Umbral: {self.similarity_threshold} | Resultado: {'SI' if matched else 'NO'}")

        return MatchResult(
            matched=matched,
            confidence=float(round(confidence, 1)),
            message="Identidad verificada" if matched else "No coincide"
        )

    def find_match(self, image_base64: str, known_encodings: List[Tuple[str, np.ndarray]]) -> MatchResult:
        result = self.detect_and_encode(image_base64)

        if not result.success:
            return MatchResult(matched=False, message=result.message)

        if not known_encodings:
            return MatchResult(matched=False, message="No hay empleados registrados")

        print(f"\n[BUSQUEDA] Comparando contra {len(known_encodings)} empleados...")

        best_id = None
        best_sim = -1

        for emp_id, known_enc in known_encodings:
            if known_enc.shape[0] != 512:
                print(f"  - {emp_id[:8]}...: SKIP (dim={known_enc.shape[0]}, necesita re-registro)")
                continue
            sim = self.cosine_similarity(known_enc, result.encoding)
            print(f"  - {emp_id[:8]}...: {sim:.4f} ({sim * 100:.1f}%)")

            if sim > best_sim:
                best_sim = sim
                best_id = emp_id

        confidence = float(best_sim * 100) if best_sim > 0 else 0.0

        print(f"\n[RESULTADO] Mejor: {best_id[:8] if best_id else 'ninguno'}")
        print(f"[RESULTADO] Similitud: {best_sim:.4f} ({confidence:.1f}%)")
        print(f"[RESULTADO] Umbral: {self.similarity_threshold} ({self.similarity_threshold * 100}%)")

        if best_sim >= self.similarity_threshold:
            print("[RESULTADO] *** MATCH ENCONTRADO ***")
            return MatchResult(
                matched=True,
                confidence=float(round(confidence, 1)),
                empleado_id=best_id,
                message="Empleado identificado"
            )

        print("[RESULTADO] *** SIN COINCIDENCIA ***")
        return MatchResult(
            matched=False,
            confidence=float(round(confidence, 1)),
            message=f"Sin coincidencia ({confidence:.1f}% < {self.similarity_threshold * 100}%)"
        )

    def find_match_from_encoding(self, encoding: np.ndarray, known_encodings: List[Tuple[str, np.ndarray]]) -> MatchResult:
        """Compara un encoding ya extraido contra la lista de conocidos (sin decodificar imagen)"""
        if not known_encodings:
            return MatchResult(matched=False, message="No hay registros para comparar")

        print(f"\n[DUP-CHECK] Verificando duplicado contra {len(known_encodings)} empleados...")

        best_id = None
        best_sim = -1

        for emp_id, known_enc in known_encodings:
            if known_enc.shape[0] != encoding.shape[0]:
                continue
            sim = self.cosine_similarity(known_enc, encoding)
            print(f"  - {emp_id[:8]}...: {sim:.4f} ({sim * 100:.1f}%)")

            if sim > best_sim:
                best_sim = sim
                best_id = emp_id

        confidence = float(best_sim * 100) if best_sim > 0 else 0.0

        if best_sim >= self.similarity_threshold:
            print(f"[DUP-CHECK] *** ROSTRO DUPLICADO: {best_id[:8]}... ({confidence:.1f}%) ***")
            return MatchResult(
                matched=True,
                confidence=float(round(confidence, 1)),
                empleado_id=best_id,
                message="Rostro duplicado detectado"
            )

        print(f"[DUP-CHECK] Sin duplicado (mejor: {confidence:.1f}%)")
        return MatchResult(matched=False, confidence=float(round(confidence, 1)), message="Sin duplicado")

    @staticmethod
    def serialize_encoding(encoding: np.ndarray) -> bytes:
        return encoding.astype(np.float32).tobytes()

    @staticmethod
    def deserialize_encoding(data: bytes) -> np.ndarray:
        # Try new format first (numpy float32 tobytes — 512 * 4 = 2048 bytes)
        arr = np.frombuffer(data, dtype=np.float32)
        if arr.shape[0] == 512:
            return arr.copy()
        # Try float64 (in case stored differently)
        arr64 = np.frombuffer(data, dtype=np.float64)
        if arr64.shape[0] == 512:
            return arr64.astype(np.float32).copy()
        # Fallback: try pickle (old format from legacy system)
        try:
            import pickle
            arr_pickle = pickle.loads(data)
            if hasattr(arr_pickle, 'shape'):
                flat = np.array(arr_pickle, dtype=np.float32).flatten()
                return flat
        except Exception:
            pass
        # Return whatever we got
        return arr.copy()

    def get_face_thumbnail(self, image_base64: str, face_location: Tuple, size: Tuple[int, int] = (200, 200)) -> str:
        try:
            image = self.decode_base64_image(image_base64)
            top, right, bottom, left = face_location

            margin = int((bottom - top) * 0.3)
            top = max(0, top - margin)
            bottom = min(image.shape[0], bottom + margin)
            left = max(0, left - margin)
            right = min(image.shape[1], right + margin)

            face = image[top:bottom, left:right]
            face_resized = cv2.resize(face, size)

            _, buffer = cv2.imencode('.jpg', face_resized, [cv2.IMWRITE_JPEG_QUALITY, 90])
            return base64.b64encode(buffer).decode()
        except:
            return ""


face_service = FaceRecognitionService()