#include <Arduino.h>
#include <driver.std>

// ==========================================
// CODE ĐIỀU KHIỂN LED RGB ANODE CHUNG BẰNG CỤM NÚT BẤM
// THIẾT KẾ DÀNH RIÊNG CHO ESP32
// ==========================================

// 1. Khai báo các chân kết nối LED RGB
const int redPin = 33;   // Chân Đỏ (R) nối GPIO 18
const int greenPin = 26; // Chân Xanh lá (G) nối GPIO 19
const int bluePin = 25;  // Chân Xanh dương (B) nối GPIO 21

// 2. Khai báo các chân kết nối Cụm nút bấm
const int btnPV = 27;   
const int btnNV = 14;   
const int btnPlay = 12; 

void setup() {
  // Khởi tạo Cổng Serial Monitor với tốc độ baud 115200 (chuẩn ESP32)
  Serial.begin(115200);

  // Cấu hình các chân LED là đầu ra (OUTPUT)
  pinMode(redPin, OUTPUT);
  pinMode(greenPin, OUTPUT);
  pinMode(bluePin, OUTPUT);

  // Cấu hình các chân nút bấm là đầu vào kéo lên nội (INPUT_PULLUP)
  // Khi không bấm nút = HIGH, khi bấm nút chân chập với kcom (GND) = LOW
  pinMode(btnPV, INPUT_PULLUP);
  pinMode(btnNV, INPUT_PULLUP);
  pinMode(btnPlay, INPUT_PULLUP);

  // Đảm bảo tắt toàn bộ đèn LED khi mạch vừa khởi động xong
  setColor(0, 0, 0); 
  
  Serial.println("\n====================================");
  Serial.println("ESP32 CONG TAC & LED RGB DA SAN SANG!");
  Serial.println("Hay thu bam cac nut tren cum dieu khien...");
  Serial.println("====================================");
}

void loop() {
  // Đọc trạng thái điện áp hiện tại của cả 3 nút nhấn
  int statusPV = digitalRead(btnPV);
  int statusNV = digitalRead(btnNV);
  int statusPlay = digitalRead(btnPlay);

  // KIỂM TRA TRẠNG THÁI VÀ ĐIỀU KHIỂN ĐÈN
  
  // Nếu nút P/V được nhấn (Điện áp sụt về mức LOW)
  if (statusPV == LOW) {
    setColor(255, 0, 0); // Kích hoạt sáng màu ĐỎ
    Serial.println("[Nut bam: P/V] -> LED sang màu DO");
  }
  
  // Nếu nút N/V được nhấn
  else if (statusNV == LOW) {
    setColor(0, 255, 0); // Kích hoạt sáng màu XANH LÁ
    Serial.println("[Nut bam: N/V] -> LED sang màu XANH LA");
  }
  
  // Nếu nút play được nhấn
  else if (statusPlay == LOW) {
    setColor(0, 0, 255); // Kích hoạt sáng màu XANH DƯƠNG
    Serial.println("[Nut bam: Play] -> LED sang màu XANH DUONG");
  }
  
  // Trường hợp không có bất kỳ nút nào được nhấn (Thả tay tự do)
  else {
    setColor(0, 0, 0); // TẮT TOÀN BỘ ĐÈN
  }

  // Chờ một khoảng rất ngắn 20ms để chống nhiễu cơ học khi bấm phím (Debounce)
  delay(20); 
}

// ==========================================
// HÀM XUẤT TÍN HIỆU ĐIỀU KHIỂN ĐỘ SÁNG LED RGB
// ĐÃ ĐƯỢC ĐẢO NGƯỢC LOGIC CHO LED ANODE CHUNG (3.3V)
// ==========================================
void setColor(int redValue, int greenValue, int blueValue) {
  // Lấy 255 trừ đi giá trị để đảo logic:
  // - Nếu truyền vào 255 -> 255-255 = 0V (Chân sụt áp tạo chênh lệch với 3.3V -> SÁNG NHẤT)
  // - Nếu truyền vào 0   -> 255-0 = 255 (Chân lên 3.3V bằng nguồn Anode -> TẮT HOÀN TOÀN)
  analogWrite(redPin, 255 - redValue);
  analogWrite(greenPin, 255 - greenValue);
  analogWrite(bluePin, 255 - blueValue);
}
