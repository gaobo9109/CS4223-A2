#include "processor.h"
#include <fstreami>
#include <iomanip>

Processor::Processor(std::string traceFile, int cacheSize, int associativity, int blockSize):
    cache(blockSize_, cacheSize_, associativity_)
{
    instructions = readTraceFile(traceFile);
    currentCycle = 0;
    cycleTillUnblocked = 0;

}

void Processor::readTraceFile(std::string traceFile)
{
   std::ifstream file(traceFile);
   int label, value;

   while(file >> std::setbase(0) >> label >> value)
   {
        instructions.push_back(std::make_pair(label,value);
   }
}

void Processor::tick()
{
    if(currentCycle == cycleTillUnblocked)
    {
        executeInstr();
    }

    currentCycle ++; 
}

int Processor::executeInstr()
{
    int label = instructions[instrCount].first;
    int value = instructions[instrCount].second;
    int cycleElapsed; 

    switch(label)
    {
        case 0: cycleElapsed = load(value);
        case 1: cycleElapsed = store(value);
        case 2: cycleElapsed = compute(value);
    }

    instrCount ++;
    cycleTillUnblocked = currentCycle + cycleElapsed; 
}

void Processor::load(int memAddr)
{

}

void Processor::store(int memAddr)
{

}

void Processor::compute(int cycles)
{

}
