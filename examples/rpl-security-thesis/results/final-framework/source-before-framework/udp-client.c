#include "contiki.h"
#include "sys/ctimer.h"
#include "project-conf.h"
#include "net/routing/rpl-lite/rpl.h"
#include "net/routing/rpl-lite/rpl-icmp6.h"
#include "net/routing/routing.h"
#include "random.h"
#include "net/netstack.h"
#include "net/ipv6/simple-udp.h"
#include "net/linkaddr.h"
#include "sys/energest.h"
#include "rpl-metrics.h"

#include <stdint.h>
#include <inttypes.h>
#include <stdio.h>
#include <string.h>

#include "sys/log.h"

#define LOG_MODULE "App"
#define LOG_LEVEL LOG_LEVEL_INFO

#define UDP_CLIENT_PORT 8765
#define UDP_SERVER_PORT 5678

#define SEND_INTERVAL  (10 * CLOCK_SECOND)
#define STATS_INTERVAL (30 * CLOCK_SECOND)

static struct simple_udp_connection udp_conn;

static uint32_t tx_count = 0;
static uint32_t rx_count = 0;
static uint32_t unreachable_count = 0;

static unsigned int
get_node_id(void)
{
  return (unsigned int)linkaddr_node_addr.u8[LINKADDR_SIZE - 1];
}

static unsigned long
simulation_time_seconds(void)
{
  return (unsigned long)(clock_time() / CLOCK_SECOND);
}

static void
print_energy_stats(void)
{
  energest_flush();

  printf(
    "ENERGY,time=%lu,node=%u,cpu=%" PRIu64
    ",lpm=%" PRIu64
    ",tx=%" PRIu64
    ",rx=%" PRIu64 "\n",
    simulation_time_seconds(),
    get_node_id(),
    (uint64_t)energest_type_time(ENERGEST_TYPE_CPU),
    (uint64_t)energest_type_time(ENERGEST_TYPE_LPM),
    (uint64_t)energest_type_time(ENERGEST_TYPE_TRANSMIT),
    (uint64_t)energest_type_time(ENERGEST_TYPE_LISTEN)
  );
}

PROCESS(udp_client_process, "RPL thesis UDP client");

/* THESIS_DIS_FLOOD_PROCESS_IMPLEMENTED */
PROCESS(thesis_dis_flood_process, "Thesis controlled DIS flood process");
AUTOSTART_PROCESSES(&udp_client_process, &thesis_dis_flood_process);

static void
udp_rx_callback(struct simple_udp_connection *c,
                const uip_ipaddr_t *sender_addr,
                uint16_t sender_port,
                const uip_ipaddr_t *receiver_addr,
                uint16_t receiver_port,
                const uint8_t *data,
                uint16_t datalen)
{
  rx_count++;

  printf(
    "RX,time=%lu,node=%u,rx_total=%" PRIu32
    ",payload=%.*s\n",
    simulation_time_seconds(),
    get_node_id(),
    rx_count,
    datalen,
    (const char *)data
  );
}

PROCESS_THREAD(udp_client_process, ev, data)
{
  static struct etimer send_timer;
  static struct etimer stats_timer;
  static char payload[64];
  uip_ipaddr_t dest_ipaddr;

  PROCESS_BEGIN();

  printf(
    "CLIENT_START,time=%lu,node=%u\n",
    simulation_time_seconds(),
    get_node_id()
  );

  simple_udp_register(
    &udp_conn,
    UDP_CLIENT_PORT,
    NULL,
    UDP_SERVER_PORT,
    udp_rx_callback
  );

  etimer_set(&send_timer, random_rand() % SEND_INTERVAL);
  etimer_set(&stats_timer, STATS_INTERVAL);

  while(1) {

    PROCESS_WAIT_EVENT();

    if(etimer_expired(&send_timer)) {

      if(NETSTACK_ROUTING.node_is_reachable() &&
         NETSTACK_ROUTING.get_root_ipaddr(&dest_ipaddr)) {

        tx_count++;

        snprintf(
          payload,
          sizeof(payload),
          "node=%u,seq=%" PRIu32,
          get_node_id(),
          tx_count
        );

        printf(
          "TX,time=%lu,node=%u,seq=%" PRIu32
          ",tx_total=%" PRIu32 "\n",
          simulation_time_seconds(),
          get_node_id(),
          tx_count,
          tx_count
        );

        simple_udp_sendto(
          &udp_conn,
          payload,
          strlen(payload),
          &dest_ipaddr
        );

      } else {

        unreachable_count++;

        printf(
          "UNREACHABLE,time=%lu,node=%u,count=%" PRIu32 "\n",
          simulation_time_seconds(),
          get_node_id(),
          unreachable_count
        );
      }

      etimer_set(
        &send_timer,
        SEND_INTERVAL
        - CLOCK_SECOND
        + (random_rand() % (2 * CLOCK_SECOND))
      );
    }

    if(etimer_expired(&stats_timer)) {

      printf(
        "STATS,time=%lu,node=%u,tx=%" PRIu32
        ",rx=%" PRIu32
        ",unreachable=%" PRIu32 "\n",
        simulation_time_seconds(),
        get_node_id(),
        tx_count,
        rx_count,
        unreachable_count
      );

      print_energy_stats();
      thesis_print_rpl_state();
      thesis_print_rpl_control_stats();
      thesis_print_forward_stats();

      etimer_reset(&stats_timer);
    }
  }

  PROCESS_END();
}


