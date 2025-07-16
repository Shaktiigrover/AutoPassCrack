import argparse
import os
import string
import itertools
import math
from multiprocessing import Process, Manager
import json
import time

RESUME_FILE = '.autopasscrack_resume.json'

def save_resume(state):
    with open(RESUME_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f)

def load_resume():
    try:
        with open(RESUME_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None

def clear_resume():
    import os
    if os.path.exists(RESUME_FILE):
        os.remove(RESUME_FILE)

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

# --- Worker functions must be at module level for multiprocessing on Windows ---
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

def worker_username_mode(start, end, charset, un_length, password_list, args, found_flag):
    from .auto_brute import brute_force
    un_gen = username_range_generator(start, end, charset, un_length)
    if not found_flag.value:
        result = brute_force(
            url=args.url,
            username=un_gen,
            password_list=password_list,
            delay=args.delay,
            success_url=args.success_url,
            verbose=True
        )
        if result:
            found_flag.value = True

def worker_both_mode(start, end, charset, un_length, pw_length, args, found_flag):
    from .auto_brute import brute_force
    for idx in range(start, end):
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
        if result:
            found_flag.value = True
            break

def main():
    parser = argparse.ArgumentParser(description="Auto password brute force for web login forms.")
    parser.add_argument('url', help='Login page URL')
    parser.add_argument('--username', help='Username to try (optional)', default=None)
    parser.add_argument('--passwords', help='Password list file (optional) or comma-separated passwords')
    parser.add_argument('--delay', type=int, default=2, help='Delay between attempts (seconds)')
    parser.add_argument('--success_url', help='URL after successful login (optional)')
    parser.add_argument('--workers', type=int, default=1, help='Number of parallel browser windows (default: 1)')
    parser.add_argument('--max-length', type=int, default=4, help='Max password length for auto generation (default: 4, max: 20)')
    parser.add_argument('--charset', help='Custom charset for password/username generation (default: letters+digits+punctuation)', default=None)
    parser.add_argument('--blacklist', help='Blacklist characters for password/username generation', default=None)
    parser.add_argument('--whitelist', help='Whitelist characters for password/username generation', default=None)
    parser.add_argument('--common-passwords', help='File with common passwords to try first', default=None)
    parser.add_argument('--common-usernames', help='File with common usernames to try first', default=None)
    parser.add_argument('--resume', action='store_true', help='Resume from last progress if available')
    parser.add_argument('--username-selector', help='CSS selector for username field (optional)', default=None)
    parser.add_argument('--password-selector', help='CSS selector for password field (optional)', default=None)
    parser.add_argument('--proxy', help='Proxy server (e.g., http://127.0.0.1:8080)', default=None)
    parser.add_argument('--dry-run', action='store_true', help='Only test the first username/password pair for debug')
    parser.add_argument('--logfile', help='Log file to write progress and results', default=None)
    parser.add_argument('--success-message', help='Text message indicating successful login (optional)', default=None)
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
        # Fully auto-generate all username/password combinations
        max_length = min(args.max_length, 20)
        # Determine charset
        if args.charset:
            charset = args.charset
        else:
            charset = string.ascii_letters + string.digits + string.punctuation
        if args.blacklist:
            charset = ''.join([c for c in charset if c not in args.blacklist])
        if args.whitelist:
            charset = ''.join([c for c in charset if c in args.whitelist])
        with Manager() as manager:
            found_flag = manager.Value('b', False)
            resume_state = None
            if args.resume:
                resume_state = load_resume()
                if resume_state:
                    print('[INFO] Resuming from last saved progress (auto mode)...')
            resume_un_length = resume_state.get('un_length') if resume_state else None
            resume_pw_length = resume_state.get('pw_length') if resume_state else None
            resume_idx = resume_state.get('idx') if resume_state else 0
            for un_length in range(max_length, 0, -1):
                for pw_length in range(max_length, 0, -1):
                    if found_flag.value:
                        break
                    if resume_un_length is not None and resume_pw_length is not None:
                        if un_length > resume_un_length or (un_length == resume_un_length and pw_length > resume_pw_length):
                            continue
                    print(f"[INFO] Trying all username/password combinations: username length {un_length}, password length {pw_length}...")
                    total = (len(charset) ** un_length) * (len(charset) ** pw_length)
                    chunk_size = total // args.workers
                    processes = []
                    for i in range(args.workers):
                        start = i * chunk_size
                        end = (i+1) * chunk_size if i < args.workers - 1 else total
                        # Resume only for the first chunk
                        if resume_un_length == un_length and resume_pw_length == pw_length and i == 0 and resume_idx:
                            start = resume_idx
                        p = Process(target=worker_both_mode, args=(start, end, charset, un_length, pw_length, args, found_flag))
                        p.start()
                        processes.append(p)
                    # Save resume state after each chunk
                    if args.resume:
                        save_resume({'un_length': un_length, 'pw_length': pw_length, 'idx': 0})
                    for p in processes:
                        p.join()
                        # If found_flag is set, terminate all other processes
                        if found_flag.value:
                            for proc in processes:
                                if proc.is_alive():
                                    proc.terminate()
                            break
                    if found_flag.value:
                        print(f"[INFO] Username/password found at username length {un_length}, password length {pw_length}, stopping further attempts.")
                        if args.resume:
                            clear_resume()
                        break
            else:
                print("[INFO] All username/password combinations tried, no login succeeded.")
        return

    password_list = None
    # Determine charset
    if args.charset:
        charset = args.charset
    else:
        charset = string.ascii_letters + string.digits + string.punctuation
    if args.blacklist:
        charset = ''.join([c for c in charset if c not in args.blacklist])
    if args.whitelist:
        charset = ''.join([c for c in charset if c in args.whitelist])
    max_pw_length = min(args.max_length, 20)

    if args.passwords:
        # If --passwords is a file and exists, use file as password list
        if os.path.isfile(args.passwords):
            with open(args.passwords, encoding='utf-8') as f:
                password_list = [line.strip() for line in f if line.strip()]
            is_generator = False
        else:
            # If file does not exist, treat as direct password string (support comma separated)
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

    # Prioritize common passwords/usernames if provided
    common_passwords = []
    if args.common_passwords and os.path.isfile(args.common_passwords):
        with open(args.common_passwords, encoding='utf-8') as f:
            common_passwords = [line.strip() for line in f if line.strip()]
    common_usernames = []
    if args.common_usernames and os.path.isfile(args.common_usernames):
        with open(args.common_usernames, encoding='utf-8') as f:
            common_usernames = [line.strip() for line in f if line.strip()]

    # If common_passwords exist, try them first before any other mode
    if common_passwords:
        print('[INFO] Trying common passwords first...')
        from .auto_brute import brute_force
        total = len(common_passwords)
        start_time = time.time()
        for idx, pwd in enumerate(common_passwords):
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
        # If found, should exit (brute_force 會自動 print 成功訊息)
        # User can stop process if needed

    # Progress/resume state
    resume_state = None
    if args.resume:
        resume_state = load_resume()
        if resume_state:
            print('[INFO] Resuming from last saved progress...')

    # For multi-worker resume: filter out already tried passwords
    if args.resume and resume_state and args.workers > 1 and not is_generator:
        tried = set(resume_state.get('tried', []))
        password_list = [pw for pw in password_list if pw not in tried]
        print(f'[INFO] Resuming: {len(password_list)} passwords left to try.')

    def print_progress(current, total, start_time):
        percent = (current / total) * 100 if total else 0
        elapsed = time.time() - start_time
        eta = (elapsed / current) * (total - current) if current else 0
        msg = f'Progress: {current}/{total} ({percent:.2f}%), Elapsed: {elapsed:.1f}s, ETA: {eta:.1f}s'
        print(msg, end='\r')
        if args.logfile:
            with open(args.logfile, 'a', encoding='utf-8') as logf:
                logf.write(msg + '\n')

    if args.dry_run:
        print('[INFO] Dry-run mode: only testing the first username/password pair.')
        from .auto_brute import brute_force
        test_username = args.username if args.username else 'admin'
        test_password = None
        if args.passwords:
            if os.path.isfile(args.passwords):
                with open(args.passwords, encoding='utf-8') as f:
                    pw_list = [line.strip() for line in f if line.strip()]
                test_password = pw_list[0] if pw_list else 'password'
            else:
                pw_list = [pw.strip() for pw in args.passwords.split(',') if pw.strip()]
                test_password = pw_list[0] if pw_list else 'password'
        else:
            test_password = 'password'
        brute_force(
            url=args.url,
            username=test_username,
            password_list=[test_password],
            delay=args.delay,
            success_url=args.success_url,
            verbose=True,
            username_selector=args.username_selector,
            password_selector=args.password_selector,
            proxy=args.proxy
        )
        return

    if not is_generator:
        # list mode
        if args.workers == 1:
            from .auto_brute import brute_force
            total = len(password_list)
            start_time = time.time()
            for idx, pwd in enumerate(password_list):
                print_progress(idx+1, total, start_time)
                # Save resume state
                if args.resume:
                    save_resume({'index': idx+1, 'total': total, 'passwords': password_list})
                brute_force(
                    url=args.url,
                    username=args.username,
                    password_list=[pwd],
                    delay=args.delay,
                    success_url=args.success_url,
                    verbose=True,
                    username_selector=args.username_selector,
                    password_selector=args.password_selector,
                    proxy=args.proxy,
                    success_message=args.success_message
                )
            print()  # Newline after progress
            if args.resume:
                clear_resume()
        else:
            chunk_size = math.ceil(len(password_list) / args.workers)
            processes = []
            with Manager() as manager:
                found_flag = manager.Value('b', False)
                # For resume: track which passwords have been tried
                tried_pw = resume_state.get('tried', []) if args.resume and resume_state else []
                for i in range(args.workers):
                    sublist = password_list[i*chunk_size:(i+1)*chunk_size]
                    # Remove already tried passwords from sublist
                    sublist = [pw for pw in sublist if pw not in tried_pw]
                    p = Process(target=worker_list_mode, args=(sublist, args, found_flag))
                    p.start()
                    processes.append(p)
                for p in processes:
                    p.join()
                    # If found_flag is set, terminate all other processes
                    if found_flag.value:
                        for proc in processes:
                            if proc.is_alive():
                                proc.terminate()
                        break
                # After all workers, save which passwords have been tried
                if args.resume:
                    tried_pw += password_list
                    save_resume({'tried': tried_pw})
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
                    # If found_flag is set, terminate all other processes
                    if found_flag.value:
                        for proc in processes:
                            if proc.is_alive():
                                proc.terminate()
                        break
                if found_flag.value:
                    print(f"[INFO] Password found at length {pw_length}, stopping further attempts.")
                    break
            else:
                print("[INFO] All lengths tried, no password found.")

if __name__ == '__main__':
    main()