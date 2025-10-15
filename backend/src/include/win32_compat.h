#ifndef WIN32_COMPAT_H
#define WIN32_COMPAT_H

/* Only needed for MSVC - MinGW has these functions built-in */
#if defined(_WIN32) && defined(_MSC_VER)

#include <windows.h>
#include <time.h>

/* Define CLOCK_REALTIME for Windows */
#ifndef CLOCK_REALTIME
#define CLOCK_REALTIME 0
#endif

/* Windows implementation of clock_gettime */
static inline int clock_gettime(int clk_id, struct timespec *spec) {
    LARGE_INTEGER freq, count;

    if (clk_id != CLOCK_REALTIME) {
        return -1;
    }

    QueryPerformanceFrequency(&freq);
    QueryPerformanceCounter(&count);

    spec->tv_sec = (time_t)(count.QuadPart / freq.QuadPart);
    spec->tv_nsec = (long)(((count.QuadPart % freq.QuadPart) * 1000000000) / freq.QuadPart);

    return 0;
}

#endif /* _WIN32 && _MSC_VER */

#endif /* WIN32_COMPAT_H */
