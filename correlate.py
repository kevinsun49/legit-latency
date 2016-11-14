def roll(lst):
	lst[0], lst[1:] = lst[-1], lst[0:-1]

def dot(l1, l2):
	total = 0
	for i in range(len(l1)):
		total += (l1[i] * l2[i])
	return total

def identify_peak(ds):
	return ds.index(max(ds))

def cross_correlate(d1, d2):
	length1, length2 = len(d1), len(d2)
	paddedlength = length1 + length2 - 1
	padded1, padded2 = [0] * paddedlength, [0] * paddedlength
	for i in range(length1):
		padded1[i] = d1[i]
	for i in range(length1 - 1, length1 + length2 - 1):
		padded2[i] = d2[i - (length1 - 1)]
	roll(padded2)
	correlation = []
	for _ in range(len(padded2)):
		correlation.append(dot(padded1, padded2))
		roll(padded2)
	return correlation

#returns delay of d2 compared to d1 (both args are dp/dt graphs)
def correlation(d1, d2):
	return identify_peak(cross_correlate(d1, d2))

#numpy equivalent of above code: cross-correlates two arrays of numbers rather than two lists; utilizes built-in numpy.roll and numpy.dot, etc
"""
import numpy as np
def correlation(d1, d2):
	return identify_peak(np.correlate(d1, d2, 'full'))

def identify_peak(ds):
	maxNum = ds[0]
    maxIndex = 0
    for num in range(1, len(ds)):
        if ds[num] > maxNum:
            maxNum = ds[num]
            maxIndex = num
    return maxIndex
"""