import machine
from machine import UART

# Inicialização do módulo para leitura do campbell_device
campbell_device = UART(1, baudrate=115200, rx=25, tx=33)

def read_until(sinal_fim):
    counter = 0
    counter_max = len(sinal_fim)
    mensagem = ""
    
    while counter < counter_max:
        recebido = campbell_device.read(1)
        if recebido:
            try:
                recebido_2 = recebido.decode('utf-8')
                if recebido_2 == sinal_fim[counter]:
                    counter += 1
                else:
                    # print(recebido_2, end='')
                    mensagem += recebido_2
            except:
                print(f"Erro decoding: {recebido}")
                
    print(f"Recebido:\t\t{mensagem}")
    return(mensagem)

def write(message):
    campbell_device.write(message.encode())  # Escrever como bytes
    print(message)
