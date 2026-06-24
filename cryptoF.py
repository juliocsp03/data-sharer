from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import os
from pathlib import Path

LLAVE = bytes.fromhex('ksdjcnsdkcjdsnckjdscnsdjcnsdkjcnsdkjcnskdjcnskdjcnskdjcnskdjcnskdjcn')
def cifrar_archivo(ruta_entrada, ruta_salida, llave = LLAVE):
    cipher = AES.new(llave, AES.MODE_GCM)
    
    with open(ruta_entrada, 'rb') as f_in, open(ruta_salida, 'wb') as f_out:
        f_out.write(cipher.nonce)
        
        while True:
            chunk = f_in.read(64 * 1024)
            if len(chunk) == 0:
                break
            f_out.write(cipher.encrypt(chunk))
        tag = cipher.digest()
        f_out.write(tag)

def descifrar_archivo(ruta_entrada, ruta_salida, llave = LLAVE):
    tamano_archivo = os.path.getsize(ruta_entrada)
    
    with open(ruta_entrada, 'rb') as f_in:
        nonce = f_in.read(16)
        cuerpo_cifrado_tamano = tamano_archivo - 32 
        
        cipher = AES.new(llave, AES.MODE_GCM, nonce=nonce)
        
        with open(ruta_salida, 'wb') as f_out:
            leido = 0
            while leido < cuerpo_cifrado_tamano:
                chunk_size = min(64 * 1024, cuerpo_cifrado_tamano - leido)
                chunk = f_in.read(chunk_size)
                f_out.write(cipher.decrypt(chunk))
                leido += len(chunk)
            
            tag = f_in.read(16)
            try:
                cipher.verify(tag)
            except ValueError:
                os.remove(ruta_salida)
    os.remove(ruta_entrada)