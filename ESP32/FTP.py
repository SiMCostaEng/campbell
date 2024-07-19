import machine
from machine import Pin
import time

# Define as constantes
SIM800 = machine.UART(2, baudrate=9600)
FTP_Reset = Pin(15, Pin.OUT, value=1)

# Constantes de Configuração FTP
FTP_IP = '200.132.216.21'
FTP_PORT = 21
FTP_USER = 'datalogger_0'
FTP_PASS = 'd4t4fl0w$'
FTP_APN = 'java.claro.com.br'

# Constantes de Tempo
RETRY_MAX_COUNTER = 5
WAIT_TIME = 0.5

# Flag de modo de depuração
debug = False

write_initiated = False

def extrair_texto(mensagem_str):
    """
    Extrai texto e número de uma string de mensagem.

    :param mensagem_str: String de mensagem para extrair os dados.
    :return: Tupla (texto, número) se bem-sucedido, None caso contrário.
    """
    indice_inicio = mensagem_str.find("+FTPGET: 2,")

    if indice_inicio != -1:
        # Obter o número correspondente
        numero_inicio = indice_inicio + len("+FTPGET: 2,")
        numero_fim = mensagem_str.find("\r\n", numero_inicio)
        numero = mensagem_str[numero_inicio:numero_fim]
        
        # Encontrar o índice de \r\n após o número
        indice_texto_inicio = numero_fim + len("\r\n")
        indice_texto_fim = mensagem_str.find("\r\n", indice_texto_inicio)
        
        # Extrair o texto
        texto = mensagem_str[indice_texto_inicio:indice_texto_fim]

        return texto, numero

    return None

def sendAT(command, expected_response=""):
    """
    Envia um comando AT para o módulo SIM800 e verifica a resposta esperada.

    :param command: Comando AT a ser enviado.
    :param expected_response: Resposta esperada do módulo.
    :return: True se a resposta esperada for recebida, False caso contrário.
    """
    global debug
    if expected_response:
        if debug:
            print(f'{command}')
        for _ in range(RETRY_MAX_COUNTER):
            SIM800.write(f'{command}\r\n')
            for _ in range(RETRY_MAX_COUNTER):
                response = SIM800.read()
                if response is not None:
                    if debug:
                        print(f'\t{response}')
                    response = response.decode('utf-8')
                    if expected_response in response:
                        return True
                time.sleep(WAIT_TIME)
        return False
    else:
        SIM800.write(command, len(command))
        if debug:
            print(command)
        time.sleep(WAIT_TIME)
        return True

def sendAT_read(command, contagem_max):
    """
    Envia um comando AT para leitura com o módulo SIM800.

    :param command: Comando AT a ser enviado.
    :param contagem_max: Contagem máxima para o comando.
    :return: Tupla (True, mensagem_recebida) se bem-sucedido, (False, "") caso contrário.
    """
    global debug
    mensagem_completa = ""
    contagem = contagem_max
    while True:
        if debug:
            print(command)
        for _ in range(RETRY_MAX_COUNTER):
            SIM800.write(f'{command}{contagem_max}\r\n')
            for _ in range(RETRY_MAX_COUNTER):
                response = SIM800.read()
                if debug:
                    print(f'\t{response}')

                if response is not None:
                    retorno = response.decode('utf-8')
                    retorno, contagem = extrair_texto(response.decode('utf-8'))
                    mensagem_completa += retorno
                    if int(contagem) != contagem_max:
                        return True, mensagem_completa
                time.sleep(WAIT_TIME)
        return False, ""

