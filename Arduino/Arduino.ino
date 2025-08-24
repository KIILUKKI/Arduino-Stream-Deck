// === USER CONFIGURATION SECTION === //
const int buttonPins[] = {2, 3, 4, 5, 6, 7};  // Digital pins for 6 buttons
const int potPins[] = {A0};                   // Only one potentiometer (A0)
// === END USER CONFIGURATION === //

const int numButtons = sizeof(buttonPins) / sizeof(buttonPins[0]);
const int numPots = sizeof(potPins) / sizeof(potPins[0]);

void setup() {
  Serial.begin(9600);

  // Set button pins as INPUT_PULLUP (active low)
  for (int i = 0; i < numButtons; i++) {
    pinMode(buttonPins[i], INPUT_PULLUP);
  }
}

void loop() {
  // --- Read buttons ---
  for (int i = 0; i < numButtons; i++) {
    int pressed = (digitalRead(buttonPins[i]) == LOW) ? 1 : 0; // 1 = pressed
    Serial.print(pressed);
    Serial.print(",");
  }

  // --- Read potentiometer(s) ---
  for (int j = 0; j < numPots; j++) {
    int value = analogRead(potPins[j]); // range 0–1023
    Serial.print(value);
    if (j < numPots - 1) Serial.print(",");
  }

  Serial.println();  // End line for one full update
  delay(10);         // ~100 Hz update rate
}
