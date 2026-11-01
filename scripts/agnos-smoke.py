#!/usr/bin/env python3
# agnos-smoke.py — run agora on a real AGNOS kernel in QEMU and check what only
# AGNOS can show: the poll sweep's send path (1.12.3 / 1.12.4, ADR 0023).
#
# Usage:
#   CYRIUS_DCE=1 cyrius build --agnos src/main.cyr build/agora-agnos
#   CYRIUS_DCE=1 cyrius build src/main.cyr build/agora    (the host reference)
#   python3 scripts/agnos-smoke.py
#
# Manual, not CI: it needs an agnos kernel and rootfs built from the agnos
# repo, gnoboot's BOOTX64.EFI, OVMF, qemu-system-x86_64, parted, sgdisk,
# mtools and mkfs.ext2. Paths and knobs, all overridable:
#   AGNOS_KERNEL   ../agnos/build/agnos      (agnos >= 1.57.13 for sock_send_dl #109)
#   AGNOS_ROOTFS   ../agnos/build/rootfs     (needs bin/agnsh)
#   GNOBOOT_EFI    ../gnoboot/build/BOOTX64.EFI
#   AGORA_AGNOS    build/agora-agnos          (the binary under test)
#   AGORA_HOST     build/agora                (renders the expected byte counts)
#   AGORA_EXPECT_VERSION   VERSION's contents (for an older binary)
#   AGNOS_ACCEL    QEMU CPU / accelerator args, default "-cpu max": single-CPU
#                  TCG, the form agnos's own -smp 1 smokes use. Timings are only
#                  comparable between runs with the same value; "-enable-kvm
#                  -cpu host" is much faster.
#   SMOKE_STALL_SECS   how long the bystander is watched (default 60)
#
# It boots agnos with the rootfs plus agora at /bin/agora and a store at /bbs
# holding one ~61 KB post (smoke 31's), types `agora serve 2323 --store /bbs`
# at agnsh over QEMU's monitor, and talks to it from the host over QEMU user
# networking (a hostfwd to the guest's 2323). The serial log is kept in a
# temporary directory and printed; nothing else outside one is written.
#
# What is checked, and why it needs AGNOS:
#   serve      agora starts on agnos, listens, and greets with this version
#   read       a reading client's `read 1` arrives whole (the host binary's
#              byte count). Its rate is reported: on agnos >= 1.57.13 the drain
#              sends without waiting, and the kernel keeps ONE segment in
#              flight per connection, so a segment goes only once the one
#              before it is ACKed: one per sweep when the ACK is not back
#              within the drain (the floor), more when the peer ACKs at once
#   make-room  four pipelined `read 1` (~245 KB, more than the 128 KB tx queue)
#              arrive whole: the make-room drain may wait (one send, at most
#              SESS_DRAIN_WAIT_US = 250 ms) instead of dropping a session whose
#              command outgrew the queue (1.8.1 S5)
#   page       (1.13.0, ADR 0034) after an 80x10 window report, `help` stops
#              at `--More--` with the rest held in the queue (the drain stops at
#              the output gate's hold), and Enter turns the pages until every
#              line has arrived once and the prompt follows
#   bystander  while a client with a 4 KB receive buffer asks for ~12 MB and
#              reads NOTHING, another session's keystroke echo stays prompt
#              (< 1 s) for SMOKE_STALL_SECS. This is the check that needs the
#              kernel: once QEMU's buffers fill, the non-reader's window
#              closes, and a raw sock_send #48 per drain (agora 1.12.2) then
#              holds the shared sweep for #48's ~8 s progress window, per sweep
#   dropped    the non-reader stops being served (its queue overflowed) having
#              been handed less than half of what it asked for. How it ended is
#              reported but not required: agnos gives up on the closed conn's
#              held FIN slot after 5 resends (~47 s) and then answers nothing the
#              peer sends with a RST (agnos issue 2026-10-31), so the host behind
#              QEMU's user network sees no EOF
#   xreply     (1.13.1, ADR 0035; needs openssl) a logged-in client posts on pub,
#              replies to it from tech with `reply pub/1`, and pub's `read 1`
#              lists `tech/1`: a cross-board reply takes both boards' flock#59
#              locks at once on the agnos kernel, and pub's index is built on
#              its ext2 store
#   descent    (needs openssl, for the login signature) a logged-in client
#              steps into the Descent, whose endpoint (<store>/.descent) is a
#              stub MUD on the host that reads 64 KB and then stops reading;
#              the client keeps typing (8 MB), and a bystander's echo stays
#              prompt for SMOKE_STALL_SECS. Through agora 1.12.3 the write to
#              the MUD was the stdlib's agnos `sys_write`, which retries for a
#              30 s stall deadline re-armed on progress, inside the sweep
# Not covered: the #48 fallback on a kernel before 1.57.13 (only a current
# kernel is booted), and the shutdown goodbye (no signal reaches the guest).
#
# A FAIL is a result, not a broken harness. Run it against the 1.12.2 agnos
# binary (AGORA_AGNOS=… AGORA_EXPECT_VERSION=1.12.2) to see `bystander` go red,
# and against 1.12.3 to see `descent` go red.

