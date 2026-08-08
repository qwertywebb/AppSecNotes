# Извлечь все изображения из PDF
pdfimages -all document.pdf images

# QR-коды
zbarimg test.png                 # Чтение QR
qrencode -o qr.png "FLAG{test}"  # Создание QR
