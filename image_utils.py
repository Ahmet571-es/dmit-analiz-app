import cv2
import numpy as np

def check_image_quality(image_bytes, blur_threshold=60.0):
    """
    Resmin kalitesini ve netliğini kontrol eder.
    Laplacian Varyansı yöntemi kullanılır.
    
    Argümanlar:
        image_bytes: Resmin byte verisi.
        blur_threshold: Eşik değeri (Altında kalırsa bulanık sayılır). 
                        Telefon kameraları için 60-100 arası idealdir.
    
    Dönüş:
        (is_accepted, score, message)
        - is_accepted: True (Net) / False (Bulanık)
        - score: Netlik puanı (Yüksek iyidir)
        - message: Kullanıcıya gösterilecek mesaj
    """
    try:
        # Byte'tan OpenCV formatına çevir
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return False, 0.0, "Resim dosyası bozuk veya okunamadı."

        # Griye çevirip kenar keskinliğini ölç
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        score = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        if score < blur_threshold:
            return False, score, f"⚠️ GÖRÜNTÜ ÇOK BULANIK (Netlik: {int(score)}/100). Lütfen kamerayı sabitleyip tekrar çekin."
        
        return True, score, "✅ Görüntü net ve işlenmeye uygun."

    except Exception as e:
        return False, 0.0, f"Kalite kontrol hatası: {str(e)}"

def process_fingerprint(image_bytes):
    """
    Grok Yapay Zekası için parmak izini 'İskeletleştirir'.
    Adımlar:
    1. Keskinleştirme
    2. Kontrast Artırma (CLAHE)
    3. Gürültü Temizleme
    4. Siyah-Beyaz Yapma (Otsu)
    5. İnceltme (Skeletonization) -> Çizgileri 1 piksel yapar.
    """
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return image_bytes

        # 1. HAFİF KESKİNLEŞTİRME (Sharpening Kernel)
        # Hafif odak kayıplarını telafi eder.
        kernel = np.array([[0, -1, 0],
                           [-1, 5,-1],
                           [0, -1, 0]])
        img = cv2.filter2D(src=img, ddepth=-1, kernel=kernel)

        # 2. Gri Tona Çevir
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 3. CLAHE (Kontrastı Patlat)
        # Bu adım çizgileri arka plandan ayırır.
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # 4. Gaussian Blur (Gürültü Temizleme)
        # Sensör tozlarını yok eder.
        blurred = cv2.GaussianBlur(enhanced, (5, 5), 0)
        
        # 5. Otsu Eşikleme (Binary)
        # Resmi sadece Siyah ve Beyaz yapar.
        _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # 6. İSKELETLEŞTİRME (Skeletonization) - KRİTİK ADIM
        # Kalın çizgileri tek piksellik "tel" haline getirir.
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
        is_success, buffer = cv2.imencode(".jpg", skeleton)
        
        if is_success:
            return buffer.tobytes()
        else:
            return image_bytes

    except Exception as e:
        print(f"Görüntü İşleme Hatası: {e}")
        return image_bytes
