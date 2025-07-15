import argparse
import os
import string
import itertools
import math
from multiprocessing import Process, Manager

def index_to_password(idx, charset, length):
    # Convert integer idx to a password string in the given charset
    base = len(charset)
    chars = []
    for _ in range(length):
        chars.append(charset[idx % base])
        idx //= base
    return ''.join(reversed(chars))

def password_range_generator(start, end, charset, length):
    # Generate all passwords from start to end-1
    for idx in range(start, end):
        yield index_to_password(idx, charset, length)

def worker_list_mode(sublist, args, found_flag):
    from .auto_brute import brute_force
    if not found_flag.value:
        result = brute_force(
            url=args.url,
            username=args.username,
            password_list=sublist,
            delay=args.delay,
            success_url=args.success_url,
            verbose=True
        )
        if result:
            found_flag.value = True

def worker_gen_mode(start, end, charset, pw_length, args, found_flag):
    from .auto_brute import brute_force
    pw_gen = password_range_generator(start, end, charset, pw_length)
    if not found_flag.value:
        result = brute_force(
            url=args.url,
            username=args.username,
            password_list=pw_gen,
            delay=args.delay,
            success_url=args.success_url,
            verbose=True
        )
        if result:
            found_flag.value = True

def main():
    parser = argparse.ArgumentParser(description="Auto password brute force for web login forms.")
    parser.add_argument('url', help='Login page URL')
    parser.add_argument('--username', help='Username to try (optional)', default=None)
    parser.add_argument('--passwords', help='Password list file (optional)')
    parser.add_argument('--delay', type=int, default=2, help='Delay between attempts (seconds)')
    parser.add_argument('--success_url', help='URL after successful login (optional)')
    parser.add_argument('--workers', type=int, default=1, help='Number of parallel browser windows (default: 1)')
    parser.add_argument('--max-length', type=int, default=4, help='Max password length for auto generation (default: 4, max: 20)')
    args = parser.parse_args()

    password_list = None
    charset = string.ascii_letters + string.digits + string.punctuation
    max_pw_length = min(args.max_length, 20)

    if args.passwords:
        with open(args.passwords, encoding='utf-8') as f:
            password_list = [line.strip() for line in f if line.strip()]
        is_generator = False
    else:
        # Check if default_passwords/password.txt exists
        pwd_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'default_passwords', 'password.txt')
        if os.path.exists(pwd_path):
            with open(pwd_path, encoding='utf-8') as f:
                password_list = [line.strip() for line in f if line.strip()]
            is_generator = False
        else:
            # Dynamically generate passwords up to pw_length
            is_generator = True

    if not is_generator:
        # list mode
        if args.workers == 1:
            from .auto_brute import brute_force
            brute_force(
                url=args.url,
                username=args.username,
                password_list=password_list,
                delay=args.delay,
                success_url=args.success_url,
                verbose=True
            )
        else:
            chunk_size = math.ceil(len(password_list) / args.workers)
            processes = []
            with Manager() as manager:
                found_flag = manager.Value('b', False)
                for i in range(args.workers):
                    sublist = password_list[i*chunk_size:(i+1)*chunk_size]
                    p = Process(target=worker_list_mode, args=(sublist, args, found_flag))
                    p.start()
                    processes.append(p)
                for p in processes:
                    p.join()
    else:
        # Auto-generate passwords, try from max_pw_length down to 1
        with Manager() as manager:
            found_flag = manager.Value('b', False)
            for pw_length in range(max_pw_length, 0, -1):
                if found_flag.value:
                    break
                print(f"[INFO] Trying all passwords of length {pw_length}...")
                total = len(charset) ** pw_length
                chunk_size = total // args.workers
                processes = []
                for i in range(args.workers):
                    start = i * chunk_size
                    end = (i+1) * chunk_size if i < args.workers - 1 else total
                    p = Process(target=worker_gen_mode, args=(start, end, charset, pw_length, args, found_flag))
                    p.start()
                    processes.append(p)
                for p in processes:
                    p.join()
                if found_flag.value:
                    print(f"[INFO] Password found at length {pw_length}, stopping further attempts.")
                    break
            else:
                print("[INFO] All lengths tried, no password found.")

if __name__ == '__main__':
    main()
