import os
import requests
from datetime import datetime
from pathlib import Path
import cryptoF as crypto
import uuid
import sys

def download(log_callback=print):
	log_callback("Iniciando proceso de descarga...")
	config = {}
	if getattr(sys, 'frozen', False):
		ruta_base = os.path.dirname(sys.executable)
	else:
		ruta_base = os.path.dirname(os.path.abspath(__file__))
	path_archivo = os.path.join(ruta_base, ".conf")

	with open(path_archivo, 'r') as f:
		lines = f.readlines()
		for line in lines:
			key, value = line.strip().split('=', 1)
			config[key] = value
	downloads_folder = config.get('DOWNLOADS')
	user = config.get('USER')
	password = config.get('PASSWORD')
	buckets = eval(config.get('BUCKETS'))
	id = str(uuid.uuid4())
	os.makedirs(downloads_folder, exist_ok=True)
	files = []
	url_auth = 'http://localhost:8071/api'
	url_storage = 'http://localhost:5070/api'

	# Obtener token de autenticación
	token_response = requests.post(f'{url_auth}/token', data={"username": user, "password": password}, headers={
		"Content-Type": "application/x-www-form-urlencoded"
	})
	if token_response.status_code == 200:
		token = token_response.json().get("access_token")
		log_callback(f"Autenticación exitosa")
	else:
		log_callback(f"Error en la autenticación")
		print(f"Error en la autenticación: {token_response.status_code} {token_response.text}")
		sys.exit(1)

	# Obtener los segmentos de cada archivo para su posterior descarga
	def getSegments(users=buckets):
		for bucket in buckets:
			print("token", token)
			response = requests.post(f'{url_storage}/get-md', json={"user": user, "bucket": bucket, "token": token, "request_id": id})
			if response.status_code == 200:
				metadata = response.json()
				if len(metadata['files']) > 0:
					for file in metadata['files']:
						files.append(file)
				else:
					log_callback(f"Fallo en la extracción de segmentos del bucket {bucket}: {response.status_code} {response.text}")
			else:
				print(f"Error al obtener los segmentos del bucket {bucket}: {response.status_code} {response.text}")
				log_callback(f"Bucket {bucket} no encontrado para el usuario {user}")
				

	def downloadFile(file):
		log_callback(f"Descargando {file['file']} de bucket {file['segments'][0]['user']}")
		user_folder = os.path.normpath(f"{downloads_folder}/{file['segments'][0]['user']}")
		os.makedirs(user_folder, exist_ok=True)
		with open(f"{user_folder}/{file['file']}", "wb") as f:
			for segment in file['segments']:
				response = requests.post(f'{url_storage}/download', json={
					"path": segment["path"],
					"start_position": segment["start_position"],
					"end_position": segment["end_position"],
					"chunk_size": segment["chunk_size"],
					"request_id": id,
					"token": token
				})
				if response.status_code == 200:
					chunk_data = response.content
					f.write(chunk_data)
					log_callback(f"Segmento descargado [{segment['start_position']} - {segment['end_position']}] del archivo {file['file']}")
				else:
					log_callback(f"Error al descargar segmento [{segment['start_position']} - {segment['end_position']}] del archivo {file['file']}: {response.status_code} {response.text}")
			with open(f"{user_folder}/registry.txt", "a") as f:
				f.write(f"Archivo {file['file']} descargado exitosamente. {datetime.now()}.\n")

	def decrypt(file):
		encrypted_path = os.path.normpath(f"{downloads_folder}/{file['segments'][0]['user']}/{file['file']}")
		decrypted_path = os.path.normpath(f"{downloads_folder}/{file['segments'][0]['user']}/{Path(file['file']).stem}")
		crypto.descifrar_archivo(encrypted_path, decrypted_path)
		log_callback(f"Descifrado el archivo {file['file']} en {decrypted_path}")

	getSegments(buckets)

	# print(files)
	for file in files:
		# print(file)
		# break
		downloadFile(file)
		decrypt(file)

	response_remove = requests.post(f'{url_storage}/save/remove', json={"file_id": id})

if __name__ == "__main__":
	download()