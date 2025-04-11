# nuvem/main_exe.py (Console Launcher Version) -  Compiled entrypoint
"This is a console launcher version of nuvem.py, made to be run from an .exe file by pyinstaller."


import time
import os
import sys
import traceback
import subprocess
import runpy
import socket
import threading

# --- Platform Specific Imports for Termination ---
if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

# --- Configuration ---
STREAMLIT_PORT = 8501
STARTUP_WAIT_TIMEOUT = 20  # Max seconds to wait for Streamlit port
PORT_CHECK_INTERVAL = 0.5
PORT_CHECK_TIMEOUT = 1.0
INTERNAL_FLAG = "--internal-streamlit-run"  # Flag to identify subprocess


# --- Helper Function to find nuvem.py ---
def encontrar_nuvem_py(base_path, is_frozen):
    """Finds nuvem.py within the bundle/source"""
    print(f"--- Buscando nuvem.py ---")
    print(f"Base path para busca: {base_path}")
    print(f"Esta congelado (frozen)? {is_frozen}")
    caminho_relativo_primario = os.path.join("nuvem", "pages", "nuvem.py")
    caminho_abs_primario = os.path.join(base_path, caminho_relativo_primario)
    print(f"[Info] Tentando caminho primario: {caminho_abs_primario}")
    if os.path.exists(caminho_abs_primario):
        print(f"[Ok] Encontrado (Primario): {caminho_abs_primario}")
        return caminho_abs_primario
    print(f"[Error] Arquivo 'nuvem.py' nao encontrado.")
    if is_frozen:
        print(f"Conteudo de _MEIPASS ({base_path}):")
        try:
            [print(f"  - {item}") for item in os.listdir(base_path)]
        except Exception as list_e:
            print(f"    Erro ao listar: {list_e}")
    return None


# --- Function to Start Streamlit Process ---
streamlit_process = None  # Global variable to hold the process object


def start_streamlit_subprocess(app_path_for_streamlit):
    """Launches the Streamlit server as a subprocess using the main exe itself."""
    global streamlit_process
    python_executable = sys.executable
    print(f"\n--- Iniciando SUBPROCESSO Streamlit ---")
    print(f"[Info] Usando Executavel: {python_executable}")
    command = [
        python_executable,
        INTERNAL_FLAG,
        app_path_for_streamlit,
        str(STREAMLIT_PORT),
    ]
    print(f"[Info] Comando Subprocesso: {' '.join(command)}")
    try:
        creationflags = 0
        startupinfo = None
        stdout_pipe = subprocess.PIPE  # Capture output even if not monitored constantly
        stderr_pipe = subprocess.PIPE
        if sys.platform == "win32":
            # Still hide the subprocess window if possible
            creationflags = subprocess.CREATE_NO_WINDOW
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        print("[Info] Lancando processo (que vai rodar Streamlit)...")
        # Assign to the global variable
        streamlit_process = subprocess.Popen(
            command,
            stdout=stdout_pipe,
            stderr=stderr_pipe,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=creationflags,
            startupinfo=startupinfo,
        )
        print(f"[Ok] Processo iniciado (PID: {streamlit_process.pid}).")

        # Output monitoring if needed for debugging startup
        def minimal_monitor(pipe, pipe_name):
            try:
                # Read only a few lines or for a short time
                for _ in range(10):  # Limit lines read
                    line = pipe.readline()
                    if not line:
                        break
                    safe_line = (
                        line.strip()
                        .encode(sys.stdout.encoding, errors="replace")
                        .decode(sys.stdout.encoding)
                    )
                    print(f"   [Init Subprocess {pipe_name}]: {safe_line}")
            except Exception:
                pass  # Ignore errors here
            finally:
                if pipe:
                    pass  # Don't close pipe here, let main process handle process object
                threading.Thread(
                    target=minimal_monitor,
                    args=(streamlit_process.stdout, "stdout"),
                    daemon=True,
                ).start()
                threading.Thread(
                    target=minimal_monitor,
                    args=(streamlit_process.stderr, "stderr"),
                    daemon=True,
                ).start()

    except Exception as e:
        print(f"\n[Error] ERRO inesperado ao iniciar o SUBPROCESSO Streamlit:")
        traceback.print_exc()
        raise


# --- Function to check if Streamlit port is open ---
def is_port_open(host, port, timeout=PORT_CHECK_TIMEOUT):
    # (Keep As Is)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        return sock.connect_ex((host, port)) == 0
    except Exception:
        return False
    finally:
        sock.close()


# --- Windows Job Object Handling ---
job_handle = None


