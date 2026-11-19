#include "contiki.h"

#include "net/linkaddr.h"
#include "net/link-stats.h"

#include "net/routing/rpl-lite/rpl.h"
#include "net/routing/rpl-lite/rpl-neighbor.h"

#include "rpl-metrics.h"

#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>

static uint32_t parent_switches = 0;

static uint32_t dis_in_count = 0;
static uint32_t dis_out_count = 0;

static uint32_t dio_in_count = 0;
static uint32_t dio_out_count = 0;

static uint32_t dao_in_count = 0;
static uint32_t dao_out_count = 0;

/*---------------------------------------------------------------------------*/
static unsigned int
get_node_id(void)
{
  return (unsigned int)linkaddr_node_addr.u8[LINKADDR_SIZE - 1];
}
/*---------------------------------------------------------------------------*/
static unsigned long
simulation_time_seconds(void)
{
  return (unsigned long)(clock_time() / CLOCK_SECOND);
}
/*---------------------------------------------------------------------------*/
void
thesis_parent_switch(rpl_nbr_t *old_parent, rpl_nbr_t *new_parent)
{
  /*
   * Initial attachment NULL -> parent is not counted as a switch.
   * Only changes between two established parents are counted.
   */
  if(old_parent != NULL &&
     new_parent != NULL &&
     old_parent != new_parent) {
    parent_switches++;

    printf(
      "PARENT_SWITCH,time=%lu,node=%u,count=%" PRIu32 "\n",
      simulation_time_seconds(),
      get_node_id(),
      parent_switches
    );
  }
}
/*---------------------------------------------------------------------------*/
uint32_t
thesis_parent_switch_count(void)
{
  return parent_switches;
}

/*---------------------------------------------------------------------------*/
void
thesis_count_dis_in(void)
{
  dis_in_count++;
}
/*---------------------------------------------------------------------------*/
void
thesis_count_dis_out(void)
{
  dis_out_count++;
}
/*---------------------------------------------------------------------------*/
void
thesis_count_dio_in(void)
{
  dio_in_count++;
}
/*---------------------------------------------------------------------------*/
void
thesis_count_dio_out(void)
{
  dio_out_count++;
}
/*---------------------------------------------------------------------------*/
void
thesis_count_dao_in(void)
{
  dao_in_count++;
}
/*---------------------------------------------------------------------------*/
void
thesis_count_dao_out(void)
{
  dao_out_count++;
}
/*---------------------------------------------------------------------------*/
void
thesis_print_rpl_control_stats(void)
{
  printf(
    "RPL_CTRL,time=%lu,node=%u,"
    "dis_in=%" PRIu32 ",dis_out=%" PRIu32 ","
    "dio_in=%" PRIu32 ",dio_out=%" PRIu32 ","
    "dao_in=%" PRIu32 ",dao_out=%" PRIu32 "\n",
    simulation_time_seconds(),
    get_node_id(),
    dis_in_count,
    dis_out_count,
    dio_in_count,
    dio_out_count,
    dao_in_count,
    dao_out_count
  );
}
/*---------------------------------------------------------------------------*/
void
thesis_print_rpl_state(void)
{
  rpl_dag_t *dag;
  rpl_nbr_t *parent;
  const linkaddr_t *parent_lladdr;
  const struct link_stats *stats;

  unsigned int parent_id = 0;
  uint16_t etx = 0;
  uint8_t etx_valid = 0;

  dag = rpl_get_any_dag();

  if(dag == NULL) {
    printf(
      "RPL_STATE,time=%lu,node=%u,joined=0,rank=65535,"
      "parent=0,version=0,etx=0,etx_valid=0,"
      "parent_changes=%" PRIu32 "\n",
      simulation_time_seconds(),
      get_node_id(),
      parent_switches
    );
    return;
  }

  parent = dag->preferred_parent;

  if(parent != NULL) {
    parent_lladdr = rpl_neighbor_get_lladdr(parent);

    if(parent_lladdr != NULL) {
      parent_id =
        (unsigned int)parent_lladdr->u8[LINKADDR_SIZE - 1];

      stats = link_stats_from_lladdr(parent_lladdr);

      if(stats != NULL) {
        etx = stats->etx;
        etx_valid = link_stats_is_fresh(stats) ? 1 : 0;
      }
    }
  }

  printf(
    "RPL_STATE,time=%lu,node=%u,joined=%u,"
    "rank=%u,parent=%u,version=%u,"
    "etx=%u,etx_divisor=%u,etx_valid=%u,"
    "parent_changes=%" PRIu32 "\n",
    simulation_time_seconds(),
    get_node_id(),
    dag->rank != 0xffff ? 1 : 0,
    (unsigned int)dag->rank,
    parent_id,
    (unsigned int)dag->version,
    (unsigned int)etx,
    (unsigned int)LINK_STATS_ETX_DIVISOR,
    etx_valid,
    parent_switches
  );
}
/*---------------------------------------------------------------------------*/
