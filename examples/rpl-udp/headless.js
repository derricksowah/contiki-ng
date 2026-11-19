TIMEOUT(300000, log.testOK());

while(true) {
    YIELD();
    log.log(time + " ID:" + id + " " + msg + "\n");
}
