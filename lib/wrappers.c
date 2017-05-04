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
    gcc -o wrappers.so wrappers.c -fPIC -shared -lprocps

    Usage:
    LD_PRELOAD=/wrappers.so makemkvcon ...
 */

#define _GNU_SOURCE
#include <dlfcn.h>
#include <limits.h>
#include <proc/readproc.h>
#include <signal.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>


static pid_t bash_pid;
static int (*real_close)(int fd);
static int (*real_open)(const char *path, int flags, mode_t mode);
static void init(void) __attribute__((constructor));


// Constructor.
static void init(void) {
    real_close = dlsym(RTLD_NEXT, "close");
    real_open = dlsym(RTLD_NEXT, "open");

    // Main bash script calls sudo which calls makemkvcon. Get the bash script PID to send SIGUSR1 to.
    pid_t sudo_pid = getppid();
    PROCTAB* proc = openproc(PROC_FILLSTAT | PROC_FILLSTATUS, sudo_pid);
    if (proc) {
//        proc_t sudo_info = readproc(proc, NULL);
//        if (sudo_info) {
//            bash_pid = sudo_info.ppid;
//            free(sudo_info);
//        }
        closeproc(proc);
    }
}


// Determine if path is an MKV file we're interested in.
bool is_mkv(const char *path) {
    // Shortest possible "valid" path is "/output/title00.mkv" which is 19 chars.
    if (strlen(path) < 19) return false;

    // Make sure file is in /output.
    if (strncmp("/output/", path, sizeof("/output/") - 1) != 0) return false;

    // Lastly make sure file extension is ".mkv".
    char *dot = strrchr(path, '.');
    return dot && !strcmp(dot, ".mkv");
}


// Wrapping open() function call for umask purposes.
int open(const char *path, int flags, mode_t mode) {
    // Don't intercept calls that don't open MKV files in /output.
    if (!is_mkv(path)) return real_open(path, flags, mode);

    // Call with new mode (from touch command source code).
    return real_open(path, flags, S_IRUSR | S_IWUSR | S_IRGRP | S_IWGRP | S_IROTH | S_IWOTH);
}


// Wrapping close() function call for SIGUSR1 purposes.
int close(int fd) {
    char link_name[sizeof("/proc/self/fd/") + 4];
    char path[PATH_MAX];
    ssize_t ret;

    snprintf(link_name, sizeof link_name, "/proc/self/fd/%d", fd);  // Set link_name to something like: /proc/self/fd/16
    if ((ret = readlink(link_name, path, sizeof(path) - 1)) > 0) {
        // In here means readlink() succeeded in resolving the symlink.
        path[ret] = 0;  // Terminate string.
        if (is_mkv(path)) {
            printf("INTERCEPTED: %d -> %s\n", fd, path);
            if (bash_pid) {
                printf("SENDING SIGNAL TO %d\n", bash_pid);
                kill(bash_pid, SIGUSR1);
            }
        }
    }

    return real_close(fd);
}
