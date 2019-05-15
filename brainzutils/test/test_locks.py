import unittest
import tempfile
import shutil
import time
import os.path
import signal
from multiprocessing import Process
from brainzutils import locks


class LockedOpenTestCase(unittest.TestCase):
    test_data = b"testing"

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.file_path = os.path.join(self.temp_dir, "test.txt")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_write(self):
        with locks.locked_open(self.file_path, locks.M_WRITE) as f:
            f.write(self.test_data)
        self.assertEqual(self.test_data, _read(self.file_path))

    def test_read(self):
        _write(self.file_path, self.test_data)
        with locks.locked_open(self.file_path, locks.M_READWRITE) as f:
            self.assertEqual(self.test_data, f.read())

    def test_read_write(self):
        _write(self.file_path, self.test_data)
        with locks.locked_open(self.file_path, locks.M_READWRITE) as f:
            data = f.read().swapcase()
            f.seek(0)
            f.write(data)
        self.assertEqual(self.test_data.swapcase(), _read(self.file_path))

    def test_concurrent_read(self):
        _write(self.file_path, self.test_data)
        with locks.locked_open(self.file_path, locks.M_READ) as f1:
            with locks.locked_open(self.file_path, locks.M_READ) as f2:
                self.assertEqual(self.test_data, f1.read())
                self.assertEqual(self.test_data, f2.read())

    def test_non_blocking_read_during_write(self):
        with locks.locked_open(self.file_path, locks.M_WRITE):
            with self.assertRaises(IOError):
                with locks.locked_open(self.file_path, locks.M_READ, blocking=False):
                    pass

    def test_non_blocking_write_during_read(self):
        _write(self.file_path, self.test_data)
        with locks.locked_open(self.file_path, locks.M_READ):
            with self.assertRaises(IOError):
                with locks.locked_open(self.file_path, locks.M_WRITE, blocking=False):
                    pass

    def test_multiprocess_read(self):
        _write(self.file_path, self.test_data)

        def func_blocker(self):
            with locks.locked_open(self.file_path, locks.M_READ):
                while True:
                    pass

        def func_other(self):
            with self.assertRaises(IOError):
                with locks.locked_open(self.file_path, locks.M_WRITE, blocking=False):
                    pass

        p_blocker = Process(target=func_blocker, args=(self,))
        p_other = Process(target=func_other, args=(self,))
        try:
            p_blocker.start()
            timeout = time.time() + 5  # seconds
            while not p_blocker.is_alive():
                if time.time() > timeout:
                    raise Exception("Failed to start blocker process!")
            p_other.start()

            p_other.join(1)
            p_blocker.terminate()
            time.sleep(.3)

            self.assertFalse(p_other.is_alive())
            self.assertEqual(p_other.exitcode, 0)

            self.assertFalse(p_blocker.is_alive())
            self.assertEqual(p_blocker.exitcode, -signal.SIGTERM)

        finally:
            # In case anything above fails, still need to terminate the processes
            p_blocker.terminate()
            p_other.terminate()


def _write(path, data):
    with open(path, "wb") as f:
        f.write(data)


def _read(path):
    with open(path, "rb") as f:
        return f.read()
