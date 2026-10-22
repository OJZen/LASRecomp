"""Regenerating a smaller module removes only its obsolete numbered chunks."""
import contextlib
import io
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import gen


class CleanupTests(unittest.TestCase):
    def test_smaller_and_empty_regeneration(self):
        for starts in ([0x100000], []):
            with self.subTest(functions=len(starts)), tempfile.TemporaryDirectory() as td:
                out = Path(td)
                unrelated = ('other_1000.c', 'synthetic_1000.c.bak', 'synthetic_12.c',
                             'synthetic_notes.c', 'synthetic_extra_1000.c')
                for name in unrelated:
                    (out / name).write_text('keep me')
                for index in (0, 1, 999, 1000, 10000):
                    (out / f'synthetic_{index:03d}.c').write_text('obsolete')
                module = SimpleNamespace(
                    words=[], hi=0x100004, stats={}, lifter=SimpleNamespace(sc=False),
                    boundaries=lambda: starts, scan=lambda a, end: ({a}, set(), {}),
                    emit_function=lambda *args: ['void f_100000(Cpu *c) { (void)c; }'])
                argv = ['gen.py', 'synthetic', 'unused.nso', '0x100000', td]
                with patch.object(gen, 'Module', return_value=module), \
                        patch.object(sys, 'argv', argv), contextlib.redirect_stderr(io.StringIO()):
                    gen.main()
                expected = set(unrelated) | {'synthetic_table.c'}
                if starts:
                    expected.add('synthetic_000.c')
                    self.assertIn('void f_100000', (out / 'synthetic_000.c').read_text())
                self.assertEqual({p.name for p in out.iterdir()}, expected)
                for name in unrelated:
                    self.assertEqual((out / name).read_text(), 'keep me')
                self.assertIn(f'synthetic_fn_count = {len(starts)};',
                              (out / 'synthetic_table.c').read_text())


if __name__ == '__main__':
    unittest.main()
