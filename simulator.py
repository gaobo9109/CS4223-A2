from processor import Processor
from mesi import MESICache
from dragon import DragonCache
from shared_line import SharedLine


class Simulator:
    def __init__(self, protocol, input_file, cache_size, associativity, block_size):
        if protocol == 'MESI':
            self.caches = [MESICache(cache_size, associativity, block_size, i) for i in range(4)]
        elif protocol == 'DRAGON':
            self.caches = [DragonCache(cache_size, associativity, block_size, i) for i in range(4)]

        self.processors = [Processor(input_file, i, self.caches[i]) for i in range(4)]
        self.shared_line = SharedLine()
        for cache in self.caches:
            cache.set_shared_line(self.shared_line)

        
    def run():
        done = [False for i in range(4)]

        while not all(done):
            for p in self.processors:
                if done[p.pid]: 
                    continue

                res = p.tick()
                if res is None:
                    if p.finished:
                        done[p.pid] = True
                    continue

                label, value = res
                cache = p.cache

                if label == OTHER:
                    p.compute_for(value)
                    continue

                if label == LOAD:
                    action = 'r'

                elif label == STORE:
                    action = 'w'

                if not bus.is_blocked():
                    bus_txn, cycles = cache.processor_action(action, value)


                

