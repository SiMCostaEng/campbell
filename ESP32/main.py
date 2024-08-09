import campbell, FTP
import machine
from machine import Pin

FILE_NAME = "Ilha_Polvora.csv"

UART_3v3 = Pin(5, Pin.OUT, value=1)
print("Comecou")

FTP.reset()
FTP_OK = False

contador = 0
while True:
    recebido_campbell = campbell.read_until(r"\r\n") # Escrita de finalização precisa ser idêntico ao código no dispositivo da campbell
    try:
        FTP_OK = FTP.init(True)
        if FTP_OK:
            contador += 1
            FTP.write(FILE_NAME, str(contador) + " ; " + recebido_campbell, False)
        FTP.reset()
        print("Success ", end="")
    except:
        print("Error ", end="")
    print(f"Send {recebido_campbell}", end="")
    recebido_campbell = ""