/*---------------------------------------------------------------------------*/
/*
 * Controlled thesis DIS-flood experiment.
 *
 * Normal RPL convergence is allowed for 120 seconds.
 * Only THESIS_DIS_FLOOD_NODE_ID generates the burst.
 * All other motes simply keep this process dormant.
 */
/*---------------------------------------------------------------------------*/
/*
 * Controlled DIS flooding using Contiki callback timers.
 *
 * This avoids relying on a second process waiting on an etimer.
 * The callback is armed by the process and executed by Contiki's
 * ctimer infrastructure after the 120-second convergence period.
 */

static struct ctimer thesis_dis_flood_timer;
static uint8_t thesis_dis_flood_started = 0;

/*---------------------------------------------------------------------------*/
static void
thesis_dis_flood_callback(void *ptr)
{
  unsigned int thesis_node_id;
  unsigned int i;

  thesis_node_id =
    (unsigned int)linkaddr_node_addr.u8[LINKADDR_SIZE - 1];

  if(!THESIS_DIS_FLOOD_ATTACK ||
     thesis_node_id != THESIS_DIS_FLOOD_NODE_ID) {
    return;
  }

  if(!thesis_dis_flood_started) {
    thesis_dis_flood_started = 1;

    printf(
      "DIS_FLOOD_START,time=%lu,node=%u,burst=%u\n",
      (unsigned long)(clock_time() / CLOCK_SECOND),
      thesis_node_id,
      (unsigned int)THESIS_DIS_FLOOD_BURST
    );
  }

  for(i = 0; i < THESIS_DIS_FLOOD_BURST; i++) {
    rpl_icmp6_dis_output(NULL);
  }

  printf(
    "DIS_FLOOD_BURST,time=%lu,node=%u,count=%u\n",
    (unsigned long)(clock_time() / CLOCK_SECOND),
    thesis_node_id,
    (unsigned int)THESIS_DIS_FLOOD_BURST
  );

  /*
   * Continue one burst every ten seconds.
   */
  ctimer_set(
    &thesis_dis_flood_timer,
    10 * CLOCK_SECOND,
    thesis_dis_flood_callback,
    NULL
  );
}
/*---------------------------------------------------------------------------*/

PROCESS_THREAD(thesis_dis_flood_process, ev, data)
{
  unsigned int thesis_node_id;

  PROCESS_BEGIN();

  thesis_node_id =
    (unsigned int)linkaddr_node_addr.u8[LINKADDR_SIZE - 1];

  printf(
    "DIS_PROCESS_BOOT,time=%lu,node=%u,enabled=%u,target=%u\n",
    (unsigned long)(clock_time() / CLOCK_SECOND),
    thesis_node_id,
    (unsigned int)THESIS_DIS_FLOOD_ATTACK,
    (unsigned int)THESIS_DIS_FLOOD_NODE_ID
  );

  if(THESIS_DIS_FLOOD_ATTACK &&
     thesis_node_id == THESIS_DIS_FLOOD_NODE_ID) {

    printf(
      "DIS_FLOOD_ARMED,time=%lu,node=%u,start_after=120\n",
      (unsigned long)(clock_time() / CLOCK_SECOND),
      thesis_node_id
    );

    ctimer_set(
      &thesis_dis_flood_timer,
      120 * CLOCK_SECOND,
      thesis_dis_flood_callback,
      NULL
    );
  }

  PROCESS_END();
}
/*---------------------------------------------------------------------------*/
