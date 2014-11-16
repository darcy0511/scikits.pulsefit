
import numpy as np
import blockident_median_c
from block import Block

class BlockIdentMedian(object):
    """BlockIdentMedian identifies blocks by using a fast moving-median
    filter to establish a baseline, and a threshold value (measured
    from the baseline) to identify blocks that may contain pulses.
    """
    def __init__(self, r, p, th, filt_len, pad_pre, pad_post, max_len,
                 exclude_pre=None, exclude_post=None, debug=False):
        """Arguments:
        r            -- The residual data.
        p            -- The pulse shape.
        th           -- Threshold value for the smallest pulse.
        filt_len     -- The number of samples in the median filter.
        pad_pre      -- The number of padding samples included in the
        pad_post     -- block, before and after the pulses.
        max_len      -- The maximum length of a block.
        exclude_pre  -- Exclude pulses from beginning of block.
        exclude_post -- Exclude pulses from the end of the block.
        """
        self.r = r
        self.p = p
        self.th = float(th)
        self.filt_len = int(filt_len)
        self.pad_pre = int(pad_pre)
        self.pad_post = int(pad_post)
        self.max_len = int(max_len)
        self.exclude_pre = pad_pre if exclude_pre is None else exclude_pre
        self.exclude_post = pad_post if exclude_post is None else exclude_post
        
        self.idx = filt_len # The current position in r.

        
    def next_block(self):
        """Get the next block for fitting. Returns None when the end 
        of the data is reached.
        """
        # Call the C function that will do the actual search. 
        return_inds = np.zeros(2, dtype=np.int64)
        b = blockident_median_c.next_block(
            self.idx, 
            self.filt_len, 
            self.pad_post,
            self.max_len,
            self.th,
            self.r,
            return_inds)
        i0, i1 = return_inds
        
        # If the first index is the length of the block, we're at the end. 
        if i0 == self.r.size:
            return None

        # Construct new block.
        block = Block(self.r, self.p,
                      max(i0 - self.pad_pre, 0),
                      min(i1 + self.pad_post, self.r.size - 1),
                      b)

        block.exclude_pre = self.exclude_pre
        block.exclude_post = self.exclude_post
        
        # Update current index. 
        self.idx = block.i1 - max(self.pad_post, self.filt_len)
        
        return block

        
    def set_position(self, index):
        self.idx = max(index, self.filt_len)