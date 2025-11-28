// Техномир: конфигурация Hazelcast кластера
Config config = new Config();
config.setClusterName("technomir-cache");

// Настройка сети
config.getNetworkConfig()
    .setPort(5701)
    .setPortAutoIncrement(true)
    .getJoin()
    .getMulticastConfig()
    .setEnabled(false)  // Отключаем multicast
    .getTcpIpConfig()
    .setEnabled(true)
    .addMember("10.0.0.1,10.0.0.2,10.0.0.3");  // Явный список узлов

HazelcastInstance hz = Hazelcast.newHazelcastInstance(config);