import cv2
import numpy as np

def process_fingerprint(image_bytes):
    """
    Grok'un 'Skeletonized' (İskeletleştirilmiş) beklentisini karşılamak için
    parmak izini alır, temizler, siyah-beyaz yapar ve 'İnceltme' (Thinning) uygular.
    """
    try:
        # 1. Byte verisini OpenCV formatına çevir
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return image_bytes

        # 2. Gri Tona Çevir
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 3. CLAHE ile Kontrastı Patlat (Çizgileri belirginleştir)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # 4. Gürültü Temizleme (Gaussian Blur)
        blurred = cv2.GaussianBlur(enhanced, (5, 5), 0)
        
        # 5. Otsu Eşikleme ile Net Siyah-Beyaz (Binary) Yap
        # (Adaptive Threshold yerine Otsu bazen daha temiz sonuç verir)
        _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # 6. İSKELETLEŞTİRME (SKELETONIZATION) - EN ÖNEMLİ ADIM
        # Bu algoritma kalın çizgileri 1 piksel genişliğinde 'tel' haline getirir.
        skeleton = np.zeros(binary.shape, np.uint8)
        element = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
        done = False

        while not done:
            eroded = cv2.erode(binary, element)
            temp = cv2.dilate(eroded, element)
            temp = cv2.subtract(binary, temp)
            skeleton = cv2.bitwise_or(skeleton, temp)
            binary = eroded.copy()

            if cv2.countNonZero(binary) == 0:
                done = True

        # 7. Sonuç: Siyah zemin üzerine Beyaz İskelet
        # Grok'un en iyi gördüğü format budur.
        is_success, buffer = cv2.imencode(".jpg", skeleton)
        
        if is_success:
            return buffer.tobytes()
        else:
            return image_bytes # İşleme hatası olursa orijinali döndür

    except Exception as e:
        print(f"Görüntü İşleme Hatası: {e}")
        return image_bytes # Kritik hata olursa sistem çökmesin, orijinali yollasın
