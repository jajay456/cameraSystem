/*
  KROSS Replay — court button firmware (ESP32)

  Wired per esp32_button/WIRING.th.md: one leg of the momentary push button
  to GPIO4, the other to GND. Uses the ESP32's internal pull-up, so GPIO4
  reads HIGH normally and LOW while the button is held down.

  On each press, sends the same POST /api/trigger that the on-screen and
  phone buttons use (see app/main.py's api_trigger), with this court's
  button_token so the server can tell a real court button apart from a
  spoofed request (see the token check added in api_trigger).

  Fill in the six values below for this specific court, then Sketch ->
  Upload. Needs the "esp32" board package installed in Arduino IDE
  (Boards Manager -> search "esp32" -> install "esp32 by Espressif
  Systems") — WiFi.h and HTTPClient.h come with it, no extra libraries.
*/

#include <WiFi.h>
#include <HTTPClient.h>

// ---- fill in for this court ----
const char* WIFI_SSID     = "YOUR_WIFI_NAME";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* SERVER_HOST   = "192.168.1.182";   // the mini-PC's LAN IP — same
                                                // one it prints on startup
                                                // ("from your phone:
                                                // http://<this>:8000/m").
                                                // Give that machine a
                                                // static IP / DHCP
                                                // reservation on the router
                                                // so it never changes.
const int   SERVER_PORT   = 8000;
const char* COURT_ID      = "court_1";
const char* BUTTON_TOKEN  = "onnut-court_1-ac8761";  // courts.court_1
                                                       // .button_token in
                                                       // config.yaml

// ---- wiring (see WIRING.th.md) ----
const int BUTTON_PIN = 4;   // GPIO4
const int LED_PIN    = 2;   // most DevKit boards have an onboard LED here;
                             // purely a "did it fire" indicator, optional —
                             // remove the blinkLed() calls below if your
                             // board doesn't have one

void connectWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(400);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("Connected, IP: ");
  Serial.println(WiFi.localIP());
}

void blinkLed(int times, int ms) {
  for (int i = 0; i < times; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(ms);
    digitalWrite(LED_PIN, LOW);
    delay(ms);
  }
}

void sendTrigger() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected -- reconnecting...");
    connectWiFi();
  }

  HTTPClient http;
  String url = String("http://") + SERVER_HOST + ":" + SERVER_PORT + "/api/trigger";
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(5000);

  String body = String("{\"court\":\"") + COURT_ID +
                "\",\"token\":\"" + BUTTON_TOKEN + "\"}";
  int status = http.POST(body);

  if (status > 0) {
    Serial.printf("trigger -> HTTP %d: %s\n", status, http.getString().c_str());
    if (status == 200) {
      blinkLed(2, 120);   // two quick blinks = captured
    } else {
      blinkLed(1, 600);   // one long blink = rejected (cooldown, bad token, ...)
    }
  } else {
    Serial.printf("trigger failed: %s\n", http.errorToString(status).c_str());
    blinkLed(4, 80);      // fast flicker = couldn't reach the server at all
  }
  http.end();
}

void setup() {
  Serial.begin(115200);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pinMode(LED_PIN, OUTPUT);
  connectWiFi();
}

void loop() {
  static bool lastPressed = false;
  bool pressed = (digitalRead(BUTTON_PIN) == LOW);

  if (pressed && !lastPressed) {
    delay(50);  // debounce
    if (digitalRead(BUTTON_PIN) == LOW) {
      Serial.println("button pressed -> sending trigger");
      sendTrigger();
    }
  }
  lastPressed = pressed;

  delay(20);
}
