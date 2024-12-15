import os
import struct


def create_test_environment():
    # Criar o sistema de arquivos FURGfs2
    fs_file = "test_furgfs2.fs"
    source_file = "source_file.txt"
    destination_file = "destination_file.txt"

    # Criar o arquivo FURGfs2
    fs_size = 1024 * 1024  # 1 MB
    block_size = 4096
    header_size = 1024
    fat_size = (fs_size // block_size) * 4
    directory_size = 1000 * 264  # Até 1000 arquivos
    data_offset = header_size + fat_size + directory_size

    with open(fs_file, "wb") as fs:
        # Cabeçalho
        header = struct.pack("I I I I", fs_size, block_size, header_size, data_offset)
        fs.write(header.ljust(header_size, b'\x00'))

        # FAT
        fs.write(b'\x00' * fat_size)

        # Diretório
        fs.write(b'\x00' * directory_size)

        # Dados
        fs.write(b'\x00' * (fs_size - data_offset))

    print(f"Sistema de arquivos criado: {fs_file}")

    # Criar o arquivo de origem
    with open(source_file, "w") as src:
        src.write("Olá, teste FURGfs2!")

    print(f"Arquivo de origem criado: {source_file}")

    # Criar o arquivo de destino vazio
    with open(destination_file, "w") as dest:
        dest.write("")

    print(f"Arquivo de destino criado: {destination_file}")


if __name__ == "__main__":
    create_test_environment()
