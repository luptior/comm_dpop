from datetime import datetime as dt


def value_msg_prop(agent):
    # print(dt.now(), str(agent.id) + ': Begin value_msg_prop')
    agent.logger.info(f"{dt.now()}, {str(agent.id)} + : Begin value_msg_prop")

    # Wait till value_msg from parent has arrived.
    while True:
        if ('value_msg_' + str(agent.p)) in agent.msgs:
            break

    D = agent.msgs['value_msg_' + str(agent.p)]

    index = []
    for nodeid in agent.table_ant:
        index.append(D[nodeid])
    index = tuple(index)
    agent.value = agent.table[index]

    # Send the index of assigned value
    ind = agent.domain.index(agent.value)
    D[agent.id] = ind
    for child in agent.c:
        agent.send('value_msg_' + str(agent.id), D, child)

    agent.logger.info(f"{dt.now()}, {str(agent.id)} + : End value_msg_prop")
