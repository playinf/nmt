# bleu.py
# code modified from nltk.align.bleu
# author: Playinf
# email: playinf@stu.xmu.edu.cn

import math
import numpy
from collections import Counter

def count_ngrams(seq, n):
    counts = {}
    length = len(seq)

    for i in range(length):
        if i + n <= length:
            ngram = ' '.join(seq[i:i + n])
            if ngram not in counts:
                counts[ngram] = 0
            counts[ngram] += 1

    return counts

def closest_length(candidate, references):
    clen = len(candidate)
    closest_diff = 9999
    closest_len = 9999

    for reference in references:
        rlen = len(reference)
        diff = abs(rlen - clen)

        if diff < closest_diff:
            closest_diff = diff
            closest_len = rlen
        elif diff == closest_diff:
            closest_len = rlen if rlen < closest_len else closest_len

    return closest_len

def modified_precision(candidate, references, n):
    counts = count_ngrams(candidate, n)

    if len(counts) == 0:
        return 0, 0

    max_counts = {}
    for reference in references:
        ref_counts = count_ngrams(reference, n)
        for ngram in counts:
            mcount = 0 if ngram not in max_counts else max_counts[ngram]
            rcount = 0 if ngram not in ref_counts else ref_counts[ngram]
            max_counts[ngram] = max(mcount, rcount)

    clipped_counts = {}

    for ngram, count in counts.items():
        clipped_counts[ngram] = min(count, max_counts[ngram])

    return float(sum(clipped_counts.values())), float(sum(counts.values()))

def brevity_penalty(trans, refs):
    bp_c = 0.0
    bp_r = 0.0

    for candidate, references in zip(trans, refs):
        bp_c += len(candidate)
        bp_r += closest_length(candidate, references)

    bp = 1.0

    if bp_c <= bp_r:
        bp = math.exp(1.0 - bp_r / bp_c)

    return bp

# trans: a list of tokenized sentence
# refs: a list of list of tokenized reference sentences
def bleu(trans, refs, n = 4, weight = None):
    p_norm = [0 for i in range(n)]
    p_denorm = [0 for i in range(n)]

    for candidate, references in zip(trans, refs):
        for i in range(n):
            ccount, tcount = modified_precision(candidate, references, i + 1)
            p_norm[i] += ccount
            p_denorm[i] += tcount

    bleu_n = [0 for i in range(n)]

    for i in range(n):
        if p_norm[i] == 0 or p_denorm[i] == 0:
            bleu_n[i] = -9999
        else:
            bleu_n[i] = math.log(float(p_norm[i]) / float(p_denorm[i]))

    bp = brevity_penalty(trans, refs)

    bleu = bp * math.exp(sum(bleu_n) / float(n))

    return bleu

def bleu_stats(hypo, ref, k):
    yield len(hypo)
    yield len(ref)
    for n in xrange(1, k + 1):
        sngrams = [tuple(hypo[i:i + n]) for i in xrange(len(hypo) + 1 - n)]
        rngrams = [tuple(ref[i:i + n]) for i in xrange(len(ref) + 1 - n)]
        scounts = Counter(sngrams)
        rcounts = Counter(rngrams)
        yield sum((scounts & rcounts).values())
        yield max(len(hypo) + 1 - n, 0)

def sentence_bleu(hypothesis, reference, n = 4):
    stats = list(bleu_stats(hypothesis, reference, n))
    stats = numpy.atleast_2d(numpy.asarray(stats))[:, :10].sum(axis=0)

    if not all(stats):
        return 0
    c, r = stats[:2]

    vals = [numpy.log(float(x) / y) for x, y in zip(stats[2::2], stats[3::2])]
    log_bleu_prec = sum(vals) / float(n)
    return numpy.exp(min(0, 1 - float(r) / c) + log_bleu_prec)

def smoothed_sentence_bleu(hypothesis, reference, n = 4):
    stats = list(bleu_stats(hypothesis, reference, n))
    c, r = stats[:2]

    # smoothed transform
    def transform(x, y):
      return numpy.log((1 + float(x)) / (1 + y))

    vals = [transform(x, y) for x, y in zip(stats[2::2], stats[3::2])]
    log_bleu_prec = sum(vals) / float(n)
    return numpy.exp(min(0, 1 - float(r) / c) + log_bleu_prec)