import campbell
import machine

while True:
    recebido_campbell = campbell.read_until(r"\r\n") # Escrita de finalização precisa ser idêntico ao código no dispositivo da campbell
    print(recebido_campbell)
