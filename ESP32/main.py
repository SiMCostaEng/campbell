import campbell, FTP
import machine
from machine import Pin

UART_3v3 = Pin(5, Pin.OUT, value=1)
print("Comecou")

FTP_OK = FTP.init(False)
if FTP_OK:
    FTP.write("CR800.csv", "Comecou\n", True)

contador = 0
while True:
    recebido_campbell = campbell.read_until(r"\r\n") + '\n' # Escrita de finalização precisa ser idêntico ao código no dispositivo da campbell
    print(recebido_campbell, end="")
    if FTP_OK:
        contador += 1
        FTP.write("CR800.csv", str(contador) + " ; " + recebido_campbell, False)
