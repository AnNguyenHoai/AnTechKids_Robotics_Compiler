#include "Sensor_TRCT5000_3CH.h"

void Sensor_TRCT5000_3CH::TRCT5000_init()
{
  pinMode(_pin_L, INPUT);
  pinMode(_pin_C, INPUT);
  pinMode(_pin_R, INPUT); 
}

// Gặp màu đen (hấp thụ tia hồng ngoại) -> Chân xuất mức HIGH (1)
bool Sensor_TRCT5000_3CH::TRCT5000_isLeftDetected_BlackColor()
{
  return digitalRead(_pin_L) == LINE_DETECTED_LEVEL;
}

bool Sensor_TRCT5000_3CH::TRCT5000_isCenterDetected_BlackColor()
{
  return digitalRead(_pin_C) == LINE_DETECTED_LEVEL;
}

bool Sensor_TRCT5000_3CH::TRCT5000_isRightDetected_BlackColor()
{
  return digitalRead(_pin_R) == LINE_DETECTED_LEVEL;
}

// Bất kỳ mắt nào gặp màu đen (true)
bool Sensor_TRCT5000_3CH::TRCT5000_any_BlackColorDetected()
{
  return (TRCT5000_isLeftDetected_BlackColor() || TRCT5000_isCenterDetected_BlackColor() || TRCT5000_isRightDetected_BlackColor());
}

// Tất cả các mắt đều gặp màu đen (true)
bool Sensor_TRCT5000_3CH::TRCT5000_all_BlackColorDetected()
{
  return (TRCT5000_isLeftDetected_BlackColor() && TRCT5000_isCenterDetected_BlackColor() && TRCT5000_isRightDetected_BlackColor());
}

void Sensor_TRCT5000_3CH::TRCT5000_printStatus()
{
  Serial.print("Trạng thái [L|C|R]: ");
  Serial.print(TRCT5000_isLeftDetected_BlackColor() ? "[Đen]" : "[Trắng]");
  Serial.print(TRCT5000_isCenterDetected_BlackColor() ? " [Đen]" : " [Trắng]");
  Serial.print(TRCT5000_isRightDetected_BlackColor() ? " [Đen]" : " [Trắng]");
  
  Serial.print(" | Any Black: ");
  Serial.print(TRCT5000_any_BlackColorDetected() ? "Có" : "Không");
  Serial.print(" | All Black: ");
  Serial.println(TRCT5000_all_BlackColorDetected() ? "Có" : "Không");
}