import binascii, os, re, shutil, socket, subprocess, sys, tempfile, threading, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIB = os.path.dirname(ROOT)


def env(name, default):
    v = os.environ.get(name, "")
    return v if v else default


KERNEL = env("AGNOS_KERNEL", os.path.join(SIB, "agnos/build/agnos"))
ROOTFS = env("AGNOS_ROOTFS", os.path.join(SIB, "agnos/build/rootfs"))
GNOBOOT = env("GNOBOOT_EFI", os.path.join(SIB, "gnoboot/build/BOOTX64.EFI"))
AGORA = env("AGORA_AGNOS", os.path.join(ROOT, "build/agora-agnos"))
HOST = env("AGORA_HOST", os.path.join(ROOT, "build/agora"))
ACCEL = env("AGNOS_ACCEL", "-cpu max").split()
STALL_SECS = int(env("SMOKE_STALL_SECS", "60"))
with open(os.path.join(ROOT, "VERSION")) as f:
    WANT_VER = env("AGORA_EXPECT_VERSION", f.read().strip())

GUEST_PORT = 2323
READS = 200            # the non-reader's `read 1` x ~61 KB each, as smoke 31
ECHO_SLOW_MS = 1000    # smoke 31's bound for a bystander's echo
MUD_READS = 65536      # what the stub MUD reads before it stops reading
FLOOD = 8 * 1048576    # what the Descent client types at it
MUD_BANNER = b"stub MUD ready"
MORE = b"--More-- (Enter; q to stop)"
NAWS_80x10 = bytes([255, 251, 31, 255, 250, 31, 0, 80, 0, 10, 255, 240])
PKCS8 = bytes.fromhex("302e020100300506032b657004220420")   # Ed25519 seed -> DER (smoke 37)
HAVE_OPENSSL = shutil.which("openssl") is not None


def die(msg):
    print("agnos-smoke: " + msg, file=sys.stderr)
    sys.exit(2)


def p(*a):
    print(*a, flush=True)


for path in (KERNEL, os.path.join(ROOTFS, "bin/agnsh"), GNOBOOT, AGORA, HOST):
    if not os.path.lexists(path):
        die("missing " + path)
for tool in ("qemu-system-x86_64", "parted", "sgdisk", "mformat", "mcopy", "mkfs.ext2"):
    if shutil.which(tool) is None:
        die("missing tool " + tool)

OVMF_CODE = OVMF_VARS = None
for c in ("/usr/share/edk2/x64/OVMF_CODE.4m.fd", "/usr/share/edk2/x64/OVMF_CODE.fd",
          "/usr/share/OVMF/OVMF_CODE.fd", "/usr/share/OVMF/OVMF_CODE_4M.fd"):
    if os.path.exists(c):
        OVMF_CODE = c
        break
for c in ("/usr/share/edk2/x64/OVMF_VARS.4m.fd", "/usr/share/edk2/x64/OVMF_VARS.fd",
          "/usr/share/OVMF/OVMF_VARS.fd", "/usr/share/OVMF/OVMF_VARS_4M.fd"):
    if os.path.exists(c):
        OVMF_VARS = c
        break
if not OVMF_CODE or not OVMF_VARS:
    die("OVMF not found")


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def seed_store(store):
    os.makedirs(store, exist_ok=True)
    with open(os.path.join(store, "1.txt"), "w") as f:
        f.write("Subject: big\r\n\r\n" + ("x" * 100 + "\r\n") * 600)


