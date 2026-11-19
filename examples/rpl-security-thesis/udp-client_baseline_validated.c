#include "contiki.h"
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
AUTOSTART_PROCESSES(&udp_client_process);

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

      etimer_reset(&stats_timer);
    }
  }

  PROCESS_END();
}
