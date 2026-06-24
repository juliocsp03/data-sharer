import os
import hashlib

def getMetadata(res):
    type = None
    data = []
    if (os.path.isdir(res)):
        data = dirs(res)
        type = "directorio"
    elif (os.path.isfile(res)):
        data.append(files(res))
        type = "archivo"
    else:
        print("Entrada inválida")
    return {"type": type, "resources": data}

def getSegmentData(segment):
    data = None
    with open(segment['origin'], "rb") as file:
        file.seek(segment['start_position'])
        data = file.read(segment['chunk_size'])
    return data

def files(res):
    with open(res, "rb") as file:
        digest = getFileHash(res)
    return {"hash": digest, "path": res, "size": os.path.getsize(res), "extension": os.path.splitext(res)[1], "state": "none", "temperature": "none", "owners": "none" }

def getFileHash(path):
    hash_func = getattr(hashlib, "sha256")()
    with open(path, "rb") as file:
        while chunk := file.read(1048576):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def saveFile(path, data, name):
     with open(f"{path}{name}", "wb") as file:
          file.write(data)

def dirs(res):
    list_metadata = []
    for element in os.listdir(res):
        if os.path.isdir(res + '/' + element):
            list_metadata = list_metadata + dirs(res + '/' + element)
        elif os.path.isfile(res + '/' + element):
            list_metadata.append(files(f"{res}/{element}"))
    return list_metadata

def array_of_segments(file_size, path, segment_name, chunk_size):
	# INICIALIZA POSICIÓN EN 0
	position = 0
	# DEFINE EL TAMAÑO DEL SEGMENTO
	chunk = chunk_size
    # OBTIENE EL NOMBRE Y EXTENSIÓN DEL ARCHIVO
	filename, extension = os.path.splitext(os.path.basename(path))
	# DEFINE ARREGLO DE POSICIONES
	positions = []
	while position < file_size:
		# DEFINE POSICIÓN FINAL DE UN CHUNK
		end_position = position + chunk if ((position + chunk) < file_size) else position + (file_size - position)
		# AGREGA ELEMENTO AL ARREGLO DE POSICIONES
		positions.append({"origin": path, "filename": filename, "extension": extension,"start_position": position, "end_position": end_position, "file_size": file_size, "segment": segment_name, "chunk_size": chunk})
		# ACTUALIZA LA POSICIÓN
		position = position + chunk
	# RETORNA LAS POSICIONES
	return positions

def array_of_segments_for_server_file(file_size, segment_name, chunk_size):
	# INICIALIZA POSICIÓN EN 0
	position = 0
	# DEFINE EL TAMAÑO DEL SEGMENTO
	chunk = chunk_size
    # OBTIENE EL NOMBRE Y EXTENSIÓN DEL ARCHIVO
	# filename, extension = os.path.splitext(os.path.basename(path))
	# DEFINE ARREGLO DE POSICIONES
	positions = []
	while position < file_size:
		# DEFINE POSICIÓN FINAL DE UN CHUNK
		end_position = position + chunk if ((position + chunk) < file_size) else position + (file_size - position)
		# AGREGA ELEMENTO AL ARREGLO DE POSICIONES
		positions.append({"start_position": position, "end_position": end_position, "file_size": file_size, "segment": segment_name, "chunk_size": chunk})
		# ACTUALIZA LA POSICIÓN
		position = position + chunk
	# RETORNA LAS POSICIONES
	return positions