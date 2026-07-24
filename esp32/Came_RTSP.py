import cv2

url = 'rtsp://admin:oAMeR2@192.168.1.196:8556/live'   # Thay bằng địa chỉ của m

cap = cv2.VideoCapture(url)

if not cap.isOpened():
    print("Không kết nối được camera!")
    exit()
 
while True:
    ret, frame = cap.read()

    if not ret:
        print("Không đọc được frame")
        break

    cv2.imshow("Phone Camera", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()