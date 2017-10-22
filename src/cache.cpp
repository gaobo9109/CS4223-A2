#include "cache.h"

Cache::Cache(int cacheSize, int blockSize, int associativity)
{
    nBlock = cacheSize / blockSize;
    nSet = nBlock / associativity;
    setSize = associativity;
    blocks.resize(nSet);

    //initialize cache
    for(int i=0; i<nSet; i++)
    {
        std::list<CacheBlock> set;
        blocks.push_pack(set);
    }
}

//check if block in cache, move the block to the front of the list if present
bool Cache::contain(int setIndex, int tag)
{
    std::list<CacheBlock>& set = blocks[setIndex];

    bool found = false;
    std::list<CacheBlock>::iterator it;
    for(it = set.begin(); it!= set.end(); ++it)
    {
        if(it->tag == tag && it->valid)
        {
            found = true;
            break;
        }
    }

    if(found)
    {
        //move the matched block to the front of the list
        set.splice(set.begin(), set, it);
    }

    return found;
}

// assume block not in cache
// return true if need to write dirty block to memory
bool Cache::insert(int setIndex, int tag)
{
    std::list<CacheBlock>& set = blocks[setIndex];
    CacheBlock block = {false, true, tag, 0};
    bool writeBack = false;

    if(set.size() < setSize)
    {
        set.push_front(block);
    }
    else
    {
        writeBack = set.end()->valid && set.end()->dirty;
        set.pop_back();
        set.push_front(block);
    }
    
    return writeBack;
}

// assume block in cache and at front of the list 
void Cache::modify(int setIndex)
{
    blocks[setIndex].begin()->dirty = true;
}

// assume block in cache and at front of the list
void Cache::invalidate(int setIndex)
{
    std::list<CacheBlock>& set = blocks[setIndex];
    set.begin()->valid = false;
    // move block to the end of the list to be evicted next
    set.splice(set.end(), set, set.begin());
}

void Cache::setState(int setIndex, int state)
{
    blocks[setIndex].begin()->state = state;
}

int Cache::getState(int setIndex)
{
    return blocks[setIndex].begin()->state;
}


