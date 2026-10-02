import logging

def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.info('{"event":"worker_started","service":"nomos-worker"}')

if __name__ == "__main__":
    main()