def setup_job_object():
    global job_handle
    if sys.platform != "win32":
        print("[Info] Nao e Windows, pulando configuracao de Job Object.")
        return

    print("[Info] Configurando Job Object (Windows) para terminacao de subprocesso...")
    # Define constants and structures
    SYNCHRONIZE = 0x00100000
    JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
    JobObjectExtendedLimitInformation = 9
    INVALID_HANDLE_VALUE = -1

    class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", wintypes.LARGE_INTEGER),
            ("PerJobUserTimeLimit", wintypes.LARGE_INTEGER),
            ("LimitFlags", wintypes.DWORD),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", wintypes.DWORD),
            ("Affinity", ctypes.POINTER(wintypes.ULONG)),
            ("PriorityClass", wintypes.DWORD),
            ("SchedulingClass", wintypes.DWORD),
        ]

    class IO_COUNTERS(ctypes.Structure):
        _fields_ = [
            ("ReadOperationCount", ctypes.c_ulonglong),
            ("WriteOperationCount", ctypes.c_ulonglong),
            ("OtherOperationCount", ctypes.c_ulonglong),
            ("ReadTransferCount", ctypes.c_ulonglong),
            ("WriteTransferCount", ctypes.c_ulonglong),
            ("OtherTransferCount", ctypes.c_ulonglong),
        ]

    class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
            ("IoInfo", IO_COUNTERS),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    kernel32 = ctypes.windll.kernel32

    # Create Job Object
    job_handle = kernel32.CreateJobObjectW(None, None)
    if not job_handle:
        print(f"[Error] Falha ao criar Job Object: {ctypes.get_last_error()}")
        return

    # Get current limits
    extended_info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
    res = kernel32.QueryInformationJobObject(
        job_handle,
        JobObjectExtendedLimitInformation,
        ctypes.byref(extended_info),
        ctypes.sizeof(extended_info),
        None,
    )
    if not res:
        print(f"[Error] Falha ao consultar Job Object: {ctypes.get_last_error()}")
        kernel32.CloseHandle(job_handle)
        job_handle = None
        return

    # Set the kill-on-close flag
    extended_info.BasicLimitInformation.LimitFlags |= JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE

    # Set the modified limits
    res = kernel32.SetInformationJobObject(
        job_handle,
        JobObjectExtendedLimitInformation,
        ctypes.byref(extended_info),
        ctypes.sizeof(extended_info),
    )
    if not res:
        print(f"[Error] Falha ao definir Job Object: {ctypes.get_last_error()}")
        kernel32.CloseHandle(job_handle)
        job_handle = None
        return

    # Assign the *current* process to the Job Object
    current_process_handle = kernel32.GetCurrentProcess()
    res = kernel32.AssignProcessToJobObject(job_handle, current_process_handle)
    if not res:
        print(
            f"[Error] Falha ao atribuir processo ao Job Object: {ctypes.get_last_error()}"
        )
        kernel32.CloseHandle(job_handle)
        job_handle = None
        return

    print("[Ok] Processo atual atribuido ao Job Object com Kill On Close.")


