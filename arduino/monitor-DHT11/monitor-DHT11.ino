
#include "DHT.h"
#define DHTPIN 2
#define DHTTYPE DHT11

DHT dht(DHTPIN, DHTTYPE);

void setup() {
  // funcao de setup
  Serial.begin(9600);
  dht.begin();

  while (!Serial) {}
}

void loop() {
  // loop principal
  delay(5000);
  float humi = dht.readHumidity();
  float temp = dht.readTemperature();
  if (isnan(humi)) {
    Serial.println("error readding humidity");
  } else {
    Serial.print("sensor humidity ");
    Serial.println(humi);
  }
  if (isnan(temp)) {
    Serial.println("error reading temperature");
  } else {
    Serial.print("sensor temperature ");
    Serial.println(temp);
  }
}
