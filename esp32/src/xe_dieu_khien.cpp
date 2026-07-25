#include <WiFi.h>
#include <WebServer.h>
#include <WebSocketsServer.h>

const char* ssid = "IOP_AP";
const char* password = "wirelessofiop";

#define ENA 19
#define IN1 18
#define IN2 5
#define ENB 4
#define IN3 17
#define IN4 16
#define trig 14
#define echo 12

bool running = false;

WebServer server(80);
WebSocketsServer webSocket = WebSocketsServer(81);

void setup() {
  Serial.begin(115200);
  
  // Connect WiFi
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  Serial.println("Connecting WiFi...");
  while(WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  // Setup pins
  pinMode(trig, OUTPUT);
  pinMode(echo, INPUT);
  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(ENB, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  digitalWrite(ENA, HIGH);
  digitalWrite(ENB, HIGH);
  stopMotor();

  // Web Server
  server.on("/", handleRoot);
  server.begin();

  // WebSocket
  webSocket.begin();
  webSocket.onEvent(webSocketEvent);

  Serial.println("WebSocket server started on port 81");
  Serial.println("Open browser: http://" + WiFi.localIP().toString());
}

void loop() {
  server.handleClient();
  webSocket.loop();

  // Read distance sensor
  digitalWrite(trig, LOW);
  delayMicroseconds(2);
  digitalWrite(trig, HIGH);
  delayMicroseconds(10);
  digitalWrite(trig, LOW);

  long duration = pulseIn(echo, HIGH);
  float distance = duration * 0.0343 / 2;
  
  // Send distance to app via WebSocket
  if (webSocket.connectedClients() > 0) {
    webSocket.broadcastTXT(String(distance).c_str());
  }

  // Auto stop if obstacle detected
  if (running && distance <= 8) {
    stopMotor();
    running = false;
    if (webSocket.connectedClients() > 0) {
      webSocket.broadcastTXT("STOPPED");
    }
  }

  // Serial commands for testing
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd == "run") {
      forward();
      Serial.println("RUN");
    } else if (cmd == "stop") {
      stopMotor();
      Serial.println("STOP");
    }
  }
  
  delay(50);
}

// ===== WEBSOCKET EVENT HANDLER =====
void webSocketEvent(uint8_t num, WStype_t type, uint8_t * payload, size_t length) {
  switch(type) {
    case WStype_DISCONNECTED:
      Serial.printf("[%u] Disconnected!\n", num);
      stopMotor();  // Auto stop for safety
      break;
      
    case WStype_CONNECTED:
      {
        IPAddress ip = webSocket.remoteIP(num);
        Serial.printf("[%u] Connected from %d.%d.%d.%d\n", num, ip[0], ip[1], ip[2], ip[3]);
        webSocket.sendTXT(num, "CONNECTED");
      }
      break;
      
    case WStype_TEXT:
      {
        String cmd = String((char*)payload);
        Serial.printf("[%u] CMD: %s\n", num, cmd.c_str());
        
        if (cmd == "forward" || cmd == "forward_press") {
          forward();
        } else if (cmd == "backward" || cmd == "backward_press") {
          backward();
        } else if (cmd == "left" || cmd == "left_press") {
          left();
        } else if (cmd == "right" || cmd == "right_press") {
          right();
        } else if (cmd == "stop" || cmd == "stop_press") {
          stopMotor();
        }
      }
      break;
      
    case WStype_BIN:
      Serial.printf("[%u] Received binary data\n", num);
      break;
  }
}

// ===== MOTOR CONTROL FUNCTIONS =====
void forward() {
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
  running = true;
  Serial.println(">> Forward");
}

void backward() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);
  running = true;
  Serial.println(">> Backward");
}

void stopMotor() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
  running = false;
  Serial.println(">> Stop");
}

void left() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
  running = true;
  Serial.println(">> Left");
}

void right() {
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);
  running = true;
  Serial.println(">> Right");
}

