import os
import struct
from FURGfs2 import FURGfs2

TEST_FILE = "test_furgfs2.fs"
TEST_SOURCE_FILE = "source_file.txt"
TEST_DESTINATION_FILE = "destination_file.txt"


def create_test_environment():
    """Cria os arquivos necessários para os testes."""
    # Criar o sistema de arquivos FURGfs2
    fs_size = 16 * 1024 * 1024  # 16 MB
    fs = FURGfs2(size=fs_size)
    fs.create(TEST_FILE)
    print(f"Sistema de arquivos criado: {TEST_FILE}")

    # Criar o arquivo de origem
    content = b"This is a test file for FURGfs2."
    with open(TEST_SOURCE_FILE, "wb") as src:
        src.write(content)
    print(f"Arquivo de origem criado: {TEST_SOURCE_FILE}")

    # Certifique-se de que o arquivo de destino não existe antes do teste
    if os.path.exists(TEST_DESTINATION_FILE):
        os.remove(TEST_DESTINATION_FILE)


def test_create_fs():
    """Teste: Verifica se o sistema de arquivos foi criado."""
    assert os.path.exists(TEST_FILE)
    print("Teste de criação do sistema de arquivos: OK")


def test_copy_to_furgfs2():
    """Teste: Copia um arquivo para o sistema de arquivos."""
    fs = FURGfs2(size=16 * 1024 * 1024)
    fs.file_path = TEST_FILE
    fs.copy_to_furgfs2(TEST_SOURCE_FILE, "test_file.txt")
    files = list_files(fs)
    assert "test_file.txt" in files
    print("Teste de cópia para o sistema de arquivos: OK")


def test_list_files():
    """Teste: Lista os arquivos no sistema de arquivos."""
    fs = FURGfs2(size=16 * 1024 * 1024)
    fs.file_path = TEST_FILE
    fs.list_files()
    print("Teste de listagem de arquivos: OK")


def test_copy_from_furgfs2():
    """Teste: Copia um arquivo do sistema de arquivos para o sistema real."""
    fs = FURGfs2(size=16 * 1024 * 1024)
    fs.file_path = TEST_FILE
    fs.copy_from_furgfs2("test_file.txt", TEST_DESTINATION_FILE)
    assert os.path.exists(TEST_DESTINATION_FILE)
    print("Teste de cópia do sistema de arquivos para o sistema real: OK")


def test_rename_file():
    """Teste: Renomeia um arquivo no sistema de arquivos."""
    fs = FURGfs2(size=16 * 1024 * 1024)
    fs.file_path = TEST_FILE
    fs.rename_file("test_file.txt", "renamed_file.txt")
    files = list_files(fs)
    assert "renamed_file.txt" in files
    assert "test_file.txt" not in files
    print("Teste de renomeação de arquivo: OK")


def test_protect_file():
    """Teste: Protege um arquivo contra exclusão."""
    fs = FURGfs2(size=16 * 1024 * 1024)
    fs.file_path = TEST_FILE
    fs.protect_file("renamed_file.txt", protect=True)
    fs.list_files()
    try:
        fs.delete_file("renamed_file.txt")
        assert False, "Arquivo protegido foi deletado"
    except ValueError as e:
        assert "protegido contra remoção" in str(e)
    print("Teste de proteção de arquivo: OK")


def test_unprotect_file():
    """Teste: Remove a proteção de um arquivo e o exclui."""
    fs = FURGfs2(size=16 * 1024 * 1024)
    fs.file_path = TEST_FILE
    fs.protect_file("renamed_file.txt", protect=False)
    fs.delete_file("renamed_file.txt")
    files = list_files(fs)
    assert "renamed_file.txt" not in files
    print("Teste de remoção de proteção e exclusão de arquivo: OK")


def list_files(fs):
    """Lista os arquivos no sistema de arquivos e retorna uma lista de nomes."""
    import io
    from contextlib import redirect_stdout

    f = io.StringIO()
    with redirect_stdout(f):
        fs.list_files()
    output = f.getvalue()
    return [line.split(" - ")[0].strip() for line in output.splitlines() if line.strip()]


def run_tests():
    """Executa todos os testes em sequência."""
    create_test_environment()
    test_create_fs()
    test_copy_to_furgfs2()
    test_list_files()
    test_copy_from_furgfs2()
    test_rename_file()
    test_protect_file()
    test_unprotect_file()
    print("Todos os testes foram executados com sucesso.")


if __name__ == "__main__":
    run_tests()
