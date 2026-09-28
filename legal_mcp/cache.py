"""Yalnız resmî kaynak sorguları/metinleri; olay ve model cevabı saklanmaz."""
import time,threading,copy
from collections import OrderedDict

class MemoryCache:
    def __init__(self,ttl=300,max_entries=256):
        self.ttl=ttl;self.max_entries=max_entries;self.entries=OrderedDict();self.lock=threading.RLock()
    def get(self,key):
        with self.lock:
            row=self.entries.get(key)
            if row and row[0]>time.monotonic():
                self.entries.move_to_end(key);return copy.deepcopy(row[1])
            self.entries.pop(key,None);return None
    def put(self,key,value):
        with self.lock:
            self.entries[key]=(time.monotonic()+self.ttl,copy.deepcopy(value));self.entries.move_to_end(key)
            while len(self.entries)>self.max_entries:self.entries.popitem(last=False)
    def clear(self):
        with self.lock:self.entries.clear()

SOURCE_CACHE=MemoryCache()
