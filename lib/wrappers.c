/*
    Designed for makemkvcon running inside a Docker container writing MKV files to /output.

    The problem:
    makemkvcon creates MKV files with the maximum of 0644 file mode. The current umask limits the maximum file mode, but
    does not itself increase permissions (only decreases). This means when a user has a umask of 0002 and touches a new
    file, it will have permissions of 664. However when makemkvcon runs MKV files will have permissions of 644.

    The solution:
    This code compiles into a shared object which is loaded at the beginning of makemkvcon's execution. This will
    intercept open(3) syscalls and modify the requested mode if a new MKV file inside /output is opened.

    Build:
    gcc -o wrappers.so wrappers.c -fPIC -shared

    Usage:
    LD_PRELOAD=/wrappers.so makemkvcon ...
 */

#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>

// Pointers to real open(3) and close(1) functions.
static int (*real_open)(const char *path, int flags, mode_t mode);
static int (*real_close)(int fd);
static void __attribute__((constructor)) init(void) {
    real_open = dlsym(RTLD_NEXT, "open");
    real_close = dlsym(RTLD_NEXT, "close");
}

// Wrapping open(3) function call for umask purposes.
int open(const char *path, int flags, mode_t mode) {
    // Don't intercept calls that don't open files in /output.
    // Shortest possible "valid" path is "/output/title00.mkv" which is 19 chars.
    if (strlen(path) < 19 || strncmp("/output/", path, 8) != 0) return real_open(path, flags, mode);

    // Also don't intercept if file extension not .mkv:
    char *dot = strrchr(path, '.');
    if (!dot || strcmp(dot, ".mkv")) return real_open(path, flags, mode);

    // Call with new mode (from touch command source code).
    return real_open(path, flags, S_IRUSR | S_IWUSR | S_IRGRP | S_IWGRP | S_IROTH | S_IWOTH);
}

// Wrapping close(1) function call for SIGUSR1 purposes.
int close(int fd) {
    printf("INTERCEPTED: %d\n", fd);
    // TODO
    return real_close(fd);
}