def grab(s, idle):
    """Read until `idle` seconds pass with nothing new; (bytes, time of the last byte)."""
    s.settimeout(idle)
    out = b""
    last = time.time()
    while True:
        try:
            d = s.recv(65536)
        except socket.timeout:
            return out, last
        except OSError:
            return out, last
        if not d:
            return out, last
        out += d
        last = time.time()


def connect(port, timeout=20):
    deadline = time.time() + timeout
    while True:
        try:
            return socket.create_connection(("127.0.0.1", port), timeout=10)
        except OSError:
            if time.time() > deadline:
                raise
            time.sleep(0.5)


def until(s, needle, t):
    out, end = b"", time.time() + t
    s.settimeout(0.2)
    while needle not in out and time.time() < end:
        try:
            d = s.recv(65536)
        except socket.timeout:
            continue
        except OSError:
            break
        if not d:
            break
        out += d
    return out


def sign(nonce):
    kf = os.path.join(WORK, "qix.der")
    with open(kf, "wb") as f, open(KEY, "rb") as k:
        f.write(PKCS8 + k.read())
    mf = os.path.join(WORK, "login.msg")
    with open(mf, "wb") as f:
        f.write(b"agora-login:" + nonce)
    return binascii.hexlify(subprocess.check_output(
        ["openssl", "pkeyutl", "-sign", "-rawin", "-inkey", kf, "-keyform", "DER", "-in", mf]))


def watch(v, secs):
    """Type one key at a time for `secs`; (worst echo ms, keys, [(s, ms) of the slow ones])."""
    worst, n, slow = 0.0, 0, []
    t_start = time.time()
    while time.time() - t_start < secs:
        t0 = time.time()
        v.sendall(b"x")
        v.settimeout(30)
        try:
            v.recv(64)
            ms = (time.time() - t0) * 1000
        except OSError:
            ms = 30000.0
        n += 1
        worst = max(worst, ms)
        if ms >= ECHO_SLOW_MS:
            slow.append((round(time.time() - t_start, 1), round(ms)))
        time.sleep(0.2)
    return worst, n, slow


def measure(port, idle):
    """The byte counts the checks compare: greeting, `read 1`, four pipelined."""
    s = connect(port)
    greet, _ = grab(s, idle)
    t0 = time.time()
    s.sendall(b"read 1\r\n")
    one, t1 = grab(s, idle)
    t2 = time.time()
    s.sendall(b"read 1\r\n" * 4)
    four, t3 = grab(s, idle)
    s.close()
    return greet, one, t1 - t0, four, t3 - t2


# The host reference: the same store, the poll model, the same client.
HDIR = tempfile.mkdtemp(prefix="agora-host-")
seed_store(os.path.join(HDIR, "bbs"))
hport = free_port()
host = subprocess.Popen([HOST, "serve", str(hport), "--store", os.path.join(HDIR, "bbs")],
                        env=dict(os.environ, AGORA_SERVE="poll"),
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    _, H_ONE, _, H_FOUR, _ = measure(hport, 1.5)
finally:
    host.terminate()
    try:
        host.wait(timeout=5)
    except subprocess.TimeoutExpired:
        host.kill()
    shutil.rmtree(HDIR, ignore_errors=True)
if len(H_ONE) < 60000 or len(H_FOUR) < 4 * 60000:
    die("host reference looks wrong: read 1 = %d B, x4 = %d B" % (len(H_ONE), len(H_FOUR)))

WORK = tempfile.mkdtemp(prefix="agora-agnos-")
SEED = os.path.join(WORK, "seed")
IMG = os.path.join(WORK, "disk.img")
SER = os.path.join(WORK, "serial.log")
# A UNIX socket path is at most 108 bytes, which a deep TMPDIR overruns: the
# monitor gets its own short directory.
QDIR = tempfile.mkdtemp(prefix="agora-q-", dir=os.environ.get("XDG_RUNTIME_DIR") or "/tmp")
MON = os.path.join(QDIR, "mon.sock")


def sh(cmd):
    r = subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if r.returncode != 0:
        die("image step failed: " + cmd + "\n" + r.stderr.decode("latin1")[:400])


subprocess.run(["cp", "-a", ROOTFS, SEED], check=True)
shutil.copyfile(AGORA, os.path.join(SEED, "bin/agora"))
os.chmod(os.path.join(SEED, "bin/agora"), 0o755)
seed_store(os.path.join(SEED, "bbs"))


class StubMud(threading.Thread):
    """The Descent's endpoint: greets, reads MUD_READS bytes, then never reads again."""

    def __init__(self):
        super().__init__(daemon=True)
        self.ls = socket.socket()
        self.ls.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4096)   # inherited by the accept
        self.ls.bind(("127.0.0.1", 0))
        self.ls.listen(4)
        self.port = self.ls.getsockname()[1]
        self.got = 0
        self.conn = None
        self.done = threading.Event()

    def run(self):
        try:
            c, _ = self.ls.accept()
        except OSError:
            return
        self.conn = c
        try:
            c.sendall(MUD_BANNER + b"\r\n")
            while self.got < MUD_READS:
                d = c.recv(65536)
                if not d:
                    return
                self.got += len(d)
        except OSError:
            return
        self.done.wait()

    def stop(self):
        self.done.set()
        for s in (self.conn, self.ls):
            try:
                if s:
                    s.close()
            except OSError:
                pass


