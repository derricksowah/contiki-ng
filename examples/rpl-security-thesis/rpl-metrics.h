#ifndef RPL_METRICS_H_
#define RPL_METRICS_H_

#include <stdint.h>

uint32_t thesis_parent_switch_count(void);
void thesis_print_rpl_state(void);
void thesis_print_rpl_control_stats(void);

void thesis_count_dis_in(void);
void thesis_count_dis_out(void);

void thesis_count_dio_in(void);
void thesis_count_dio_out(void);

void thesis_count_dao_in(void);
void thesis_count_dao_out(void);

void thesis_count_forward_in(void);
void thesis_count_forward_out(void);
void thesis_count_forward_drop(void);
void thesis_print_forward_stats(void);


#endif
