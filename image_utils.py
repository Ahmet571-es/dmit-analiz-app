import cv2
import numpy as np

def process_fingerprint(image_bytes):
    """
    Grok'un daha iyi görmesi için parmak izi resmini işler:
    1. Gri tona çevirir.
    2. CLAHE ile kontrastı patlatır (Çizgiler netleşir).
    3. Gürültüleri temizler.
    4. Adaptive Threshold ile siyah-beyaz (Binary) yapar.
    """
    # 1. Byte verisini OpenCV formatına çevir
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # 2. Gri Tona Çevir
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 3. CLAHE (Contrast Limited Adaptive Histogram Equalization)
    # Bu adım parmak izi çizgilerini inanılmaz belirginleştirir.
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    
    # 4. Gaussian Blur (Gürültü temizleme - parazit noktaları siler)
    blurred = cv2.GaussianBlur(enhanced, (5, 5), 0)
    
    # 5. Adaptive Threshold (Siyah-Beyaz Keskinleştirme)
    # Bu işlem resimdeki gölgeleri yok eder, sadece net çizgiler kalır.
    binary = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY_INV, 11, 2)
    
    # 6. İşlenmiş resmi tekrar byte formatına çevir (Grok'a göndermek için)
    is_success, buffer = cv2.imencode(".jpg", binary)
    
    if is_success:
        return buffer.tobytes()
    else:
        return image_bytes # Hata olursa orijinali döndür
