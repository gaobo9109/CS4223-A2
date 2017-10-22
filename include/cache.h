#ifndef CACHE_H
#define CACHE_H

struct CacheBlock
{
    bool dirty;
    bool valid;
    int tag;
    int state;
};

class Cache
{
public:
    Cache(int cacheSize, int blockSize, int associativity);
    bool contain(int setIndex, int tag);
    bool insert(int setIndex, int tag);
    void modify(int setIndex);
    void invalidate(int setIndex);
    void setState(int setIndex, int state);
    int getState(setIndex);
        
private:
    std::vector<std::list<CacheBlock>> blocks;
    int nBlock;
    int nSet;
    int setSize;
}

#endif
