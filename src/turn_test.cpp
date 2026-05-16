/* ************************************************************************************************* */
// UCSD ECE 5 Lab 4 — Turn Test Script
// Validates motor wiring and direction before running the full PID line follower.
//
// HOW TO UPLOAD THIS INSTEAD OF main.cpp:
//   In PlatformIO, select the environment "turn-test" from the bottom toolbar
//   (the env switcher shows "esp32-s3-devkitm-1" by default — switch it to "turn-test")
//   then hit Upload. Switch back to "esp32-s3-devkitm-1" for the line follower.
//
// PIN LAYOUT — L298N Dual H-Bridge to ESP32-S3
// ─────────────────────────────────────────────
//
//   L298N Board                    ESP32-S3 GPIO
//   ──────────────────────────────────────────────
//   ENA  (PWM speed, Motor A LEFT)  →  GPIO 42
//   IN1  (direction bit 1, LEFT)    →  GPIO 41
//   IN2  (direction bit 2, LEFT)    →  GPIO 40
//   ENB  (PWM speed, Motor B RIGHT) →  GPIO 37
//   IN3  (direction bit 1, RIGHT)   →  GPIO 39
//   IN4  (direction bit 2, RIGHT)   →  GPIO 38
//
//   Power rails:
//   VCC (motor supply)  →  your 12V battery +
//   GND                 →  battery GND AND ESP32 GND (common ground — REQUIRED)
//   5V  (logic supply)  →  ESP32 5V pin (or its onboard regulator if jumper is set)
//
//   Motor wires:
//   OUT1 / OUT2  →  Left  motor terminals
//   OUT3 / OUT4  →  Right motor terminals
//
// DIRECTION TRUTH TABLE (per motor, same logic for both A and B sides)
// ─────────────────────────────────────────────────────────────────────
//   IN1   IN2   Motor A behavior
//   HIGH  LOW   → Forward
//   LOW   HIGH  → Backward
//   LOW   LOW   → Coast (free spin)
//   HIGH  HIGH  → Brake (locked)
//
//   IN3   IN4   Motor B behavior   (same table, right side)
//
// NOTE: The RIGHT motor (Motor B) is physically mounted in the mirror direction,
//       so in code backwardB() produces physical forward motion for the right wheel.
//       forwardB() produces physical backward for the right wheel.
//       This is already handled in the runMotorAtSpeed() helper below.
//
// WHAT THIS SCRIPT DOES
// ──────────────────────
//   1. Both motors forward  (straight) for 1.5s
//   2. Stop 0.5s
//   3. Turn LEFT  in place  for 1.0s  (left backward, right forward)
//   4. Stop 0.5s
//   5. Turn RIGHT in place  for 1.0s  (left forward, right backward)
//   6. Stop 0.5s
//   7. Repeat forever
//
//   Watch the wheels and confirm:
//     • Step 1: both wheels spin forward
//     • Step 3: left wheel backward, right wheel forward (pivot left)
//     • Step 5: left wheel forward, right wheel backward (pivot right)
//   If any wheel spins the wrong way, swap that motor's two output wires (OUT1↔OUT2
//   for left, OUT3↔OUT4 for right).
/* ************************************************************************************************* */

#include <L298NX2.h>

//                       Left Motor        Right Motor
//                   ENA, IN1, IN2,    ENB, IN3, IN4
L298NX2 DriveMotors(  42,  41,  40,     37,  39,  38);

enum side { LEFT, RIGHT };

const int TEST_SPEED = 80; // 0–255, keep low so nothing crashes during validation

// ── helper: matches main.cpp's runMotorAtSpeed exactly ───────────────────────
// positive speed = physical forward, negative speed = physical backward
void runMotorAtSpeed(side s, int speed) {
  if (s == LEFT) {
    DriveMotors.setSpeedA(abs(speed));
    if (speed >= 0) DriveMotors.forwardA();
    else            DriveMotors.backwardA();
  } else {
    DriveMotors.setSpeedB(abs(speed));
    // Right motor is mounted in reverse, so library backward = physical forward
    if (speed >= 0) DriveMotors.backwardB();
    else            DriveMotors.forwardB();
  }
}

void stopAll() {
  DriveMotors.stopA();
  DriveMotors.stopB();
}

// ── test sequences ────────────────────────────────────────────────────────────
void goStraight(int ms) {
  Serial.println(">> STRAIGHT");
  runMotorAtSpeed(LEFT,  TEST_SPEED);
  runMotorAtSpeed(RIGHT, TEST_SPEED);
  delay(ms);
}

void turnLeft(int ms) {
  Serial.println(">> LEFT TURN (left wheel back, right wheel forward)");
  runMotorAtSpeed(LEFT,  -TEST_SPEED); // left wheel backward
  runMotorAtSpeed(RIGHT,  TEST_SPEED); // right wheel forward
  delay(ms);
}

void turnRight(int ms) {
  Serial.println(">> RIGHT TURN (left wheel forward, right wheel back)");
  runMotorAtSpeed(LEFT,   TEST_SPEED); // left wheel forward
  runMotorAtSpeed(RIGHT, -TEST_SPEED); // right wheel backward
  delay(ms);
}

// ─────────────────────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  Serial.println("\nTurn Test Ready — watching motors");
}

void loop() {
  goStraight(1500);
  stopAll(); delay(500);

  turnLeft(1000);
  stopAll(); delay(500);

  turnRight(1000);
  stopAll(); delay(500);
}
