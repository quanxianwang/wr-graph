
#ifndef __PROFILE_ANALYZER_H
#define __PROFILE_ANALYZER_H

#ifdef  __cplusplus
extern "C" {
#endif

#include <time.h>
#include <stdio.h>
#include <sys/time.h>
#define ADD_PROFILING_POINT(msg) \
	do { \
		struct timespec tp; \
		unsigned int time; \
		clock_gettime(CLOCK_REALTIME, &tp); \
		time = (tp.tv_sec * 1000000L) + (tp.tv_nsec / 1000); \
		fprintf(stderr, "[%10.3f]profiling_point:%s\n", \
			time / 1000.0, msg); \
	} while(0)

#define ADD_PROFILING_START(msg) \
    do { \
        struct timespec tp; \
        unsigned int time; \
        clock_gettime(CLOCK_REALTIME, &tp); \
        time = (tp.tv_sec * 1000000L) + (tp.tv_nsec / 1000); \
        fprintf(stderr, "[%10.3f]profiling_start:%s\n", \
            time / 1000.0, msg); \
    } while(0)

#define ADD_PROFILING_END(msg) \
    do { \
        struct timespec tp; \
        unsigned int time; \
        clock_gettime(CLOCK_REALTIME, &tp); \
        time = (tp.tv_sec * 1000000L) + (tp.tv_nsec / 1000); \
        fprintf(stderr, "[%10.3f]profiling_end:%s\n", \
            time / 1000.0, msg); \
    } while(0)

#ifdef  __cplusplus
}
#endif

#endif
