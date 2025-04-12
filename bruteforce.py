import py7zr
from pathlib import Path
from threading import Thread, Event
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
output_file = os.path.join(script_dir, "found_password.txt")

#zipFile_name = "secret.7z"
wordlist_path = input("wordlist path: ")
output_dir = input("output dir: ")
zipFile_path = input("zipfile path: ")
#zipFile_path = os.path.join(script_dir, zipFile_name)
#os.makedirs(output_dir, exist_ok=True)

def open_wordlist(wordlist_path):
    with open(wordlist_path, "r", encoding="utf-8", errors="ignore") as f:
        return [line.strip() for line in f]

def move_cursor(line, col=0):
    print(f"\033[{line};{col}H", end="")
    
def clear_screen():
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")
        
def progress(itteratie, totaal):
    percentage = (itteratie / totaal) * 100
    bar_length = 40
    block = int(round(bar_length * percentage / 100))
    progress_bar = "█" * block + "-" * (bar_length - block)
    print(f"\r[{progress_bar}] {percentage:.2f}%", end="")

def try_passwords(archive, wordlist):
    for i, password in enumerate(wordlist):
        progress(i, len(wordlist))
        try:
            with py7zr.SevenZipFile(archive, mode='r', password=password) as archive_file:
                password_found(password)
            return password
        except py7zr.exceptions.Bad7zFile as e:
            continue
        except py7zr.exceptions.PasswordRequired:
            continue
        except Exception as e:
            print(f"unexpected error: {e}")
    print("\n No password found.")
    return None

def password_found(password):
    found_event.set()
    print(f"\n password =  {password}")
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_file = os.path.join(script_dir, "found_password.txt")
        with open(output_file, "w") as f:
            f.write(f"{password}\n")
            print("wachtwoord opgeslagen")
    except Exception as e:
        print(f" error saving password in txt file: {e}")

def try_passwords_multithreaded(zipfile, wordlist, thread_id):
    i = 0
    for password in wordlist:
        if not found_event.is_set():
            i += 1
            if i < 10:
                move_cursor(5 + thread_id, 0)
                print(f"\rThread {thread_id}: {i}", end="", flush=True)
            if i % 500 == 0:
                # print has a lot of overhead, especially when threaded, so we only print every 500th password
                percent = (i / len(wordlist)) * 100
                move_cursor(5 + thread_id, 0)
                print(f"\rThread {thread_id}: {percent:.3f}%", end="", flush=True)
            try:
                with py7zr.SevenZipFile(zipfile, mode='r', password=password) as archive_file:
                    password_found(password)
                    archive_file.extractall(path=output_dir)
                    return
            except (py7zr.exceptions.Bad7zFile, py7zr.exceptions.PasswordRequired):
                # the header is encrypted so it will give Bad7zFile as error
                # so the program should still continue...
                continue
            except Exception as e:
                print(f"Onverwachte fout: {e}")
                return
# Voer uit
def main():
    if not Path(zipFile_path).exists():
        print(f"Bestand niet gevonden: {zipFile_path}")
    elif not Path(wordlist_path).exists():
        print(f"Woordlijst niet gevonden: {wordlist_path}")
    else:
        wordlist = open_wordlist(wordlist_path)

        num_threads = os.cpu_count()
        change = input("current number of threads: " + str(num_threads) + "\nPress Enter to continue... or give new value \n")
        if change != "":
            try:
                num_threads = int(change)
            except ValueError:
                print("Ongeldige invoer, gebruik standaard aantal threads.")
        chunk_size = len(wordlist) // num_threads
        threads = []
        print(f" # of threads: {num_threads}, wordlist size: {len(wordlist)}, chunk size: {chunk_size} \n")
        input("press enter to continue...")
        clear_screen()
        for i in range(num_threads):
            # made sure that the last thread gets the remaining passwords
            # even if it is not divisible by num_threads
            start_index = i * chunk_size
            end_index = (i + 1) * chunk_size if i != num_threads - 1 else len(wordlist)
            thread_wordlist = wordlist[start_index:end_index]
            thread = Thread(target=try_passwords_multithreaded, args=(zipFile_path, thread_wordlist, i + 1))
            threads.append(thread)
            thread.start()

        for t in threads:
            t.join()

if __name__ == "__main__":
    found_event = Event()
    clear_screen
    try:
        main()
    except KeyboardInterrupt:
        print("exiting...")