mud = None
KEY = os.path.join(WORK, "qix.key")
if HAVE_OPENSSL:
    subprocess.run([HOST, "keygen", "--key", KEY], stdout=subprocess.DEVNULL, check=True)
    subprocess.run([HOST, "register", "--handle", "qix", "--key", KEY, "--store", os.path.join(SEED, "bbs")],
                   stdout=subprocess.DEVNULL, check=True)
    mud = StubMud()
    mud.start()
    # QEMU's user network answers the guest's 10.0.2.2 from the host's loopback.
    with open(os.path.join(SEED, "bbs/.descent"), "w") as f:
        f.write("10.0.2.2:%d\n" % mud.port)

PART_OFFSET = 33 * 1048576
PART_BLOCKS = (67 * 1048576) // 4096
FEATURES = "^resize_inode,^dir_index,^metadata_csum,^64bit,^uninit_bg"
sh(f"dd if=/dev/zero of={IMG} bs=1M count=128 status=none")
sh(f"parted -s {IMG} mklabel gpt mkpart ESP fat32 1MiB 33MiB set 1 esp on mkpart agnos-fs ext2 33MiB 100MiB")
sh(f"sgdisk -t 2:8300 {IMG}")
sh(f"mformat -i {IMG}@@1048576 -F")
sh(f"mmd -i {IMG}@@1048576 ::EFI ::EFI/BOOT ::boot")
sh(f"mcopy -i {IMG}@@1048576 {GNOBOOT} ::EFI/BOOT/BOOTX64.EFI")
sh(f"mcopy -i {IMG}@@1048576 {KERNEL} ::boot/agnos")
sh(f"mkfs.ext2 -F -q -L AGORA-SMOKE -b 4096 -m 0 -O {FEATURES} -d {SEED} -E offset={PART_OFFSET} {IMG} {PART_BLOCKS}")
shutil.copyfile(OVMF_VARS, os.path.join(WORK, "vars.fd"))
open(SER, "w").close()

