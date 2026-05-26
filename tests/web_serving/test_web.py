# scripts/test_system.py

import subprocess
import time
import sys
from pathlib import Path
import re
import socket # for testing port
import urllib.request
# import html
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[2]







def check_http200(statuscode,body):
    print(f'test for http ok {"passed" if statuscode>=200 and statuscode <400 else "failed"}')
    assert statuscode>=200 and statuscode <400
    print(f'test for non-empty body {"passed" if len(body)>0 else "failed"}')
    assert len(body)>0
    return True


def check_http404(statuscode,body):
    print(f'test for http 404 {"passed" if statuscode==404 else "failed"}')
    assert statuscode==404
    return True

def check_http403(statuscode,body):
    print(f'test for http 403 {"passed" if statuscode==403 else "failed"}')
    assert statuscode==403
    return True

def check_page_version(statuscode,body):
    pattern = r'.*version:[^\n]*?\d+\..*'
    if check_http200(statuscode,body):
        extractor = HTMLTextExtractor()
        extractor.feed(body)
        plain = extractor.get_text()
        # plain = plain.splitlines()
        plain = ' '.join([line.strip() for line in plain.splitlines()])
        found_matched_piece = False
        for line in plain.splitlines():
            found_matched_piece = found_matched_piece or re.match(pattern,line,flags=re.I)
        if not found_matched_piece:
            print(f'test for matching pattern failed (looking for r{repr(r'.*version:[^\n<>]*?\d+\..*').replace("\\\\","\\")})')
            for line in plain.splitlines():
                print(f'NOT FOUND: >> {line}')
        assert found_matched_piece
        return True
    else:
        return False




def get_free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port



def wait_when_started(proc):
    for _ in range(50):
        time.sleep(0.092)
        for line in proc.stdout:
            if "Calling serve_forever() " in line:
                return True
    raise RuntimeError(f'Server did not indicate it started:\n=== STDOUT ===\n{proc.stdout}\n=== END OF STDOUT ===\n=== STDERR ===\n{proc.stderr}\n=== END OF STDERR ===\n')


class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []

    def handle_data(self, data):
        self.text.append(data)

    def get_text(self):
        return ' '.join(self.text).replace('\n', ' ')





def run_the_tst(tmp_path,path_to_executable,host,port,request_path,fn_assert_response):
    proc = subprocess.Popen(
        [sys.executable, path_to_executable, "--program", "webserve", "--port", str(port)],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        # Wait until server becomes available
        wait_when_started(proc)

        body = None
        statuscode = None
        try:
            with urllib.request.urlopen(f"http://{host}:{port}{request_path}") as r:
                body = r.read().decode()
                print(f'=== RESPONSE BODY ===\n{repr(body) if len(f"{body}")<1024+128 else repr(f"{body[:512]}[[[REPLACE]]]{body[-512:]}").replace('[[[REPLACE]]]','...\n\n...')}\n=== END RESPONSE BODY\n')
                statuscode = r.status
        except urllib.error.HTTPError as e:
            body = e
            statuscode = e.code

        assert fn_assert_response(statuscode,body)

    finally:
        proc.terminate()
        proc.wait(timeout=30)

    print("PASS")

def test_dist_prog_home_version(tmp_path):
    path_to_executable = 'dist/webserve_bundle.py'
    host = '127.0.0.1'
    port = get_free_port()
    request_path = '/'
    fn_assert_response = check_http200
    return run_the_tst(tmp_path,path_to_executable,host,port,request_path,fn_assert_response)

def test_src_prog_home_version(tmp_path):
    path_to_executable = 'src_backend/launcher.py'
    host = '127.0.0.1'
    port = get_free_port()
    request_path = '/'
    fn_assert_response = check_http200
    return run_the_tst(tmp_path,path_to_executable,host,port,request_path,fn_assert_response)

def test_dist_prog_404_version(tmp_path):
    path_to_executable = 'dist/webserve_bundle.py'
    host = '127.0.0.1'
    port = get_free_port()
    request_path = '/somethingnonexistent'
    fn_assert_response = check_http404
    return run_the_tst(tmp_path,path_to_executable,host,port,request_path,fn_assert_response)

def test_src_prog_404_version(tmp_path):
    path_to_executable = 'src_backend/launcher.py'
    host = '127.0.0.1'
    port = get_free_port()
    request_path = '/somethingnonexistent'
    fn_assert_response = check_http404
    return run_the_tst(tmp_path,path_to_executable,host,port,request_path,fn_assert_response)

def test_dist_prog_version_version(tmp_path):
    path_to_executable = 'dist/webserve_bundle.py'
    host = '127.0.0.1'
    port = get_free_port()
    request_path = '/version'
    fn_assert_response = check_page_version
    return run_the_tst(tmp_path,path_to_executable,host,port,request_path,fn_assert_response)

def test_src_prog_version_version(tmp_path):
    path_to_executable = 'src_backend/launcher.py'
    host = '127.0.0.1'
    port = get_free_port()
    request_path = '/version'
    fn_assert_response = check_page_version
    return run_the_tst(tmp_path,path_to_executable,host,port,request_path,fn_assert_response)

def test_dist_prog_endpointresolver_version(tmp_path):
    path_to_executable = 'dist/webserve_bundle.py'
    host = '127.0.0.1'
    port = get_free_port()
    request_path = '/versionx'
    fn_assert_response = check_http404
    return run_the_tst(tmp_path,path_to_executable,host,port,request_path,fn_assert_response)

def test_src_prog_endpointresolver_version(tmp_path):
    path_to_executable = 'src_backend/launcher.py'
    host = '127.0.0.1'
    port = get_free_port()
    request_path = '/versionx'
    fn_assert_response = check_http404
    return run_the_tst(tmp_path,path_to_executable,host,port,request_path,fn_assert_response)
