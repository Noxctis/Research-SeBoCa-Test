/* ctl_wrapper.c - live control values over UDP port 25000 (no Update Model needed) */
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include "ctl_wrapper.h"

#define CTL_PORT 25000
#define NVAL 16
static const char *names[NVAL] = {"cmd","target","pumpV","valveV","drainTo",
                                  "overshoot","tol","settle","zero","thickness",
                                  "lgain","lead","trimScale","react","hold","low"};
static double val[NVAL];
static int    isset[NVAL];
static int    sock = -1;
static unsigned long seq = 0;       /* counts every received command message */

int ctl_init(void)
{
    struct sockaddr_in a;
    int i, one = 1;
    for (i = 0; i < NVAL; i++) { val[i] = 0; isset[i] = 0; }
    seq = 0;
    sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock < 0) return 1;
    setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, &one, sizeof(one));
    memset(&a, 0, sizeof(a));
    a.sin_family = AF_INET;
    a.sin_addr.s_addr = htonl(INADDR_ANY);
    a.sin_port = htons(CTL_PORT);
    if (bind(sock, (struct sockaddr *)&a, sizeof(a)) < 0) { close(sock); sock = -1; return 2; }
    fcntl(sock, F_SETFL, fcntl(sock, F_GETFL, 0) | O_NONBLOCK);
    return 0;
}

static void parse(char *msg)
{
    char *save = NULL;
    char *tok = strtok_r(msg, " \t\r\n,;", &save);
    while (tok) {
        if (strcmp(tok, "clear") == 0) {
            int i;
            for (i = 0; i < NVAL; i++) isset[i] = 0;
        } else {
            char *eq = strchr(tok, '=');
            if (eq) {
                int i;
                *eq = 0;
                for (i = 0; i < NVAL; i++)
                    if (strcmp(tok, names[i]) == 0) {
                        val[i] = atof(eq + 1);
                        isset[i] = 1;
                        if (i == 0) seq++;      /* a cmd was received: re-trigger */
                    }
            }
        }
        tok = strtok_r(NULL, " \t\r\n,;", &save);
    }
}

/* def has NVAL+1 entries (the last is unused); out gets NVAL values + the message counter */
void ctl_poll(const double *def, double *out)
{
    char buf[256];
    int i;
    if (sock >= 0) {
        for (;;) {
            int n = (int)recv(sock, buf, sizeof(buf) - 1, 0);
            if (n <= 0) break;
            buf[n] = 0;
            parse(buf);
        }
    }
    for (i = 0; i < NVAL; i++) out[i] = isset[i] ? val[i] : def[i];
    out[NVAL] = (double)seq;
}

void ctl_close(void)
{
    if (sock >= 0) close(sock);
    sock = -1;
}