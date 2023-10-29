import gzip

def verify_gz_file(file: str) -> bool:
    try:
        with gzip.open(file, 'rt') as f:
            _ = f.read()
        return True
    except:
        return False