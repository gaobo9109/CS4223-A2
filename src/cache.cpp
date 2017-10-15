#include "cache.h"

Cache::Cache(int blockSize_, int cacheSize_, int setSize_):
    blockSize(blockSize_),
    cacheSize(cacheSize_),
    setSize(setSize_)
{
    numBlock = cacheSize / blockSize;
    numSet = numBlock / setSize;

    for(int i=0; i<numBlock; i++)
    {
        blocks.push_back({false,false,0,0,0});
    }

}


void Cache::invalidate(int tag, int setIndex)
{
    int cacheIndex = isBlockInCache(tag, setIndex);
    blocks[cacheIndex].valid = false;
}

int Cache::getTagFromMemAddr(int memAddr)
{
    int blockIndex = memAddr / blockSize;
    return blockIndex / numSet;
}

int Cache::getSetIndexFromMemAddr(int memAddr)
{
    int blockIndex = memAddr / blockSize;
    return blockIndex % numSet;
}

int Cache::isBlockInCache(int tag, int setIndex)
{
    int hitIndex = -1;

    //check through all cache blocks in set
    for(int i=0; i<setSize; i++)
    {
        int cacheIndex = setIndex + i * numSet;
        if(blocks[cacheIndex].valid && blocks[cacheIndex].tag == tag)
           hitIndex = cacheIndex;
    }
    return hitIndex;
}

bool addBlockToCache(int tag, int setIndex, int cycleAdded)
{
    int earliestCycleAdded = blocks[setIndex].cycleAdded;
    int blockChosen = setIndex;
    bool evict = true;

    for(int i=0; i<setSize; i++)
    {
        int cacheIndex = setIndex + i * numSet;
        // find the first available slot in the set
        if(!blocks[cacheIndex].valid)
        {
            blocks[cacheIndex].tag = tag;
            blocks[cacheIndex].valid = true;
            blocks[cacheIndex].dirty = false;
            blocks[cacheIndex].cycleAdded = cycle;
            evict = false;
            break;
        }

        else
        {
            // find the earliest added block to evict
            if(blocks[cacheIndex].cycleAdded < earliestCycle)
            {
                earliestCycleAdded = blocks[cacheIndex].cycleAdded;
                blockChosen = cacheIndex; 
            }
        }

    }

    bool writeBack = false;

    if(evict)
    {
        if(blocks[blockChosen].dirty)
            writeBack = true;

        blocks[blockChosen].dirty = false;
        blocks[blockChosen].valid = true;
        blocks[blockChosen].tag = tag;
        blocks[blockChosen].cycleAdded = cycle;
    }

    return writeBack;
}
