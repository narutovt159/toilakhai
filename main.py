import multiprocessing
import os

def run_script(filename):
    print(f"Đang chạy: {filename}")
    os.system(f"python3 {filename}")

if __name__ == "__main__":
    scripts = [
        "tintuc_test.py",
        "tinmoi.py",
        "positions.py",
        "giacoin.py",
        "bitcoin_news.py"
    ]

    processes = []
    for script in scripts:
        p = multiprocessing.Process(target=run_script, args=(script,))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()
