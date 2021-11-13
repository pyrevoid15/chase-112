import math

def lineXline(start1, end1, start2, end2):
        d = (start2[0] - end2[0]) * (start1[1] - end1[1]) -\
            (start2[1] - end2[1]) * (start1[0] - end1[0])
            
        if d == 0:
            return False
            
        t = (start2[0] - start1[0]) * (start1[1] - end1[1]) -\
            (start2[1] - start1[1]) * (start1[0] - end1[0])
        u = (start2[0] - start1[0]) * (start2[1] - end2[1]) -\
            (start2[1] - start1[1]) * (start2[0] - end2[0])

        t /= d
        u /= d

        if 0 <= t and t <= 1 and 0 <= u and u <= 1:
            return True
        return False
