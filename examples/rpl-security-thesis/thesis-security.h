#ifndef THESIS_SECURITY_H_
#define THESIS_SECURITY_H_

#include <stdint.h>

#define THESIS_ATTACK_BLACKHOLE       1
#define THESIS_ATTACK_GRAYHOLE        2
#define THESIS_ATTACK_DECREASED_RANK  3
#define THESIS_ATTACK_DODAG_VERSION   4
#define THESIS_ATTACK_DIS_FLOOD       5

void thesis_security_violation(
  uint8_t attack,
  uint8_t attacker,
  const char *rule
);

int thesis_security_is_mitigated(
  uint8_t attack
);

void thesis_security_recovery(
  uint8_t attack,
  uint8_t attacker,
  const char *evidence
);

#endif
