Bruteforce 2 is a bit more efficient because it uses subprocess.Popen to interact with the CLI. 
By doing this I can add the test flag and 7z doesn't try to decrypt the file, he justs checks if the password is allright.
