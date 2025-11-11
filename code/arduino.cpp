#include <Wire.h>
#include <Adafruit_FRAM_I2C.h>

Adafruit_FRAM_I2C fram = Adafruit_FRAM_I2C();

const uint16_t FRAM_SIZE = 32768; // Change this if you have diffrent fram size
bool fram_initialized = false;

void setup() {
    Serial.begin(115200);
    while (!Serial) delay(10);

    if (!fram.begin()) {
        Serial.println("ERROR: FRAM not found");
        fram_initialized = false;
        return;
    }
    
    fram_initialized = true;
    Serial.println("READY: FRAM initialized");
    Serial.println("READY: Commands: ERASE, WRITE:data, READ:bytes, EXPORT");
}

void loop() {
    if (Serial.available()) {
        String cmd = Serial.readStringUntil('\n');
        cmd.trim();

        if (!fram_initialized) {
            Serial.println("ERROR: FRAM not initialized");
            return; 
        }

        if (cmd == "ERASE") {
            eraseFram();
        }
        else if (cmd.startsWith("WRITE:")) {
            String data = cmd.substring(6);
            writeFram(data);
        }
        else if (cmd.startsWith("READ:")) {
            int n = cmd.substring(5).toInt();
            readFram(n);
        }
        else if (cmd == "EXPORT") {
            exportFram();
        }
        else if (cmd.length() > 0) {
            Serial.println("ERROR: Unknown command");
        }
    }
}


void eraseFram() {
    Serial.print("ERASING...");
    
    for (uint16_t i = 0; i < FRAM_SIZE; i++) {
        fram.write(i, 0x00);
        
        if (i % 1024 == 0) {
            Serial.print(".");
            delay(1);
        }
    }
    
    Serial.println("DONE");
    Serial.println("ERASED: Full FRAM erased successfully");
}


void writeFram(String data) {
    if (data.length() == 0) {
        Serial.println("ERROR: No data provided");
        return;
    }
    
    uint16_t writeLength = min((int)data.length(), FRAM_SIZE - 1);
    
    for (uint16_t i = 0; i < writeLength; i++) {
        fram.write(i, data[i]);
        
        if (i % 100 == 0) {
            uint8_t verify = fram.read(i);
            if (verify != data[i]) {
                Serial.println("ERROR: Write verification failed at position " + String(i));
                return;
            }
        }
    }
    
    fram.write(writeLength, 0x00);
    

    for (uint16_t i = writeLength + 1; i < FRAM_SIZE; i++) {
        fram.write(i, 0x00);
    }
    
    Serial.println("WRITTEN: Data written successfully");
}


void readFram(int n) {
    if (n <= 0 || n > FRAM_SIZE) {
        Serial.println("ERROR: Invalid read length. Use 1-" + String(FRAM_SIZE));
        return;
    }
    
    Serial.print("DATA: ");
    bool data_found = false;
    for (int i = 0; i < n; i++) {
        uint8_t data = fram.read(i);
        
        if (data == 0) {
            break;
        }
        
        data_found = true;
        
        if (data >= 32 && data <= 126) {
            Serial.write(data);
        } else {
            Serial.print("[" + String(data, HEX) + "]");
        }
    }
    Serial.println();
    
    if (!data_found) {
        Serial.println("READ: Memory is empty.");
    } else {
        Serial.println("READ: Completed reading.");
    }
}


void exportFram() {
    Serial.println("BEGIN_EXPORT");
    
    for (uint16_t i = 0; i < FRAM_SIZE; i += 16) {
        if (i % 256 == 0 && i > 0) Serial.println();
        
        char addr[5];
        sprintf(addr, "%04X", i);
        Serial.print(addr);
        Serial.print(": ");
        
        for (uint8_t j = 0; j < 16; j++) {
            if (i + j < FRAM_SIZE) {
                uint8_t data = fram.read(i + j);
                if (data < 16) Serial.print("0");
                Serial.print(data, HEX);
                Serial.print(" ");
            }
        }
        
        Serial.print(" ");
        
        for (uint8_t j = 0; j < 16; j++) {
            if (i + j < FRAM_SIZE) {
                uint8_t data = fram.read(i + j);
                if (data >= 32 && data <= 126) {
                    Serial.write(data);
                } else {
                    Serial.print(".");
                }
            }
        }
        Serial.println();
        
        if (i % 1024 == 0) {
            delay(10);
        }
    }
    
    Serial.println("END_EXPORT");
}
