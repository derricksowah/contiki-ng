#include "contiki.h"
#include "project-conf.h"
#include "net/linkaddr.h"
#include "thesis-security.h"

#include <stdint.h>
#include <stdio.h>

#ifndef THESIS_SECURITY_FRAMEWORK
#define THESIS_SECURITY_FRAMEWORK 0
#endif

#if THESIS_SECURITY_FRAMEWORK

#if THESIS_SECURITY_FRAMEWORK

static uint32_t violations[6];
static uint8_t detected[6];
static uint8_t mitigated[6];
static uint8_t recovered[6];

static uint32_t detection_time[6];
static uint32_t mitigation_time[6];

static unsigned int
local_node_id(void)
{
  return
    (unsigned int)
    linkaddr_node_addr.u8[LINKADDR_SIZE - 1];
}

static const char *
attack_name(uint8_t attack)
{
  switch(attack) {
  case THESIS_ATTACK_BLACKHOLE:
    return "BLACKHOLE";

  case THESIS_ATTACK_GRAYHOLE:
    return "GRAYHOLE";

  case THESIS_ATTACK_DECREASED_RANK:
    return "DECREASED_RANK";

  case THESIS_ATTACK_DODAG_VERSION:
    return "DODAG_VERSION";

  case THESIS_ATTACK_DIS_FLOOD:
    return "DIS_FLOOD";

  default:
    return "UNKNOWN";
  }
}

static uint32_t
threshold(uint8_t attack)
{
  switch(attack) {

  /*
   * Forwarding attacks require repeated evidence.
   */
  case THESIS_ATTACK_BLACKHOLE:
    return 3;

  case THESIS_ATTACK_GRAYHOLE:
    return 3;

  /*
   * These are protocol invariant violations.
   */
  case THESIS_ATTACK_DECREASED_RANK:
    return 1;

  case THESIS_ATTACK_DODAG_VERSION:
    return 1;

  /*
   * Baseline steady-state DIS rate was zero.
   * Allow two events before enforcement.
   */
  case THESIS_ATTACK_DIS_FLOOD:
    return 3;

  default:
    return 1;
  }
}

#endif /* THESIS_SECURITY_FRAMEWORK */

#endif /* THESIS_SECURITY_FRAMEWORK */

void
thesis_security_violation(
  uint8_t attack,
  uint8_t attacker,
  const char *rule
)
{
#if THESIS_SECURITY_FRAMEWORK

  uint32_t now;

  if(attack == 0 || attack > 5) {
    return;
  }

  /*
   * Ignore network convergence.
   */
  if(clock_time() < 120 * CLOCK_SECOND) {
    return;
  }

  now =
    (uint32_t)(clock_time() / CLOCK_SECOND);

  violations[attack]++;

  printf(
    "SECURITY_EVIDENCE,time=%lu,observer=%u,"
    "attacker=%u,attack=%s,rule=%s,count=%lu\n",
    (unsigned long)now,
    local_node_id(),
    attacker,
    attack_name(attack),
    rule,
    (unsigned long)violations[attack]
  );

  if(!detected[attack] &&
     violations[attack] >= threshold(attack)) {

    detected[attack] = 1;
    detection_time[attack] = now;

    printf(
      "DETECTION,time=%lu,observer=%u,"
      "attacker=%u,attack=%s,rule=%s,"
      "evidence_count=%lu\n",
      (unsigned long)now,
      local_node_id(),
      attacker,
      attack_name(attack),
      rule,
      (unsigned long)violations[attack]
    );
  }

  if(detected[attack] &&
     !mitigated[attack]) {

    mitigated[attack] = 1;
    mitigation_time[attack] = now;

    printf(
      "MITIGATION,time=%lu,observer=%u,"
      "attacker=%u,attack=%s,"
      "action=ISOLATE_OR_SUPPRESS\n",
      (unsigned long)now,
      local_node_id(),
      attacker,
      attack_name(attack)
    );
  }

#else
  (void)attack;
  (void)attacker;
  (void)rule;
#endif
}


int
thesis_security_is_mitigated(
  uint8_t attack
)
{
#if THESIS_SECURITY_FRAMEWORK

  if(attack == 0 || attack > 5) {
    return 0;
  }

  return mitigated[attack];

#else
  (void)attack;
  return 0;
#endif
}


void
thesis_security_recovery(
  uint8_t attack,
  uint8_t attacker,
  const char *evidence
)
{
#if THESIS_SECURITY_FRAMEWORK

  uint32_t now;
  uint32_t recovery;

  if(attack == 0 || attack > 5) {
    return;
  }

  if(!mitigated[attack] ||
     recovered[attack]) {
    return;
  }

  now =
    (uint32_t)(clock_time() / CLOCK_SECOND);

  if(now >= mitigation_time[attack]) {
    recovery =
      now - mitigation_time[attack];
  } else {
    recovery = 0;
  }

  recovered[attack] = 1;

  printf(
    "RECOVERY,time=%lu,observer=%u,"
    "attacker=%u,attack=%s,"
    "evidence=%s,recovery_s=%lu\n",
    (unsigned long)now,
    local_node_id(),
    attacker,
    attack_name(attack),
    evidence,
    (unsigned long)recovery
  );

#else
  (void)attack;
  (void)attacker;
  (void)evidence;
#endif
}
