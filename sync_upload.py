import os
import requests
import cryptoF as crypto
import json
import uuid
import sys
config = {}

def upload(log_callback=print):
	log_callback("Iniciando proceso de subida de archivos...")
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

	upload_folder = config.get('UPLOADS')
	downloads_folder = config.get('DOWNLOADS')
	user = config.get('USER')
	password = config.get('PASSWORD')
	bucket = config.get('BUCKET')
	chunk_size = 1024 * 1024
	token = None
	url_auth = 'http://localhost:8071/api'
	url_storage = 'http://localhost:5070/api'
	os.makedirs(upload_folder, exist_ok=True)
	os.makedirs(downloads_folder, exist_ok=True)

	# Obtener token de autenticación
	token_response = requests.post(f'{url_auth}/token', data={"username": user, "password": password}, headers={
		"Content-Type": "application/x-www-form-urlencoded"
	})
	if token_response.status_code == 200:
		token = token_response.json().get("access_token")
		# print(f"Token obtained successfully: {token}")
		log_callback("Autenticación exitosa")
	else:
		log_callback(f"Error en la autenticación")
		sys.exit(1)

	# Obtener los segmentos de cada archivo para su posterior subida
	def getSegments(file):
		position = 0
		positions = []
		while position < file["size"]:
			end_position = position + chunk_size if ((position + chunk_size) < file["size"]) else position + (file["size"] - position)
			# positions.append({"storage_path": file["storage_path"], "user": user, "path": file["path"], "filename": file["file_name"],"start_position": position, "end_position": end_position, "file_size": file["size"], "chunk_size": chunk_size})
			positions.append({
				"user": user,  
				"filename": file["file_name"],
				"start_position": position,
				"end_position": end_position, 
				"file_size": file["size"], 
				"chunk_size": chunk_size,
				"bucket": file["bucket"],
				"token": token,
				"id_file": file['id']
			})
			position = position + chunk_size
		return positions

	# Cifrar archivos
	for root, directories, files in os.walk(upload_folder):
		for file_name in files:
			# log_callback(f"Encrypting {file_name}...")
			original_path = os.path.join(root, file_name)
			encrypted_path = os.path.join(root, f"{file_name}.enc")
			crypto.cifrar_archivo(original_path, encrypted_path)


	# Obtener la lista de archivos cifrados para su posterior subida
	list_of_files = []
	for root, directories, files in os.walk(upload_folder):
		for file_name in files:
			extension = os.path.splitext(file_name)[1]
			if extension == ".enc":
				file = {
					'file_name': file_name, 
					'path': os.path.join(root, file_name), 
					'size': os.path.getsize(os.path.join(root, file_name)), 
					'extension': os.path.splitext(file_name)[1],
					# 'storage_path': root.replace(upload_folder, '').lstrip(os.sep),
					'bucket': bucket,
					'id': str(uuid.uuid4())
				}
				list_of_files.append(file)

	# Subir archivos cifrados por segmentos
	for file in list_of_files:
		segments = getSegments(file)
		# log_callback(json.dumps(segments))
		detener = False
		for segment in segments:
			with open(file["path"], "rb") as f:
				f.seek(segment["start_position"])
				chunk_data = f.read(segment["chunk_size"])
				files = {
					'files': (segment["filename"], chunk_data)
				}
				log_callback("Subiendo segmento [{start} - {end}] del archivo {file} al bucket {bucket}".format(
					start=segment["start_position"],
					end=segment["end_position"],
					file=segment["filename"],
					bucket=segment["bucket"]
				))
				response = requests.post(f'{url_storage}/save', files=files, data=segment)
				# log_callback(response.status_code, response.text)
				if response.status_code == 403:
					log_callback(json.dumps(response.json().get("error")))
					detener = True
					break
				elif response.status_code == 200:
					# log_callback("Segmento subido correctamente")
					log_callback("Segmento subido correctamente")
				else:
					log_callback(response.status_code, response.text)
					detener = True
					log_callback(f"Error al subir segmento [{segment['start_position']} - {segment['end_position']}] del archivo {segment['filename']}")
					log_callback("Reintente cargar nuevamente.")
					break
		if detener:
			break
		response_remove = requests.post(f'{url_storage}/save/remove', json={"id_file": file["id"]})
		# log_callback(response_remove.status_code, response_remove.text)
		# os.remove(file["path"])
	limpiar_carpeta_subida()

# ELIMINAR TODOS LOS ARCHIVOS .enc DE LA CARPETA DE SUBIDA
def limpiar_carpeta_subida():
	upload_folder = config.get('UPLOADS')
	for root, directories, files in os.walk(upload_folder):
		for file_name in files:
			extension = os.path.splitext(file_name)[1]
			if extension == ".enc":
				os.remove(os.path.join(root, file_name))

if __name__ == "__main__":
	upload()