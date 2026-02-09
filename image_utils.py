import cv2
import numpy as np

def process_fingerprint(image_bytes):
    """
    Grok'un 'Skeletonized' (İskeletleştirilmiş) beklentisini karşılamak için
    parmak izini alır, temizler, siyah-beyaz yapar ve 'İnceltme' (Thinning) uygular.
    Bu işlem, kalın parmak izi çizgilerini 1 piksel genişliğinde 'tel' haline getirir.
    """
    try:
        # 1. Byte verisini OpenCV formatına (NumPy Array) çevir
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Eğer resim bozuksa veya yüklenemediyse orijinali döndür
        if img is None:
            return image_bytes

        # 2. Gri Tona Çevir (Renk bilgisine ihtiyacımız yok)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 3. CLAHE ile Kontrastı Patlat 
        # (Işık dağılımını dengeler, çizgileri arka plandan ayırır)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # 4. Gürültü Temizleme (Gaussian Blur)
        # (Parmak üzerindeki tozları ve sensör gürültülerini siler)
        blurred = cv2.GaussianBlur(enhanced, (5, 5), 0)
        
        # 5. Otsu Eşikleme ile Net Siyah-Beyaz (Binary) Yap
        # (Adaptive Threshold yerine Otsu kullanıyoruz çünkü iskeletleştirme için daha temiz zemin hazırlar)
        # THRESH_BINARY_INV: Çizgileri Beyaz, Arka Planı Siyah yapar.
        _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # ---------------------------------------------------------
        # 6. İSKELETLEŞTİRME (SKELETONIZATION) - SİHİRLİ DOKUNUŞ
        # ---------------------------------------------------------
        # Bu döngü, çizgiler 1 piksel kalınlığında kalana kadar onları "aşındırır".
        # Grok'un sayı sayabilmesi için en önemli adım budur.
        
        skeleton = np.zeros(binary.shape, np.uint8)
        element = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
        done = False

        while not done:
            eroded = cv2.erode(binary, element)
            temp = cv2.dilate(eroded, element)
            temp = cv2.subtract(binary, temp)
            skeleton = cv2.bitwise_or(skeleton, temp)
            binary = eroded.copy()

            # Eğer aşındırılacak piksel kalmadıysa döngüyü bitir
            if cv2.countNonZero(binary) == 0:
                done = True

        # 7. Sonuç: Siyah zemin üzerine Beyaz İskelet
        # Grok'a geri göndermek için tekrar JPG formatına (byte) çevir
        is_success, buffer = cv2.imencode(".jpg", skeleton)
        
        if is_success:
            return buffer.tobytes()
        else:
            return image_bytes # İşleme hatası olursa orijinali döndür

    except Exception as e:
        # Herhangi bir kütüphane hatasında sistemin çökmesini engelle
        print(f"Görüntü İşleme Hatası: {e}")
        return image_bytes
