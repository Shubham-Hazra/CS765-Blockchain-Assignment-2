import simpy as sp


def create_blk(env):
    yield env.timeout(1)
    print("Block Created")
    print(env.now)

def create_txn(env):
    yield env.timeout(1)
    print("Transaction Created")
    print(env.now)

def main():
    env = sp.Environment()
    while True:
        env.process(create_blk(env))
        env.process(create_txn(env))
        env.run(until=20)


if __name__ == '__main__':
    main()