__author__ = 'bendall'

import re
from collections import defaultdict, namedtuple, Counter
from bisect import bisect_left,bisect_right

GTFRow = namedtuple('GTFRow', ['chrom','source','feature','start','end','score','strand','frame','attribute'])
# BEDRow = namedtuple('BEDRow', ['chrom','start','end','name','score','strand','strand','frame','attribute'])

class _AnnotationBisect:
    def __init__(self, gtffile, attr_name="locus"):
        self.key = attr_name

        # Instance variables
        self._locus = []                      # List of locus names
        self._locus_lookup = defaultdict(list) # {}
        self._intervals = defaultdict(list)   # Dictionary containing lists of intervals for each reference
        self._intS = {}                       # Dictionary containing lists of interval start positions for each reference
        self._intE = {}                       # Dictionary containing lists of interval end positions for each reference

        # GTF filehandle
        fh = open(gtffile,'rU') if isinstance(gtffile,str) else gtffile
        features = (GTFRow(*l.strip('\n').split('\t')) for l in fh if not l.startswith('#'))
        for i,f in enumerate(features):
            attr = dict(re.findall('(\w+)\s+"(.+?)";', f.attribute))
            _locus_name = attr[self.key] if self.key in attr else 'TELE%04d' % i
            if _locus_name not in self._locus:
                self._locus.append(_locus_name)
            # else:
            #     assert False, "Non-unique locus name found: %s" % _locus_name
            #self._locus.append( attr[attr_name] if attr_name in attr else 'PSRE%04d' % i )
            self._locus_lookup[_locus_name].append( (f.chrom, int(f.start), int(f.end)) )
            # self._intervals[f.chrom].append((int(f.start), int(f.end), i))
            self._intervals[f.chrom].append((int(f.start), int(f.end), _locus_name))

        # Sort intervals by start position
        for chrom in self._intervals.keys():
            self._intervals[chrom].sort(key=lambda x:x[0])
            self._intS[chrom] = [s for s,e,i in self._intervals[chrom]]
            self._intE[chrom] = [e for s,e,i in self._intervals[chrom]]

    def lookup(self, chrom, pos):
        ''' Return the feature for a given reference and position '''
        if chrom not in self._intervals:
            return None

        sidx = bisect_right(self._intS[chrom], pos)   # Return index of leftmost interval where start > pos
        # If the end position is inclusive (as in GTF) use bisect_left
        eidx = bisect_left(self._intE[chrom], pos)   # Return index of leftmost interval where end >= pos

        # If sidx == eidx, the position is between intervals at (sidx-1) and (sidx)
        # If eidx < sidx, the position is within eidx
        feats = [self._intervals[chrom][i] for i in range(eidx,sidx)]
        if len(feats) == 0:
            return None
        else:
            assert len(feats)==1
            return feats[0][2]

    def lookup_interval(self, chrom, spos, epos):
        ''' Resolve the feature that overlaps or contains the given interval
            NOTE: Only tests the start and end positions. This means that it does not handle
                  cases where a feature lies completely within the interval. This is OK when the
                  fragment length is expected to be smaller than the feature length.

                  Fragments where ends map to different features are resolved by
                  assigning the larger of the two overlaps.
        '''
        featL = self.lookup(chrom, spos)
        featR = self.lookup(chrom, epos)
        if featL is None and featR is None:     # Neither start nor end is within a feature
            return None
        else:
            if featL is None or featR is None:    # One (and only one) end is within a feature
                return featL if featL is not None else featR
            elif featL == featR:                  # Both ends within the same feature
                return featL
            else:                                 # Ends in different features
                locL = self._locus_lookup[featL][-1]   # Assume last fragment
                locR = self._locus_lookup[featR][0]    # Assume first fragment
                overlapL = locL[2] - spos
                overlapR = epos - locR[1]
                if overlapL >= overlapR:
                    return featL
                else:
                    return featR

    def feature_length(self):
        _ret = {}
        for chr,ilist in self._intervals.iteritems():
            for spos,epos,locus_idx in ilist:
                _ret[self._locus[locus_idx]] = epos-spos
        return _ret

    def feature_name(self,id):
        return self._locus[id]

def overlapsize(a,b):
    return max(0, min(a.end,b.end) - max(a.begin,b.begin))

class _AnnotationIntervalTree:
    # GTFRow = namedtuple('GTFRow', ['chrom','source','feature','start','end','score','strand','frame','attribute'])

    def __init__(self, gtffile, attr_name="locus"):
        self.key   = attr_name
        self.itree = defaultdict(IntervalTree)

        # GTF filehandle
        fh = open(gtffile,'rU') if isinstance(gtffile,str) else gtffile
        features = (GTFRow(*l.strip('\n').split('\t')) for l in fh if not l.startswith('#'))
        for f in features:
            attr = dict(re.findall('(\w+)\s+"(.+?)";', f.attribute))
            self.itree[f.chrom][int(f.start):int(f.end)] = attr

    def lookup(self, ref, pos, get_index=False):
        return set( iv.data[self.key] for iv in self.itree[ref][pos] )

    def lookup_interval(self, ref, spos, epos):
        query = Interval(spos,epos)
        possible = self.itree[ref][query]
        if not possible:
            return None
        if len(possible)==1:
            return possible.pop().data[self.key]
        else:
            overlaps = Counter()
            for p in possible:
                overlaps[p.data[self.key]] += overlapsize(p,query)
            return overlaps.most_common()[0][0]

    def feature_length(self):
        raise NotImplementedError("feature_length() has not been implemented for AnnotationIntervalTree")

    def feature_name(self):
        raise NotImplementedError("feature_name() has not been implemented for AnnotationIntervalTree")



ANNOTATION_CLASS='bisect'

# Import Annotation class based on ANNOTATION_CLASS
if ANNOTATION_CLASS == 'bisect':
    Annotation = _AnnotationBisect
elif ANNOTATION_CLASS == 'intervaltree':
    from intervaltree import Interval, IntervalTree
    Annotation = _AnnotationIntervalTree
else:
    raise ImportError('Could not import Annotation "%s"' % ANNOTATION_CLASS)