// ===== WEB PAGE =====
void handleRoot() {
  String html = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { touch-action: none; }
        body {
            text-align: center;
            font-family: Arial;
            background: #1a1a2e;
            color: white;
            margin: 0;
            padding: 20px;
            user-select: none;
            -webkit-user-select: none;
        }
        h1 { color: #e94560; margin-bottom: 20px; }
        .container { max-width: 400px; margin: auto; }
        .status { color: #00ff00; font-size: 18px; margin: 10px 0; }
        .distance { color: #ff9800; font-size: 20px; margin: 10px 0; }
        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 10px;
            max-width: 350px;
            margin: 20px auto;
        }
        .btn {
            padding: 25px;
            font-size: 30px;
            border: none;
            border-radius: 15px;
            cursor: pointer;
            color: white;
            touch-action: none;
            transition: transform 0.1s;
        }
        .btn:active { transform: scale(0.9); }
        .btn-up { background: #4CAF50; }
        .btn-down { background: #f44336; }
        .btn-left { background: #ff9800; }
        .btn-right { background: #2196F3; }
        .btn-stop { 
            background: #ff0000;
            padding: 25px 30px;
            font-size: 24px;
        }
        .btn-run {
            background: #00c853;
            padding: 15px 50px;
            font-size: 20px;
            margin-top: 10px;
        }
        .btn-wide { grid-column: span 1; }
        .control-info {
            color: #888;
            font-size: 14px;
            margin-top: 20px;
            padding: 10px;
            background: #16213e;
            border-radius: 10px;
        }
        .emoji-big { font-size: 35px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Robot Control</h1>
        
        <div class="status" id="status">Status: Connecting...</div>
        <div class="distance" id="distance">Distance: -- cm</div>
        
        <div class="grid">
            <div></div>
            <div><button class="btn btn-up" 
                    ontouchstart="sendCmd('forward_press')" 
                    ontouchend="sendCmd('stop_press')"
                    onmousedown="sendCmd('forward_press')"
                    onmouseup="sendCmd('stop_press')">⬆</button></div>
            <div></div>
            
            <div><button class="btn btn-left" 
                    ontouchstart="sendCmd('left_press')" 
                    ontouchend="sendCmd('stop_press')"
                    onmousedown="sendCmd('left_press')"
                    onmouseup="sendCmd('stop_press')">⬅</button></div>
            <div><button class="btn btn-stop" onclick="sendCmd('stop')">⏹</button></div>
            <div><button class="btn btn-right" 
                    ontouchstart="sendCmd('right_press')" 
                    ontouchend="sendCmd('stop_press')"
                    onmousedown="sendCmd('right_press')"
                    onmouseup="sendCmd('stop_press')">➡</button></div>
            
            <div></div>
            <div><button class="btn btn-down" 
                    ontouchstart="sendCmd('backward_press')" 
                    ontouchend="sendCmd('stop_press')"
                    onmousedown="sendCmd('backward_press')"
                    onmouseup="sendCmd('stop_press')">⬇</button></div>
            <div></div>
        </div>
        
        <button class="btn btn-run" onclick="sendCmd('forward')">▶ RUN</button>
        
        <div class="control-info">
            💡 Press and hold arrows to move<br>
            Release to stop automatically
        </div>
    </div>

    <script>
        var ws = new WebSocket('ws://' + window.location.hostname + ':81/');
        
        ws.onopen = function() {
            document.getElementById('status').innerHTML = 'Status: Connected ✅';
            document.getElementById('status').style.color = '#00ff00';
        };
        
        ws.onclose = function() {
            document.getElementById('status').innerHTML = 'Status: Disconnected ❌';
            document.getElementById('status').style.color = '#ff0000';
        };
        
        ws.onmessage = function(event) {
            var data = event.data;
            if (!isNaN(data) && data != '') {
                document.getElementById('distance').innerHTML = 'Distance: ' + data + ' cm';
            } else if (data == 'STOPPED') {
                document.getElementById('status').innerHTML = 'Status: Obstacle! ⚠️';
                document.getElementById('status').style.color = '#ff9800';
                setTimeout(function() {
                    document.getElementById('status').innerHTML = 'Status: Connected ✅';
                    document.getElementById('status').style.color = '#00ff00';
                }, 1500);
            }
        };
        
        function sendCmd(cmd) {
            if (ws.readyState == WebSocket.OPEN) {
                ws.send(cmd);
            }
        }
        
        // Prevent scroll on touch
        document.addEventListener('touchmove', function(e) {
            e.preventDefault();
        }, { passive: false });
    </script>
</body>
</html>
  )rawliteral";
  server.send(200, "text/html", html);
}