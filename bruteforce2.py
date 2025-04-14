import os, subprocess
from threading import Thread, Lock, Event
from concurrent.futures import ThreadPoolExecutor, as_completed

found_event = Event()

def get_os():
    return os.name

def clear():
    if os.name == "posix":
        return os.system ("clear")
    elif os.name == "ce" or os.name == "nt" or os.name == "dos":
        return os.system ("cls")
    
def move_cursor(line, col=0):
    print(f'\033[{line};{col}H', end='')

def clear_screen():
    if os.name == "nt":
        os.system("cls")
    else:
        print('\033[2J', end='')  # clear screen
        print('\033[?25l', end='')  # hide cursor

def restore_cursor():
    print('\033[?25h', end='')  # show cursor again

def open_passwords(filename):
    try:
        with open(filename, "r", encoding="utf-8", errors="ignore") as dic:
            return dic.readlines()
    except FileNotFoundError:
        print("Dictionary file not found.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return  None

def file_exists(filepath, label):
    if not os.path.isfile(filepath):
        print(f"{label} file '{filepath}' not found.\n")
        return False
    return True

def zip_and_dic_path():
    files_exist = False
    while not files_exist:
        zip_path = input('path of the zip file')
        dictionary = input('path of the dictionary file')
        dic_exists = file_exists(dictionary, "dictionary")
        zip_exists = file_exists(zip_path, "zip")
        if  zip_exists and dic_exists:
            files_exist = True
        elif not zip_exists:
            print("wrong zip path")
        elif not dic_exists:
            print("wrong dictionary path")
    return zip_path, dictionary

def chunkify(passwords, num_threads):
    chunk_size = len(passwords) // num_threads
    for i in range(num_threads):
        start = i * chunk_size
        end = (i + 1) * chunk_size if i < num_threads - 1 else len(passwords)
        yield passwords[start:end]

def progress(i, chunk_total, thread_id):
    if i % 250 == 0 or i < 72:
                thread_progress = (i / chunk_total) * 100
                move_cursor(2 + thread_id, 0)
                print(f' [Thread-{thread_id:02}] {thread_progress:.3f}% of its chunk{" " * 10}', end='', flush=True)

def attempt_chunk(passwords, sevenzip, progress_count, total, lock, found_event, thread_id):
    chunk_total = len(passwords)
    chunk_count = 0
    for password in passwords:
        password = password.strip()
        if not found_event.is_set():
            try:
                if get_os() == "nt": #windows needs full path to 7z exe
                    proc = subprocess.Popen(
                    [r"C:\Program Files\7-Zip\7z.exe", "t", f"-p{password}", sevenzip],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                elif get_os() == "posix":
                    proc = subprocess.Popen(
                        ["7z", "t", f"-p{password}", sevenzip],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
            except Exception as e:
                print("command error ", e)
   
            chunk_count += 1
            progress(chunk_count, chunk_total, thread_id)
            proc.wait()   
            # https://7zip.bugaco.com/7zip/MANUAL/cmdline/exit_codes.htm
            if proc.returncode == 0:
                clear_screen()
                found_event.set()
                move_cursor(2 + thread_id + 1, 0)
                print(f'\n Password Found!: {password}\n')
                with open("found_password.txt", "w") as f:
                    f.write(f"Password: {password}\n")
                restore_cursor()
                os._exit(0)
            elif proc.returncode == 1:#warning, no fatal eror
                print("warning, no fatal error by {password}")
                break
            elif proc.returncode == 2:#error, fatal error
            # test shows that this is the error for wrong password
                pass
            elif proc.returncode == 7:#error, not supported:
                print("command line error")
                break
            elif proc.returncode == 8:#error, not enough memory
                print("not enough memory")
                break
            elif proc.returncode == 255:#error, user interrupt
                print("user interrupt")
                break
            else:
                raise RuntimeError(f"Unknown error code: {proc.returncode} for password: {password}")

def sevenzip(dictionary, sevenzip_path):   
    passwords = open_passwords(dictionary)
    if not passwords:
        input("\n something went wrong \n Press Enter to return...")
        return
    total = len(passwords)
    print(f'{total} passwords to test')

    progress_count = [0]
    lock = Lock()
    futures = []

    try:
        user_threads = input(f'   Enter number of threads (default: {os.cpu_count()}): ')
        num_threads = int(user_threads) if user_threads.strip() else os.cpu_count()
    except ValueError:
        print(f' Invalid thread number. Using default: {os.cpu_count()}')
        num_threads = os.cpu_count()

    chunks = list(chunkify(passwords, num_threads))
    clear_screen()
    move_cursor(0,0)
    print(f'   Using {num_threads} threads to try {len(passwords)} passwords...\n')

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [
            executor.submit(
                attempt_chunk,
                chunk,
                sevenzip_path,
                progress_count,
                total,
                lock,
                found_event,
                i + 1,
            )
            for i, chunk in enumerate(chunks)
        ]
    for future in as_completed(futures):
        if found_event.is_set():
            break
    restore_cursor()    
    print('Password not found.')

def main():
    print(f"{get_os()} detected")
    sevenzip_path, dictionary = zip_and_dic_path()
    try:
        while True:
            sevenzip(dictionary, sevenzip_path)
    except KeyboardInterrupt:
        print("interupted")
    finally:
        restore_cursor()
        print(f"Goodbye!")
        exit(0)

if __name__ == '__main__':
    clear()
    try:
        main()
    finally:
        restore_cursor()
        exit(0)

