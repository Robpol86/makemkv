/*
    Designed for makemkvcon running inside a Docker container writing MKV files to /output.

    For umask:
        The problem:
        makemkvcon creates MKV files with the maximum of 0644 file mode. The current umask limits the maximum file mode,
        but does not itself increase permissions (only decreases). This means when a user has a umask of 0002 and
        touches a new file, it will have permissions of 664. However when makemkvcon runs MKV files will have
        permissions of 644.

        The solution:
        This code compiles into a shared object which is loaded at the beginning of makemkvcon's execution. This will
        intercept open(3) syscalls and modify the requested mode if a new MKV file inside /output is opened.

    For named pipe:
        Every time makemkvcon closes an MKV file this library will write the file path to a named pipe maintained by the
        calling bash script. This lets the bash script fire a hook after each MKV file is done ripping while makemkvcon
        is running.

    Build:
    gcc -o wrappers.so wrappers.c -fPIC -shared

    Usage:
    LD_PRELOAD=/wrappers.so makemkvcon ...
 */

#define _GNU_SOURCE
#define ERROR(msg) fprintf(stderr, "ERROR %s:%d %s: %s\n", __FILE__, __LINE__, __PRETTY_FUNCTION__, msg)
#define FIFO_FILE "/tmp/titles_done"
#define O_WRONLY 00000001

#include <dlfcn.h>
#include <errno.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>


static int fifo_fd;
static int (*real_close)(int fd);
static int (*real_open)(const char *path, int flags, mode_t mode);
static void init(void) __attribute__((constructor));
static void fini(void) __attribute__((destructor));


// Constructor.
static void init(void) {
    real_close = dlsym(RTLD_NEXT, "close");
    real_open = dlsym(RTLD_NEXT, "open");

    // Create and open fifo file.
    char error_str[255];
    if (mkfifo(FIFO_FILE, 0600) == -1) {
        sprintf(error_str, "Failed to create %s: %d %s", FIFO_FILE, errno, strerror(errno));
        ERROR(error_str);
    } else if ((fifo_fd = open(FIFO_FILE, O_WRONLY)) == -1) {
        sprintf(error_str, "Failed to open %s for writing: %d %s", FIFO_FILE, errno, strerror(errno));
        ERROR(error_str);
    } else {
        dprintf(fifo_fd, "%s%c", __func__, 0);
    }
}


// Destructor.
static void fini(void) {
    if (fifo_fd > 0) {
        dprintf(fifo_fd, "%s%c", __func__, 0);
        real_close(fifo_fd);
    }
}


// Determine if path is an MKV file we're interested in.
bool is_mkv(const char *path) {
    // Shortest possible "valid" path is "/output/title00.mkv" which is 19 chars.
    if (!path || strlen(path) < 19) return false;

    // Make sure file is in /output.
    if (strncmp("/output/", path, sizeof("/output/") - 1) != 0) return false;

    // Lastly make sure file extension is ".mkv".
    char *dot = strrchr(path, '.');
    return dot && !strcmp(dot, ".mkv");
}


// Return true if file is not empty.
bool not_empty(const char *path) {
    struct stat st;
    stat(path, &st);
    off_t size = st.st_size;
    return size > 0;
}


// Wrapping open() function call for umask purposes.
int open(const char *path, int flags, mode_t mode) {
    // Don't intercept calls that don't open MKV files in /output.
    if (!is_mkv(path)) return real_open(path, flags, mode);

    // Call with new mode (from touch command source code).
    return real_open(path, flags, S_IRUSR | S_IWUSR | S_IRGRP | S_IWGRP | S_IROTH | S_IWOTH);
}


// Wrapping close() function call for named pipe purposes.
int close(int fd) {
    // First resolve file descriptor to real path of file before closing.
    char link_name[sizeof("/proc/self/fd/") + 4];
    snprintf(link_name, sizeof link_name, "/proc/self/fd/%d", fd);  // Set link_name to something like: /proc/self/fd/16
    char *path = realpath(link_name, NULL);

    // Make sure file is MKV and not empty. Close fd here since we don't need it open anymore.
    int ret = real_close(fd);
    bool write_fifo = is_mkv(path) && not_empty(path);

    // Write to named pipe.
    if (fifo_fd > 0 && write_fifo) {
        write(fifo_fd, path, strlen(path) + 1);  // Include null byte. Bash script looks for it.
        fsync(fifo_fd);
    }

    free(path);
    return ret;
}