# --- Main Execution Logic ---
if __name__ == "__main__":
    # --- MODE CHECK ---
    if INTERNAL_FLAG in sys.argv:
        # --- INTERNAL STREAMLIT RUN MODE (using runpy) ---
        print("[Internal Mode] Detectado. Iniciando Streamlit Server via runpy.")
        try:
            script_path_index = sys.argv.index(INTERNAL_FLAG) + 1
            port_index = sys.argv.index(INTERNAL_FLAG) + 2
            script_path = sys.argv[script_path_index]
            port = sys.argv[port_index]
            streamlit_cli_args = [
                "streamlit",  # sys.argv[0] for the module
                "run",
                script_path,
                "--server.headless",
                "true",
                "--server.port",
                port,
                "--server.runOnSave",
                "false",
                "--server.fileWatcherType",
                "none",
                "--global.developmentMode=false",
            ]
            print(
                f"[Internal Mode] Argumentos para sys.argv (para runpy): {streamlit_cli_args}"
            )
            sys.argv = streamlit_cli_args
            runpy.run_module("streamlit", run_name="__main__", alter_sys=True)
            print("[Internal Mode] runpy executou o modulo streamlit.")
            sys.exit(0)
        except ModuleNotFoundError:
            print(
                "[Internal Mode][CRITICAL] Erro: Modulo 'streamlit' nao encontrado via runpy."
            )
            traceback.print_exc()
            sys.exit(1)
        except Exception as e:
            print(f"[Internal Mode][CRITICAL] Erro ao executar Streamlit via runpy:")
            traceback.print_exc()
            sys.exit(1)
        # --- END INTERNAL STREAMLIT RUN MODE ---
    else:
        # --- NORMAL CONSOLE LAUNCH MODE ---
        try:
            print("--- Iniciando Lancador Principal (Modo Console) ---")

            # --- Setup Job Object for Process Cleanup (Windows Only) ---
            setup_job_object()

            # --- Find bundled script ---
            if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
                base_path = sys._MEIPASS
                is_frozen = True
                print(f"[Info] Executando empacotado (frozen). Base path: {base_path}")
            else:
                is_frozen = False
                base_path = os.path.dirname(os.path.abspath(__file__))
                print(
                    f"[Info] Executando em modo de desenvolvimento. Base path: {base_path}"
                )

            app_path = encontrar_nuvem_py(base_path, is_frozen)
            if not app_path:
                print("\n[CRITICAL] ERRO: Nao foi possivel localizar 'nuvem.py'.")
                input("   Pressione Enter para sair.")
                sys.exit(1)
            print(f"\n[Info] Script Streamlit localizado: {app_path}")

            # --- Start Streamlit Subprocess ---
            start_streamlit_subprocess(app_path)

            # --- Wait for Port ---
            print(
                f"\n[Wait] Aguardando ate {STARTUP_WAIT_TIMEOUT}s para Streamlit ({STREAMLIT_PORT}) ficar disponivel..."
            )
            start_time = time.time()
            port_ready = False
            while time.time() - start_time < STARTUP_WAIT_TIMEOUT:
                if is_port_open("127.0.0.1", STREAMLIT_PORT):
                    print(f"\n[Ok] Porta {STREAMLIT_PORT} esta aberta!")
                    port_ready = True
                    break
                else:
                    print(f".", end="", flush=True)
                    time.sleep(PORT_CHECK_INTERVAL)

            if not port_ready:
                print(f"\n[Warn] Porta {STREAMLIT_PORT} nao ficou disponivel.")
                print("   Verifique os logs iniciais do [Subprocess stdout/stderr].")
                # Attempt to terminate the potentially failed process
                if streamlit_process and streamlit_process.poll() is None:
                    print("[Info] Tentando encerrar processo Streamlit...")
                    streamlit_process.terminate()
                    try:
                        streamlit_process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        streamlit_process.kill()
                input("   Pressione Enter para sair.")
                sys.exit(1)

            # --- Server Ready - Print URL and Wait ---
            streamlit_url = f"http://localhost:{STREAMLIT_PORT}"
            print("\n" + "=" * 50)
            print(f" Servidor Streamlit iniciado com sucesso!")
            print(f" Abra o seguinte URL no seu navegador:")
            print(f"  >> {streamlit_url} <<")
            print("=" * 50)
            print("\nEste console permanecera aberto.")
            print("FECHE esta janela (ou pressione Ctrl+C) para encerrar o servidor.")

            # Keep the main process alive. The Job Object handles cleanup on close.
            # Option 1: Wait indefinitely
            while True:
                time.sleep(1)
            # Option 2: Wait for user input (cleaner exit if user presses Enter)
            # try:
            #     input("\nPressione Enter para encerrar o servidor...")
            # except EOFError: # Handles Ctrl+Z or pipe closing
            #     pass
            # finally:
            #     if streamlit_process and streamlit_process.poll() is None:
            #         print("\n[Info] Encerrando processo Streamlit...")
            #         streamlit_process.terminate()
            #         try: streamlit_process.wait(timeout=3)
            #         except subprocess.TimeoutExpired: streamlit_process.kill()
            #     if job_handle: # Clean up job object handle (optional)
            #         ctypes.windll.kernel32.CloseHandle(job_handle)
            #     print("[Info] Programa encerrado.")

        except KeyboardInterrupt:
            print("\n[Info] Ctrl+C detectado. Encerrando...")
            # Cleanup logic similar to finally block above could go here
        except Exception as e:
            print("\n[CRITICAL] Erro fatal durante a execucao (Modo Console):")
            traceback.print_exc()
            input("\n   Pressione Enter para sair.")
            sys.exit(1)
        finally:
            # --- Cleanup Logic (Executed on normal exit or error after try block) ---
            if streamlit_process and streamlit_process.poll() is None:
                print("\n[Info] Encerrando processo Streamlit (final cleanup)...")
                streamlit_process.terminate()
                try:
                    streamlit_process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    streamlit_process.kill()
            if job_handle:  # Clean up job object handle
                print("[Info] Fechando handle do Job Object...")
                ctypes.windll.kernel32.CloseHandle(job_handle)
            print("[Info] Programa finalizado.")

        # --- END NORMAL CONSOLE LAUNCH MODE ---
