#ifndef CTL_WRAPPER_H
#define CTL_WRAPPER_H
#ifdef __cplusplus
extern "C" {
#endif
int  ctl_init(void);
void ctl_poll(const double *def, double *out);
void ctl_close(void);
#ifdef __cplusplus
}
#endif
#endif