import argparse
import os
import string
import itertools

def main():
    parser = argparse.ArgumentParser(description="Auto password brute force for web login forms.")
    parser.add_argument('url', help='Login page URL')
    parser.add_argument('--username', help='Username to try (optional)', default=None)
    parser.add_argument('--passwords', help='Password list file (optional)')
    parser.add_argument('--delay', type=int, default=2, help='Delay between attempts (seconds)')
    parser.add_argument('--success_url', help='URL after successful login (optional)')
    parser.add_argument('--workers', type=int, default=1, help='Number of parallel browser windows (default: 1)')
    args = parser.parse_args()

    password_list = None
    if args.passwords:
        with open(args.passwords, encoding='utf-8') as f:
            password_list = [line.strip() for line in f if line.strip()]
    else:
        # Check if default_passwords/password.txt exists
        pwd_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'default_passwords', 'password.txt')
        if os.path.exists(pwd_path):
            with open(pwd_path, encoding='utf-8') as f:
                password_list = [line.strip() for line in f if line.strip()]
        else:
            # Auto generate all 20-char passwords with upper/lowercase, digits, and special symbols
            charset = string.ascii_letters + string.digits + string.punctuation
            password_list = (''.join(p) for p in itertools.product(charset, repeat=20))

    from .auto_brute import brute_force

    # Convert generator to list if using workers > 1 (to allow slicing)
    if not isinstance(password_list, list):
        password_list = list(password_list)

    if args.workers == 1:
        brute_force(
            url=args.url,
            username=args.username,
            password_list=password_list,
            delay=args.delay,
            success_url=args.success_url,
            verbose=True
        )
    else:
        import math
        from multiprocessing import Process
        def worker(sublist):
            brute_force(
                url=args.url,
                username=args.username,
                password_list=sublist,
                delay=args.delay,
                success_url=args.success_url,
                verbose=True
            )
        chunk_size = math.ceil(len(password_list) / args.workers)
        processes = []
        for i in range(args.workers):
            sublist = password_list[i*chunk_size:(i+1)*chunk_size]
            p = Process(target=worker, args=(sublist,))
            p.start()
            processes.append(p)
        for p in processes:
            p.join()

if __name__ == '__main__':
    main()
