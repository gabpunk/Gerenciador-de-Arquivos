import os
import struct

class FURGfs2:
    def __init__(self, size):
        self.size = size
        self.block_size = 4096
        self.header_size = 1024
        self.fat_size = (size // self.block_size) * 4
        self.directory_size = 1000 * 264  # Até 1000 arquivos
        self.data_offset = self.header_size + self.fat_size + self.directory_size
        self.file_path = None

    def create(self, file_path):
        """Cria o sistema de arquivos FURGfs2"""
        self.file_path = file_path
        with open(file_path, "wb") as f:
            # Cabeçalho
            header = struct.pack(
                "I I I I",  # Tamanho do sistema, bloco, FAT, dados
                self.size,
                self.block_size,
                self.header_size,
                self.data_offset
            )
            f.write(header.ljust(self.header_size, b'\x00'))

            # FAT
            f.write(b'\x00' * self.fat_size)

            # Diretório
            f.write(b'\x00' * self.directory_size)

            # Dados
            f.write(b'\x00' * (self.size - self.data_offset))

        print(f"FURGfs2 criado com sucesso: {file_path} ({self.size} bytes)")

    def copy_to_furgfs2(self, source_path, dest_name):
        """Copia um arquivo do sistema real para o FURGfs2"""
        if not self.file_path:
            raise ValueError("Sistema de arquivos não inicializado.")

        if len(dest_name) > 255:
            raise ValueError("O nome do arquivo é muito longo.")

        # Lê o arquivo a ser copiado
        with open(source_path, "rb") as src:
            data = src.read()
        file_size = len(data)

        # Verifica espaço disponível
        free_space = self.get_free_space()
        if file_size > free_space:
            raise ValueError("Espaço insuficiente no FURGfs2.")

        with open(self.file_path, "r+b") as fs:
            # Localiza blocos livres na FAT
            fat = self.read_fat(fs)
            required_blocks = (file_size + self.block_size - 1) // self.block_size
            blocks = [i for i, b in enumerate(fat) if b == 0][:required_blocks]

            if len(blocks) < required_blocks:
                raise ValueError("Espaço insuficiente para alocar os blocos necessários.")

            # Atualiza FAT
            for i in range(len(blocks)):
                if i == len(blocks) - 1:
                    fat[blocks[i]] = -1  # Último bloco
                else:
                    fat[blocks[i]] = blocks[i + 1]
            self.write_fat(fs, fat)

            # Escreve dados nos blocos
            for i, block in enumerate(blocks):
                fs.seek(self.data_offset + block * self.block_size)
                fs.write(data[i * self.block_size:(i + 1) * self.block_size])

            # Atualiza diretório
            self.add_to_directory(fs, dest_name, file_size, blocks[0])

        print(f"Arquivo '{source_path}' copiado para '{dest_name}' no FURGfs2.")

    def copy_from_furgfs2(self, source, destination):
        """Copia um arquivo do FURGfs2 para o sistema real."""
        with open(self.file_path, "rb") as fs:
            fs.seek(self.header_size + self.fat_size)  # Pular até a tabela do diretório
            for _ in range(1000):  # Procurar no diretório até 1000 entradas
                entry = fs.read(264)
                if len(entry) < 264:
                    raise ValueError("Dados do diretório estão incompletos.")
                name, size, start_block, flags = struct.unpack("256sIIB", entry)
                name = name.decode().strip("\x00")
                if name == source:
                    fat = self.read_fat(fs)
                    with open(destination, "wb") as dest:
                        current_block = start_block
                        while current_block != -1:
                            fs.seek(self.data_offset + current_block * self.block_size)
                            data = fs.read(self.block_size)
                            dest.write(data)
                            current_block = fat[current_block]
                    print(f"Arquivo '{source}' copiado para '{destination}'.")
                    return
        raise ValueError(f"Arquivo '{source}' não encontrado no FURGfs2.")

        
    def rename_file(self, old_name, new_name):
        """Renomeia um arquivo no FURGfs2"""
        if len(new_name) > 255:
            raise ValueError("O novo nome do arquivo é muito longo.")

        with open(self.file_path, "r+b") as fs:
            fs.seek(self.header_size + self.fat_size)
            for _ in range(1000):
                entry_pos = fs.tell()
                entry = fs.read(264)
                name, size, start_block, flags = struct.unpack("256sIIB", entry)
                name = name.decode().strip("\x00")
                if name == old_name:
                    new_entry = struct.pack(
                        "256sIIB",
                        new_name.encode().ljust(256, b'\x00'),
                        size,
                        start_block,
                        flags
                    )
                    fs.seek(entry_pos)
                    fs.write(new_entry)
                    print(f"Arquivo '{old_name}' renomeado para '{new_name}'.")
                    return
            raise ValueError(f"Arquivo '{old_name}' não encontrado.")

    def delete_file(self, name):
        """Remove um arquivo do FURGfs2"""
        with open(self.file_path, "r+b") as fs:
            fs.seek(self.header_size + self.fat_size)
            for _ in range(1000):
                entry_pos = fs.tell()
                entry = fs.read(264)
                file_name, size, start_block, flags = struct.unpack("256sIIB", entry)
                file_name = file_name.decode().strip("\x00")
                if file_name == name:
                    if flags & 0x01:
                        raise ValueError("Arquivo está protegido contra remoção.")
                    fat = self.read_fat(fs)
                    current_block = start_block
                    while current_block != -1:
                        next_block = fat[current_block]
                        fat[current_block] = 0
                        current_block = next_block
                    self.write_fat(fs, fat)
                    fs.seek(entry_pos)
                    fs.write(b'\x00' * 264)
                    print(f"Arquivo '{name}' removido do FURGfs2.")
                    return
            raise ValueError(f"Arquivo '{name}' não encontrado.")
        
    def list_files(self):
        """Lista todos os arquivos no FURGfs2"""
        if not self.file_path:
            raise ValueError("Sistema de arquivos não inicializado.")

        print("Arquivos no FURGfs2:")
        with open(self.file_path, "rb") as fs:
            fs.seek(self.header_size + self.fat_size)
            for _ in range(1000):
                entry = fs.read(264)
                if entry[0] != 0:
                    name, size, start_block, flags = struct.unpack("256sIIB", entry)
                    name = name.decode().strip("\x00")
                    print(f"{name} - {size} bytes - Bloco inicial: {start_block} - Protegido: {bool(flags)}")

    def get_free_space(self):
        """Calcula o espaço livre no FURGfs2"""
        with open(self.file_path, "rb") as fs:
            fat = self.read_fat(fs)
            free_blocks = fat.count(0)
        return free_blocks * self.block_size
    
    def protect_file(self, name, protect=True):
        """Protege ou desprotege um arquivo no FURGfs2"""
        with open(self.file_path, "r+b") as fs:
            fs.seek(self.header_size + self.fat_size)
            for _ in range(1000):
                entry_pos = fs.tell()
                entry = fs.read(264)
                file_name, size, start_block, flags = struct.unpack("256sIIB", entry)
                file_name = file_name.decode().strip("\x00")
                if file_name == name:
                    if protect:
                        flags |= 0x01  # Define o bit de proteção
                    else:
                        flags &= ~0x01  # Remove o bit de proteção
                    new_entry = struct.pack(
                        "256sIIB",
                        file_name.encode().ljust(256, b'\x00'),
                        size,
                        start_block,
                        flags
                    )
                    fs.seek(entry_pos)
                    fs.write(new_entry)
                    print(f"Arquivo '{name}' {'protegido' if protect else 'desprotegido'} com sucesso.")
                    return
            raise ValueError(f"Arquivo '{name}' não encontrado.")

    def read_fat(self, fs):
        """Lê a FAT do FURGfs2"""
        fs.seek(self.header_size)
        fat_entries = self.fat_size // 4  # Número de entradas no FAT
        return list(struct.unpack(f"{fat_entries}I", fs.read(self.fat_size)))


    def write_fat(self, fs, fat):
        """Escreve a FAT no FURGfs2"""
        # Validar os números da FAT
        for i, value in enumerate(fat):
            if value < 0 or value > 4294967295:
                raise ValueError(f"Valor inválido na FAT na posição {i}: {value}")
        
        # Escrevendo dados da FAT no formato correto
        fs.seek(self.header_size)  # Ajuste para posição correta
        packed_fat = struct.pack(f"{len(fat)}I", *fat)  # Empacota todos os valores como unsigned int
        fs.write(packed_fat)

    def add_to_directory(self, fs, name, size, start_block):
        """Adiciona um arquivo ao diretório"""
        fs.seek(self.header_size + self.fat_size)
        for _ in range(1000):
            entry = fs.read(264)
            if entry[0] == 0:  # Entrada vazia
                fs.seek(-264, 1)
                entry_data = struct.pack(
                    f"256sIIB",
                    name.encode().ljust(256, b'\x00'),
                    size,
                    start_block,
                    0  # Flags
                )
                fs.write(entry_data)
                return
        raise ValueError("Diretório cheio.")
