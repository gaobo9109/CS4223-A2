#ifndef PROCESSOR_H
#define PROCESSOR_H

#include "cache.h"

class Processor
{
public:
    Processor(std::string instruction_file, int blockSize, int cacheSize, int associativity);
    void load(int memAddr);
    void store(int memAddr);
    void compute(int cycles);


private:
    Cache cache;
    int blockSize;
    std::vector<std::pair<int, int>> instructions
    int currentCycle;
    int cycleTillUnblocked;
    int instrCount;
}



#endif
