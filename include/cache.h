#ifndef CACHE_H
#define CACHE_H

struct CacheBlock
{
    bool dirty;
    bool valid;
    int tag;
    int cycleAdded;
    int state;   
};

class Cache
{
public:
    Cache(int blockSize, int cacheSize, int setSize);
    int read(int memAddr); //read a memory address, return cycle elapsed
    int write(int memAddr); //write to a memory address, return cycle elapsed
    void invalidate(int tag, int setIndex); //invalidate a cache block

private:
    std::vector<CacheBlock> blocks;
    int blockSize;   // cache block size
    int numBlock;    // number of cache blocks 
    int cacheSize;   // size of cache in bytes
    int setSize;     // number of cache blocks in each set
    int numSet;      // number of cache sets

    int getTagFromMemAddr(int memAddr);
    int getSetIndexFromMemAddr(int memAddr);

    //return cache index of the memory block, or -1 if block does not exist in cache
    int isBlockInCache(int tag, int setIndex);
    
    //return true if a dirty block needs to be written to memory
    bool addBlockToCache(int tag, int setIndex, int cycleAdded); 
}

#endif
