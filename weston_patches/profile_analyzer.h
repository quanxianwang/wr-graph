#ifndef PERF_LOG
#define PERF_LOG

#include <time.h>
#include <stdio.h>
#include <sys/time.h>

#define START 0
#define END 1
#define PERF_TIME(msg, flag) \
	do { \
		struct timeval tv; \
		struct tm *brokendown_time;\
		char string[128];\
		gettimeofday(&tv, NULL);\
		brokendown_time = localtime(&tv.tv_sec);\
		strftime(string, sizeof(string),\
				 "%H:%M:%S", brokendown_time);\
		fprintf(stderr, "[%s.%06li] perf_%s:%s\n",\
				string, tv.tv_usec, flag?"end":"start", msg); \
	} while (0)
#endif