def init(debug_mode):
    """
    Inicializa a comunicação FTP com o módulo SIM800.

    :param debug_mode: Modo de depuração. Se True, exibe mensagens de depuração.
    :return: True se a inicialização for bem-sucedida, False caso contrário.
    """
    print("FTP init")
    global debug
    debug = debug_mode
    commands = [
        ("AT", "OK"),
        ("AT+CREG?", "OK"),
        # ("AT+CBC", "OK"),
        ("AT+CSQ", "OK"),
        ("AT+SAPBR=3,1,\"Contype\",\"GPRS\"", "OK"),
        (f"AT+SAPBR=3,1,\"APN\",\"{FTP_APN}\"", "OK"),
        ("AT+SAPBR=2,1", "OK"),
        ("AT+SAPBR=1,1", "OK"),
        ("AT+FTPCID=1", "OK"),
        (f"AT+FTPSERV=\"{FTP_IP}\"", "OK"),
        ("AT+FTPPORT=\"21\"", "OK"),
        (f"AT+FTPUN=\"{FTP_USER}\"", "OK"),
        (f"AT+FTPPW=\"{FTP_PASS}\"", "OK")
    ]
    for cmd, response in commands:
        if not sendAT(cmd, response):
            print(f'\t\tFalha ao executar comando {cmd}')
            return False
    return True

def write(filename, data, create):
    """
    Escreve dados em um arquivo remoto via FTP.

    :param filename: Nome do arquivo remoto.
    :param data: Dados a serem escritos no arquivo.
    :param create: Se True, cria um novo arquivo; se False, faz append no arquivo existente.
    :return: True se a operação for bem-sucedida, False caso contrário.
    """
    global write_initiated
    if not(write_initiated):
        if create:
            print(f"FTP create file:\t{filename}")

            commands = [
                (f'AT+FTPPUTNAME="{filename}"', "OK"),
                ("AT+FTPPUTPATH=\"/\"", "OK"),
                ("AT+FTPPUT=1", "OK")
            ]
        else:
            print(f"FTP write file:\t{filename}")

            commands = [
                ("AT+FTPPUTOPT=APPE", "OK"),  # Comando para fazer o append no arquivo ou não
                (f'AT+FTPPUTNAME="{filename}"', "OK"),
                ("AT+FTPPUTPATH=\"/\"", "OK"),
                ("AT+FTPPUT=1", "OK")
            ]

        for cmd, response in commands:
            if not sendAT(cmd, response):
                print(f'\t\tFalha ao executar comando {cmd}')
                return False
        
        write_initiated = True

    str_len = data.find('\n')
    qtde_linhas = int(1000 / str_len)
    caracteres_por_grupo = qtde_linhas * str_len
    data_len = len(data)

    data_part = ""
    data_part_len = 0
    for i in range(0, data_len, caracteres_por_grupo):
        data_part = data[i:i + caracteres_por_grupo]
        data_part_len = len(data_part)

        sendAT(f"AT+FTPPUT=2,{data_part_len}", f"FTPPUT: 2,{data_part_len}")
        sendAT(data_part, "")

    return True

def reset():
    """
    Reseta a comunicação FTP.

    Realiza uma reinicialização do módulo FTP.
    """
    print("FTP reset\n")
    
    global write_initiated
    if write_initiated:
        sendAT("AT+FTPPUT=2,0", "+FTPPUT: 1,0")
        write_initiated = False

    FTP_Reset.off()
    time.sleep(1)
    FTP_Reset.on()
    return True

def read(filename):
    """
    Lê um arquivo remoto via FTP.

    :param filename: Nome do arquivo remoto a ser lido.
    :return: True se a operação for bem-sucedida, False caso contrário.
    """
    print("FTP read file")

    commands = [
        (f'AT+FTPGETNAME="{filename}"', "OK"),
        ("AT+FTPGETPATH=\"/\"", "OK"),
        ("AT+FTPGET=1", "1,1")
    ]
    for cmd, response in commands:
        if not sendAT(cmd, response):
            print(f'\t\tFalha ao executar comando {cmd}')
            return False

    fail_check, comandos_recebidos = sendAT_read("AT+FTPGET=2,", 30)
    if not fail_check or len(comandos_recebidos) == 0:
        fail_check, comandos_recebidos = sendAT_read("AT+FTPGET=2,", 30)

    return True