HP = free_port()
qemu = subprocess.Popen([
    "qemu-system-x86_64", "-machine", "q35", "-m", "512M"] + ACCEL + [
    "-drive", f"if=pflash,format=raw,readonly=on,file={OVMF_CODE}",
    "-drive", f"if=pflash,format=raw,file={WORK}/vars.fd",
    "-drive", f"file={IMG},format=raw,if=none,id=disk0",
    "-device", "nvme,drive=disk0,serial=AGORA-SMOKE",
    "-device", "qemu-xhci,id=xhci", "-device", "usb-kbd,bus=xhci.0",
    "-netdev", f"user,id=n0,hostfwd=tcp:127.0.0.1:{HP}-:{GUEST_PORT}",
    "-device", "virtio-net-pci,netdev=n0",
    "-serial", f"file:{SER}", "-display", "none", "-no-reboot",
    "-monitor", f"unix:{MON},server,nowait",
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# HMP sendkey names for the bytes the command uses.
KEYS = {' ': 'spc', '\n': 'ret', '-': 'minus', '.': 'dot', '/': 'slash'}

results = []
rc = 1
try:
    mon = None
    for _ in range(60):
        try:
            mon = socket.socket(socket.AF_UNIX)
            mon.connect(MON)
            break
        except OSError:
            mon = None
            time.sleep(0.2)
    if mon is None:
        die("no QEMU monitor")
    mon.settimeout(1.0)

    def drain_mon():
        try:
            while True:
                mon.recv(65536)
        except OSError:
            pass

    def ser():
        try:
            with open(SER, "rb") as f:
                return f.read().decode("latin1")
        except OSError:
            return ""

    def typ(text):
        for ch in text:
            key = KEYS.get(ch, ch)
            mon.sendall(("sendkey " + key + "\n").encode())
            time.sleep(0.10)
            drain_mon()

    def check(name, ok, detail):
        results.append((name, ok))
        p(f"  {'PASS' if ok else 'FAIL'}  {name}: {detail}")

    p("accel:", " ".join(ACCEL))
    booted = False
    for _ in range(480):
        if "agnoshi" in ser():
            booted = True
            break
        time.sleep(0.25)
    if not booted:
        die("agnsh never came up; serial log: " + SER)
    kver = re.search(r"AGNOS kernel v([0-9]+\.[0-9]+\.[0-9]+)", ser())
    p("agnos kernel:", kver.group(1) if kver else "(version not seen)")
    time.sleep(1.0)
    # The first key of a session is swallowed by the HID path (agnos's harness
    # README): absorb it with a bare Enter.
    typ("\n")
    time.sleep(2.0)

    typ("agora serve %d --store /bbs\n" % GUEST_PORT)
    up = False
    deadline = time.time() + 60
    while time.time() < deadline:
        if "waiting for connections" in ser():
            up = True
            break
        time.sleep(0.5)
    if not up:
        tail = ser()[-400:]
        check("serve", False, "no listener after 60 s; console tail: " + repr(tail))
        raise SystemExit
    greet, one, one_s, four, four_s = measure(HP, 6.0)
    banner = "agora " + WANT_VER
    seen = banner in greet.decode("latin1")
    check("serve", seen, "%d-byte greeting, %s" % (len(greet), ("'%s' seen" if seen else "no '%s'") % banner))
    rate = len(one) / one_s / 1024 if one_s > 0 else 0
    check("read", len(one) == len(H_ONE),
          "%d of %d B in %.2f s (%.0f KB/s)" % (len(one), len(H_ONE), one_s, rate))
    check("make-room", len(four) == len(H_FOUR),
          "%d of %d B in %.2f s (%.0f KB/s), more than the 128 KB queue"
          % (len(four), len(H_FOUR), four_s, len(four) / four_s / 1024 if four_s > 0 else 0))

    # The page stop: the poll drain sends up to the gate's hold and no further.
    pg = connect(HP)
    grab(pg, 3.0)
    pg.sendall(NAWS_80x10 + b"help\r\n")
    seen = until(pg, MORE, 20.0)
    stopped = seen.endswith(MORE) and b"close the session" not in seen
    turns = 0
    while turns < 10 and seen.endswith(MORE):
        pg.sendall(b"\r\n")
        more, _ = grab(pg, 3.0)
        seen += more
        turns += 1
    check("page", stopped and seen.count(b"close the session") == 1 and seen.endswith(b"\r\n> "),
          "stopped at --More--: %s; %d turns; the last line %d time(s); prompt last: %s"
          % (stopped, turns, seen.count(b"close the session"), seen.endswith(b"\r\n> ")))
    pg.close()

    # The non-reader first, then a bystander that types one key at a time.
    a = socket.socket()
    a.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4096)
    a.settimeout(20)
    a.connect(("127.0.0.1", HP))
    a.sendall(b"read 1\r\n" * READS)
    v = connect(HP)
    grab(v, 3.0)
    worst, n, slow = watch(v, STALL_SECS)
    detail = "worst echo %.0f ms over %d keys in %d s" % (worst, n, STALL_SECS)
    if slow:
        detail += "; slow at (s, ms): %s" % slow[:6]
    check("bystander", worst < ECHO_SLOW_MS, detail)
    v.close()

    # Read what QEMU and the host buffered for the non-reader. A session agora
    # still served would keep sending once the window reopens; a dropped one
    # goes quiet. EOF is reported, not required. agora's close leaves the agnos
    # kernel a held FIN slot, which the persist cap does not cover, so it is
    # given up on after TCP_RTO_RETRIES (5) resends (1+2+4+8+16+16 s, ~47 s)
    # with its data and FIN undelivered; after that the kernel drops whatever
    # the peer sends without a RST (agnos issue 2026-10-31, "a segment for no
    # connection gets no RST"). So QEMU's user network, and the host behind it,
    # never see the close.
    got, _ = grab(a, 8.0)
    eof = "no EOF"
    try:
        a.settimeout(2.0)
        if a.recv(1) == b"":
            eof = "EOF"
    except (ConnectionResetError, BrokenPipeError):
        eof = "reset"
    except OSError:
        pass
    asked = READS * len(H_ONE)
    check("dropped", len(got) < asked // 2,
          "went quiet after %d of the %d B it asked for (%s)" % (len(got), asked, eof))
    a.close()

    if mud is None:
        p("  SKIP  descent: needs openssl (the login signature)")
    else:
        d = connect(HP)
        grab(d, 3.0)
        d.sendall(b"login qix\r\n")
        out = until(d, b"auth:", 20.0)
        m = re.search(rb"challenge:\s*([0-9a-f]+)", out)
        logged = False
        if m:
            d.sendall(b"auth: " + sign(m.group(1)) + b"\r\n")
            out = until(d, b"welcome, qix", 20.0)
            logged = b"welcome, qix" in out
        if not logged:
            check("descent", False, "login failed: %r" % out[-120:])
        else:
            d.sendall(b"descent\r\n")
            out = until(d, MUD_BANNER, 30.0)
            if MUD_BANNER not in out:
                check("descent", False, "no MUD banner: %r" % out[-160:])
            else:
                def flood():
                    try:
                        d.settimeout(STALL_SECS + 30)
                        d.sendall(b"x" * FLOOD)
                    except OSError:
                        pass
                threading.Thread(target=flood, daemon=True).start()
                v = connect(HP)
                grab(v, 3.0)
                worst, n, slow = watch(v, STALL_SECS)
                detail = "worst echo %.0f ms over %d keys in %d s; the MUD read %d B, then stopped" % (
                    worst, n, STALL_SECS, mud.got)
                if slow:
                    detail += "; slow at (s, ms): %s" % slow[:6]
                check("descent", worst < ECHO_SLOW_MS and mud.got >= MUD_READS, detail)
                v.close()
        d.close()

    if HAVE_OPENSSL:
        x = connect(HP)
        grab(x, 3.0)
        x.sendall(b"login qix\r\n")
        out = until(x, b"auth:", 20.0)
        m = re.search(rb"challenge:\s*([0-9a-f]+)", out)
        ok = False
        detail = "login failed"
        if m:
            x.sendall(b"auth: " + sign(m.group(1)) + b"\r\n")
            if b"welcome, qix" in until(x, b"welcome, qix", 20.0):
                steps = [b"enter pub", b"post", b"orig", b"the parent", b".", b"enter tech",
                         b"reply pub/1", b"from tech", b"."]
                for st in steps:
                    x.sendall(st + b"\r\n")
                    if st == b".":
                        until(x, b"posted as #", 30.0)
                    else:
                        grab(x, 1.0)
                x.sendall(b"enter pub\r\n")
                grab(x, 1.0)
                x.sendall(b"read 1\r\n")
                out = until(x, b"Replies:", 20.0) + until(x, b"> ", 3.0)
                line = [l for l in out.split(b"\r\n") if l.startswith(b"Replies: ")]
                ok = bool(line) and line[0] == b"Replies: tech/1"
                detail = "pub's read 1: %r" % (line[0] if line else out[-80:])
        check("xreply", ok, detail)
        x.close()

    p("serial log:", SER)
    rc = 0 if all(ok for _, ok in results) else 1
    p("agnos-smoke:", "PASS" if rc == 0 else "FAIL", f"({sum(ok for _, ok in results)}/{len(results)})")
    try:
        mon.sendall(b"quit\n")
    except OSError:
        pass
except SystemExit:
    p("serial log:", SER)
    p("agnos-smoke: FAIL (serve)")
    rc = 1
finally:
    if mud is not None:
        mud.stop()
    qemu.terminate()
    try:
        qemu.wait(timeout=3)
    except subprocess.TimeoutExpired:
        qemu.kill()
    shutil.rmtree(QDIR, ignore_errors=True)
sys.exit(rc)
