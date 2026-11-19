#include "contiki.h"
#include "net/routing/routing.h"
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

#define STATS_INTERVAL (30 * CLOCK_SECOND)

static struct simple_udp_connection udp_conn;

static uint32_t total_rx = 0;
static uint32_t total_replies = 0;

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

PROCESS(udp_server_process, "RPL thesis UDP server");
AUTOSTART_PROCESSES(&udp_server_process);

static void
udp_rx_callback(struct simple_udp_connection *c,
                const uip_ipaddr_t *sender_addr,
                uint16_t sender_port,
                const uip_ipaddr_t *receiver_addr,
                uint16_t receiver_port,
                const uint8_t *data,
                uint16_t datalen)
{
  total_rx++;

  printf(
    "SERVER_RX,time=%lu,node=%u,total_rx=%" PRIu32
    ",payload=%.*s\n",
    simulation_time_seconds(),
    get_node_id(),
    total_rx,
    datalen,
    (const char *)data
  );

  simple_udp_sendto(
    &udp_conn,
    data,
    datalen,
    sender_addr
  );

  total_replies++;

  printf(
    "SERVER_REPLY,time=%lu,node=%u,total_replies=%" PRIu32 "\n",
    simulation_time_seconds(),
    get_node_id(),
    total_replies
  );
}

PROCESS_THREAD(udp_server_process, ev, data)
{
  static struct etimer stats_timer;

  PROCESS_BEGIN();

  printf(
    "ROOT_START,time=%lu,node=%u\n",
    simulation_time_seconds(),
    get_node_id()
  );

  NETSTACK_ROUTING.root_start();

  simple_udp_register(
    &udp_conn,
    UDP_SERVER_PORT,
    NULL,
    UDP_CLIENT_PORT,
    udp_rx_callback
  );

  etimer_set(&stats_timer, STATS_INTERVAL);

  while(1) {

    PROCESS_WAIT_EVENT_UNTIL(etimer_expired(&stats_timer));

    printf(
      "ROOT_STATS,time=%lu,node=%u,total_rx=%" PRIu32
      ",total_replies=%" PRIu32 "\n",
      simulation_time_seconds(),
      get_node_id(),
      total_rx,
      total_replies
    );

    print_energy_stats();
    thesis_print_rpl_state();
    thesis_print_rpl_control_stats();

    etimer_reset(&stats_timer);
  }

  PROCESS_END();
}
